"""At most two natural speech segments, bounded TTS prefetch, serial GPU ownership."""
import json,re,subprocess,time,uuid,threading,wave,math
from concurrent.futures import ThreadPoolExecutor
from performance_jobs import JOBS,write,update,cancelled,read
from dialogue_service import DialogueCancelled
import minimax_dialogue as provider

def split_reply(text):
 # Split only at punctuation; never truncate a word or create tiny fragments.
 points=[m.end() for m in re.finditer(r'[，。！？；～!?;]',text) if 6<=m.end()<=20 and len(text)-m.end()>=6]
 if not points:return [text]
 cut=min(points,key=lambda i:abs(i-12))
 return [text[:cut],text[cut:]]

def run(service,folder,job,history,event):
 children=[];pool=None;completed=[];stopped=threading.Event()
 def check():
  if stopped.is_set() or cancelled(folder):raise DialogueCancelled()
 def prepare(child,text,intent):
  check();start=time.monotonic()
  voice=provider.speak(text,intent,child/'speech.mp3',check=check);check()
  duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(child/'speech.mp3')],timeout=15))
  if duration>12:raise provider.ProviderError('这句话语音过长，请用短句继续')
  target=(int((duration+.4)*25)+1)/25
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(child/'speech.mp3'),'-af',f'apad=whole_dur={target}','-t',str(target),'-ar','16000','-ac','1',str(child/'audio.wav')],check=True,timeout=30)
  with wave.open(str(child/'audio.wav')) as wav:frame_count=math.floor(wav.getnframes()/wav.getframerate()*25)
  check();return {'voice':voice,'tts_s':round(time.monotonic()-start,3),'audio':f'/jobs/{child.name}/speech.mp3','frame_count':frame_count}
 queued=set()
 def enqueue(index,voice,frame_offset):
  check();child=children[index];current=update(child,**voice,status='queued',frame_offset=frame_offset)
  write(child/'request.json',{k:current[k] for k in ['id','text','state','submitted_at','frame_offset','avatar_id']});queued.add(index)
 try:
  started=time.monotonic();answer=provider.reply(history,job['user_text'],event,check=check);check()
  parts=split_reply(answer['reply']);intent=answer['intent'];chat_s=round(time.monotonic()-started,3)
  for i,text in enumerate(parts):
   child=JOBS/uuid.uuid4().hex;children.append(child)
   write(child/'job.json',{'id':child.name,'parent':folder.name,'avatar_id':job.get('avatar_id','xiaoqing'),'kind':'dialogue_segment','index':i,'text':text,'state':intent,'submitted_at':job['submitted_at'],'status':'tts'})
  update(folder,text=answer['reply'],state=intent,chat_s=chat_s,chat_model=answer['model'],chat_usage=answer['usage'],status='tts',message='正在准备第一句',segments=[],segment_count=len(parts),children=[c.name for c in children])
  pool=ThreadPoolExecutor(max_workers=1)
  pending=pool.submit(prepare,children[0],parts[0],intent);frame_offset=0
  for i,child in enumerate(children):
   while not pending.done():check();time.sleep(.1)
   voice=pending.result();check()
   # The next HTTP speech request overlaps this segment's GPU work.
   if i+1<len(children):pending=pool.submit(prepare,children[i+1],parts[i+1],intent)
   if i not in queued:enqueue(i,voice,frame_offset)
   update(folder,status='rendering',message=f'正在准备第 {i+1}/{len(parts)} 句')
   deadline=time.monotonic()+180
   while True:
    check();state=read(child/'job.json')
    if i+1<len(children) and i+1 not in queued and pending.done():enqueue(i+1,pending.result(),frame_offset+voice['frame_count'])
    if state['status'] in ('done','failed','cancelled') and not (child/'request.json').exists():break
    if service.worker_status().get('status')!='ready' or time.monotonic()>deadline:raise provider.ProviderError('人物生成超时或离线，已完成的片段仍可播放')
    time.sleep(.1)
   if state['status']!='done':raise provider.ProviderError('本句画面生成失败，已完成的片段仍可播放' if completed else '本句画面生成失败，请重试')
   check();state['ready_s']=round(time.time()-job['submitted_at'],3);completed.append(state)
   frame_offset+=round(state['metrics']['media_duration_s']*25)
   update(folder,segments=completed,progress=len(completed)/len(parts),first_segment_s=completed[0]['ready_s'],message='第一句已准备好，后续回应正在生成' if len(completed)<len(parts) else '全部回应已准备好')
  check();service.append(job['session'],'assistant',answer['reply'],folder.name,intent=intent)
  update(folder,status='done',message='分段回应已准备好',metrics={'total_s':round(time.time()-job['submitted_at'],3),'first_segment_s':completed[0]['ready_s'],'media_duration_s':sum(s['metrics']['media_duration_s'] for s in completed)})
 except DialogueCancelled:update(folder,status='cancelled',message='已打断，可以继续说')
 except provider.ProviderError as e:update(folder,status='failed',message=str(e))
 except Exception:
  import traceback
  (folder/'error.log').write_text(traceback.format_exc(),encoding='utf-8')
  update(folder,status='failed',message='本轮生成失败，已完成的片段仍可重播')
 finally:
  stopped.set()
  # Never hand GPU ownership to a new turn before the old request is consumed.
  for child in children:
   if (child/'request.json').exists() or cancelled(folder):(child/'cancel').touch()
  if pool:pool.shutdown(wait=True,cancel_futures=True)
  while any((c/'request.json').exists() for c in children):
   if service.worker_status().get('status')!='ready':
    for child in children:(child/'request.json').unlink(missing_ok=True)
    break
   time.sleep(.1)
  service.admission.release()
