"""Generic photo -> six actual MiniMax half-body performances -> local caches."""
import gc,hashlib,subprocess,threading,time
from concurrent.futures import ThreadPoolExecutor
import cv2,numpy as np,torch
from performance_jobs import ROOT,write
from build_performance_assets import STATES
from minimax_motion import generate,MODEL

@torch.inference_mode()
def main(source,out,progress):
 from facexlib.detection import init_detection_model
 out.mkdir(parents=True,exist_ok=True);image=cv2.imread(str(source));progress('检查人物照片',.01)
 detector=init_detection_model('retinaface_resnet50',device='cuda',model_rootpath=str(ROOT/'vendor/photo-models'))
 detections=detector.detect_faces(image,.9)
 if len(detections)!=1:raise ValueError('请使用仅有一张清晰人脸的照片')
 d=detections[0]
 if d[2]-d[0]<90 or d[3]-d[1]<100:raise ValueError('人脸过小，请使用近景或半身照')
 del detector;gc.collect();torch.cuda.empty_cache()
 mutex=threading.Lock();completed=[];stopped=threading.Event()
 def check():
  if stopped.is_set():raise InterruptedError('Preparation stopped')
  with mutex:progress('MiniMax 正在生成半身动作（'+str(len(completed))+'/6）',.03+.59*len(completed)/6)
 def one(name):
  check()
  folder=out/name;raw=generate(source,folder,name,check)
  check();subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-an','-vf','scale=512:768:force_original_aspect_ratio=decrease,pad=512:768:(ow-iw)/2:(oh-ih)/2,fps=25','-t','6','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(folder/'motion.mp4')],check=True,timeout=60)
  cap=cv2.VideoCapture(str(folder/'motion.mp4'));middle=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))//2;frames=folder/'frames';frames.mkdir(exist_ok=True);count=0;first=None;mid=None;last=None
  while True:
   ok,f=cap.read()
   if not ok:break
   if count==0:first=f
   if count==middle:mid=f
   if count in (0,middle):cv2.imwrite(str(frames/f'{count:05d}.png'),f)
   last=f;count+=1
  cap.release()
  if count<145:raise ValueError('生成视频时长不足')
  cv2.imwrite(str(frames/f'{count-1:05d}.png'),last);cv2.imwrite(str(folder/'poster.jpg'),mid)
  movement=float(np.abs(mid[400:].astype(float)-first[400:].astype(float)).mean())
  if movement<.1:raise ValueError('半身视频缺少有效身体变化')
  data={'id':name,'name':STATES[name]['name'],'description':'自然半身表演 · '+STATES[name]['name'],'fps':25,'frames':count,'duration':count/25,'backend':MODEL,'scope':'generated head, shoulder and upper-body motion','loop_mode':'forward; endpoint transition not guaranteed','review':'subjective review required','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'body_change':movement,'video':'','poster':''}
  write(folder/'asset.json',data);write(folder/'scene.json',{'id':name,'motion_source':str(folder/'motion.mp4')})
  with mutex:completed.append(data)
  return data
 with ThreadPoolExecutor(max_workers=2) as pool:
  try:
   futures=[pool.submit(one,name) for name in STATES]
   for future in futures:future.result()
  except BaseException:
   stopped.set()
   for future in futures:future.cancel()
   raise
 completed.sort(key=lambda a:list(STATES).index(a['id']))
 write(out/'manifest.json',{'character':'uploaded','backend':MODEL,'assets':completed})
 progress('六段半身动作已完成，准备口型缓存',.65)
