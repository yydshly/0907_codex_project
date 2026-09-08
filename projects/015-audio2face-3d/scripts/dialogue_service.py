"""Single-character contextual dialogue, shared GPU admission and real avatar jobs."""
import json,subprocess,threading,time,uuid
from performance_jobs import ROOT,JOBS,write,update,cancelled,read
import minimax_dialogue as provider
import avatar_registry as avatars

class DialogueCancelled(Exception):pass
def valid_id(value):return isinstance(value,str) and len(value)==32 and all(c in '0123456789abcdef' for c in value)

class DialogueService:
 def __init__(self,admission,worker_status):
  self.admission=admission;self.worker_status=worker_status;self.storage=ROOT/'.cache/dialogue-sessions';self.mutex=threading.RLock()
 def session(self,key):
  if not valid_id(key):raise ValueError('会话不存在')
  with self.mutex:
   path=self.storage/(key+'.json')
   if not path.exists():raise ValueError('会话不存在，请新建对话')
   return read(path)
 def create(self,avatar_id=avatars.DEFAULT):
  avatar=avatars.get(avatar_id,ready=True)
  data={'id':uuid.uuid4().hex,'avatar_id':avatar['id'],'messages':[],'created_at':time.time()};write(self.storage/(data['id']+'.json'),data);return data
 def append(self,key,role,content,job,intent=None):
  with self.mutex:
   session=self.session(key);message={'role':role,'content':content,'job':job}
   if role=='assistant' and intent in provider.INTENTS:message['intent']=intent
   session['messages'].append(message);write(self.storage/(key+'.json'),session)
 def submit(self,data):
  key=data.get('session');session=self.session(key);text=data.get('text');event=data.get('event');mode=data.get('mode','classic')
  avatar=avatars.get(session.get('avatar_id',avatars.DEFAULT),ready=True)
  if data.get('avatar_id',avatar['id'])!=avatar['id']:raise ValueError('会话人物不一致，请切换后新建对话')
  if mode not in ('classic','segmented'):raise ValueError('未知对话模式')
  if not isinstance(text,str) or not 1<=len(text.strip())<=500 or event not in (None,'task_done'):raise ValueError('请输入 1–500 字，或选择任务完成事件')
  if not provider.status()['configured']:raise provider.ProviderError('请先在本机 .env.companion 配置 MiniMax API Key，保存后点击重新检查')
  if self.worker_status().get('status')!='ready':raise provider.ProviderError('人物模型正在准备，请稍后再试')
  if not self.admission.acquire(False):raise BlockingIOError('上一条还在处理，请先打断并等待后台释放')
  try:
   folder=JOBS/uuid.uuid4().hex;folder.mkdir(parents=True)
   job={'id':folder.name,'avatar_id':avatar['id'],'avatar_version':avatar['version'],'session':key,'kind':'dialogue','mode':mode,'user_text':text.strip(),'text':'','state':'think','submitted_at':time.time(),'status':'thinking','message':'正在想怎么回应你','provider':'MiniMax'}
   write(folder/'job.json',job);self.append(key,'user',text.strip(),folder.name)
   threading.Thread(target=self.run,args=(folder,job,session['messages'],event),daemon=True).start();return job
  except Exception:self.admission.release();raise
 def run(self,folder,job,history,event):
  if job.get('mode')=='segmented':
   from dialogue_segments import run
   return run(self,folder,job,history,event)
  def check():
   if cancelled(folder):raise DialogueCancelled()
  try:
   start=time.monotonic();result=provider.reply(history,job['user_text'],event,check=check);check()
   reply=result['reply'];intent=result['intent'];chat_s=round(time.monotonic()-start,3)
   self.append(job['session'],'assistant',reply,folder.name,intent=intent)
   update(folder,text=reply,state=intent,chat_model=result['model'],chat_s=chat_s,chat_usage=result['usage'],status='tts',message='回复已生成，正在准备声音')
   start=time.monotonic();voice=provider.speak(reply,intent,folder/'speech.mp3',check=check);check()
   update(folder,voice=voice,audio=f'/jobs/{folder.name}/speech.mp3')
   duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(folder/'speech.mp3')],timeout=15))
   if duration>12:raise provider.ProviderError('本次语音超过 12 秒，已保留文字和语音，请用短句继续对话')
   target=(int((duration+.4)*25)+1)/25
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(folder/'speech.mp3'),'-af',f'apad=whole_dur={target}','-t',str(target),'-ar','16000','-ac','1',str(folder/'audio.wav')],check=True,timeout=30);check()
   current=update(folder,status='queued',message='声音已准备好，正在生成有声表演',voice=voice,tts_s=round(time.monotonic()-start,3),audio=f'/jobs/{folder.name}/speech.mp3')
   write(folder/'request.json',{k:current[k] for k in ['id','text','state','submitted_at','avatar_id']})
   deadline=time.monotonic()+180
   while True:
    state=read(folder/'job.json')['status']
    if state in ('done','failed','cancelled') and not (folder/'request.json').exists():break
    if cancelled(folder) and not (folder/'request.json').exists():raise DialogueCancelled()
    if self.worker_status().get('status')!='ready' or time.monotonic()>deadline:
     (folder/'cancel').touch();raise provider.ProviderError('人物服务离线或超时，文字回复已保留')
    time.sleep(.2)
  except DialogueCancelled:update(folder,status='cancelled',message='已打断，等待你继续说')
  except provider.ProviderError as e:update(folder,status='failed',message=str(e))
  except Exception:update(folder,status='failed',message='本次处理失败，文字回复已保留，请重试')
  finally:
   if cancelled(folder) and not (folder/'request.json').exists():update(folder,status='cancelled',message='已打断，等待你继续说')
   self.admission.release()
