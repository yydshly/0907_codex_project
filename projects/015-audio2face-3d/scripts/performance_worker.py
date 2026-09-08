"""Resident MuseTalk worker: cached motion inputs, CPU Whisper, GPU mini-batches.

Produces genuine new audio-conditioned videos; not an LLM or realtime stream.
"""
import gc,json,time,traceback,os,threading,subprocess,sys
from avatar_registry import asset_for,AVATARS,get as get_avatar,change as change_avatar
import cv2,numpy as np,torch
from concurrent.futures import ThreadPoolExecutor
from performance_jobs import ROOT,ASSETS,JOBS,write,update,cancelled,read
from musetalk_complete import WEIGHTS,read_video
from performance_postprocess import render
from avatar_timing import read_pcm,envelope
torch.set_num_threads(4)
cv2.setNumThreads(1)

class Cancelled(Exception):pass
def check(folder):
 if cancelled(folder):raise Cancelled()

def stop_preparation(process):
 # A Windows venv executable launches a second Python process. Stop its owned
 # tree before restoring resident GPU models or publishing cancellation.
 if process.poll() is not None:return
 if os.name=='nt':
  subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
 else:process.terminate()
 process.wait(timeout=20)

@torch.inference_mode()
def main():
 from accelerate import init_empty_weights
 from diffusers import UNet2DConditionModel
 from musetalk.models.vae import VAE
 from musetalk.models.unet import PositionalEncoding
 from musetalk.utils.audio_processor import AudioProcessor
 from transformers import WhisperModel
 JOBS.mkdir(exist_ok=True);start=time.monotonic();write(JOBS/'worker.json',{'status':'loading'})
 with init_empty_weights():unet=UNet2DConditionModel.from_config(json.loads((WEIGHTS/'unet/config.json').read_text()))
 state=torch.load(str(WEIGHTS/'unet/unet.pth'),map_location='cpu',mmap=True,weights_only=True)
 unet.load_state_dict(state,assign=True);del state
 unet.to(device='cuda',dtype=torch.float16).eval()
 vae=VAE(str(WEIGHTS/'vae'),use_float16=True);pe=PositionalEncoding().cuda().half()
 processor=AudioProcessor(str(WEIGHTS/'whisper'))
 whisper=WhisperModel.from_pretrained(str(WEIGHTS/'whisper')).cpu().eval()
 startup=round(time.monotonic()-start,3)
 def heartbeat():
  while True:
   write(JOBS/'worker.json',{'status':'ready','startup_s':startup,'pid':os.getpid(),'updated_at':time.time(),'pipeline_version':'performance-v3-overlap'})
   time.sleep(3)
 threading.Thread(target=heartbeat,daemon=True).start();print('Worker ready',flush=True)
 pool=ThreadPoolExecutor(max_workers=1)
 pending={};motion_phases={}
 def finish(request,job,started,faces,source,boxes,masks,weights,timeline,measures):
  folder=request.parent
  try:
   check(folder);post_start=time.monotonic();post_started_at=time.time()
   post=render(faces,source,boxes,masks,weights,folder,lambda:check(folder),job.get('keep_frames',False));check(folder)
   render_s=time.monotonic()-started;current=read(folder/'job.json');count=len(weights)
   queued_at=measures.pop('_post_queued_at')
   metrics={**measures,**post,'pipeline_version':'performance-v3-overlap','render_s':round(render_s,3),'post_started_at':post_started_at,'post_finished_at':time.time(),
    'cpu_queue_wait_s':round(post_start-queued_at,3),
    'total_s':round(time.time()-job['submitted_at'],3),'media_duration_s':count/25,
    'resident_worker_startup_s':startup,'processing_realtime_factor':round(render_s/(count/25),3),'tts_s':current.get('tts_s')}
   write(folder/'timeline.json',timeline);update(folder,status='done',message='新台词视频已生成',progress=1,video=f'/jobs/{folder.name}/result.mp4',metrics=metrics)
   print(folder.name+' '+json.dumps(metrics),flush=True)
  except Cancelled:update(folder,status='cancelled',message='已取消生成')
  except Exception:
   (folder/'error.log').write_text(traceback.format_exc(),encoding='utf-8');update(folder,status='failed',message='画面合成失败，详情见任务日志');traceback.print_exc()
  finally:request.unlink(missing_ok=True)
 while True:
  pending={key:future for key,future in pending.items() if not future.done()}
  if len(pending)>=2:time.sleep(.05);continue
  requests=sorted((p for p in JOBS.glob('*/request.json') if p not in pending),key=lambda p:p.stat().st_mtime)
  if not requests:time.sleep(.2);continue
  for request in requests:
   if len(pending)>=2:break
   folder=request.parent
   try:
    check(folder);job=read(request)
    if job.get('kind')=='avatar_prepare':
     for future in pending.values():future.result()
     pending.clear();key=job['avatar_id'];get_avatar(key)
     change_avatar(key,status='preparing');update(folder,status='preparing',message='正在准备人物模型')
     try:
      unet.cpu();vae.vae.cpu();pe.cpu();gc.collect();torch.cuda.empty_cache()
      with (folder/'preparation.log').open('ab') as log:
       for phase in ('motion','cache','validate'):
        check(folder)
        process=subprocess.Popen([sys.executable,str(ROOT/'scripts/prepare_user_avatar.py'),key,folder.name,phase],cwd=ROOT,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
         deadline=time.monotonic()+1200
         while process.poll() is None:
          check(folder)
          if time.monotonic()>deadline:
           change_avatar(key,message='人物准备超时，请换一张照片重试');raise TimeoutError('Avatar preparation exceeded 20 minutes per stage')
          time.sleep(.2)
         if process.returncode:raise ValueError(get_avatar(key).get('message','人物准备失败，详见本地日志'))
        finally:
         stop_preparation(process)
     finally:
      unet.cuda();vae.vae.cuda();pe.cuda();torch.cuda.empty_cache()
     check(folder);change_avatar(key,status='ready',message='六种动作和嘴部缓存已就绪',ready_at=time.time())
     update(folder,status='done',message='人物已就绪，可以预览动作并开始对话',progress=1)
     continue
    asset=asset_for(job);started=time.monotonic()
    update(folder,status='rendering',message='分析新语音',progress=0)
    features,length=processor.get_audio_feature(str(folder/'audio.wav'))
    chunks=processor.get_whisper_chunk(features,'cpu',torch.float32,whisper,length,fps=25).cuda().half()
    audio_s=time.monotonic()-started
    check(folder);source=read_video(asset/'motion.mp4');latents=torch.load(str(asset/'latents.pt'),weights_only=True).cuda()
    boxes=np.load(asset/'float_boxes.npy');masks=np.load(asset/'masks.npy',mmap_mode='r')
    phase=0 if get_avatar(job.get('avatar_id','xiaoqing')).get('motion_backend')=='minimax-body' else int(job.get('frame_offset',0))%len(source)
    if phase:
     source=source[phase:]+source[:phase];latents=torch.roll(latents,-phase,0)
     boxes=np.roll(boxes,-phase,0);masks=np.roll(masks,-phase,0)
    pcm,rate=read_pcm(folder/'audio.wav');count=len(chunks);weights,timeline=envelope(pcm,rate,25,count)
    if get_avatar(job.get('avatar_id','xiaoqing')).get('motion_backend')=='minimax-body':
     from speech_motion import schedule,sample_video
     current=read(folder/'job.json');parent=current.get('parent');phase_start=motion_phases.get(parent,0.) if parent else 0.
     positions,phase_end,motion_stats=schedule(pcm,rate,25,count,phase_start)
     source,boxes,masks,lo,hi,fraction=sample_video(source,boxes,masks,positions)
     alpha=torch.tensor(fraction,device='cuda',dtype=latents.dtype).reshape(-1,1,1,1)
     latents=latents[lo]*(1-alpha)+latents[hi]*alpha
     write(folder/'motion.json',{'positions':positions.tolist(),'base_frame_offset':phase,'phase_end':phase_end,**motion_stats})
     update(folder,motion_phase_end=phase_end)
     if parent:motion_phases[parent]=phase_end
     if len(motion_phases)>64:motion_phases.pop(next(iter(motion_phases)))

    faces=[None]*count;active=[i for i,w in enumerate(weights) if w>0]
    inference_start=time.monotonic();gpu_started_at=time.time();torch.cuda.reset_peak_memory_stats()
    for offset in range(0,len(active),4):
     check(folder);batch=active[offset:offset+4];indices=[i%len(source) for i in batch]
     prediction=unet(latents[indices],torch.tensor([0],device='cuda'),encoder_hidden_states=pe(chunks[batch])).sample
     result=vae.decode_latents(prediction)
     for i,f in zip(batch,result):faces[i]=f
     update(folder,status='rendering',message='根据新音频生成嘴型',progress=round((offset+len(batch))/max(1,len(active))*.8,3))
    inference_s=time.monotonic()-inference_start
    if job.get('audit'):
     np.save(folder/'inference-faces.npy',np.array([f if f is not None else np.zeros((256,256,3),np.uint8) for f in faces]))
    update(folder,message='稳定嘴部并合成有声视频',progress=.85)
    measures={'audio_feature_s':round(audio_s,3),'lip_inference_s':round(inference_s,3),'gpu_started_at':gpu_started_at,'gpu_finished_at':time.time(),'gpu_peak_allocated_mb':round(torch.cuda.max_memory_allocated()/1024**2,1),'_post_queued_at':time.monotonic()}
    pending[request]=pool.submit(finish,request,job,started,faces,source,boxes,masks,weights,timeline,measures)
    del chunks,latents,faces,source;gc.collect()
   except Cancelled:
    update(folder,status='cancelled',message='已取消生成')
    if read(request).get('kind')=='avatar_prepare':change_avatar(read(request)['avatar_id'],status='cancelled',message='准备已取消，可重新上传')
   except Exception:
    (folder/'error.log').write_text(traceback.format_exc(),encoding='utf-8');update(folder,status='failed',message='生成失败，详情见任务日志');traceback.print_exc()
    if read(request).get('kind')=='avatar_prepare':
     key=read(request)['avatar_id'];change_avatar(key,status='failed');update(folder,message=get_avatar(key).get('message','人物准备失败，请换照片重试'))
   finally:
    if request not in pending:request.unlink(missing_ok=True)

if __name__=='__main__':main()
