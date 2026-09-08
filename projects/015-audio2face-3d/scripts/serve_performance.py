"""Local six-expression workbench plus submitted-text-to-video service, port 8022."""
import json,subprocess,threading,time,uuid,shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import unquote,urlparse,parse_qs
import avatar_registry as avatars
from avatar_service import AvatarService
from performance_jobs import ROOT,ASSETS,JOBS,write,update,cancelled,read
LOCK=threading.Lock()
NAMES={'listen','think','comfort','playful','annoyed','affirm'}

def worker_status():
 path=JOBS/'worker.json'
 if not path.exists():return {'status':'offline'}
 data=read(path)
 if data.get('status')=='ready' and time.time()-data.get('updated_at',0)>15:data['status']='offline'
 return data

from dialogue_service import DialogueService
import minimax_dialogue
DIALOGUE=DialogueService(LOCK,worker_status)
AVATAR_SERVICE=AvatarService(LOCK,worker_status)

def generate(folder,data):
 def ensure_active():
  if cancelled(folder):raise InterruptedError('已取消')
 try:
  if data.get('source_audio_job'):
   source=JOBS/data['source_audio_job'];original=read(source/'job.json')
   shutil.copy2(source/'audio.wav',folder/'audio.wav')
   values={'tts_s':0,'voice':original.get('voice'),'source_audio_job':source.name}
   if (source/'speech.mp3').exists():
    shutil.copy2(source/'speech.mp3',folder/'speech.mp3');values['audio']=f'/jobs/{folder.name}/speech.mp3'
   update(folder,status='queued',message='复用同一段音频，准备对照画面',**values)
   started=time.monotonic()
  else:
   started=time.monotonic();update(folder,status='tts',message='使用 MiniMax 合成语音')
   style={'comfort':'comfort','annoyed':'angry','playful':'playful','affirm':'playful'}.get(data['state'],'neutral')
   voice=minimax_dialogue.speak(data['text'],data['state'],folder/'speech.mp3',check=ensure_active)
   if cancelled(folder):return
   duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(folder/'speech.mp3')]))
   if duration>12:raise ValueError('语音超过 12 秒，请缩短台词')
   target=(int((duration+.4)*25)+1)/25
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(folder/'speech.mp3'),'-af',f'apad=whole_dur={target}','-t',str(target),'-ar','16000','-ac','1',str(folder/'audio.wav')],check=True)
   update(folder,status='queued',message='语音已生成，等待嘴型处理',audio=f'/jobs/{folder.name}/speech.mp3',tts_s=round(time.monotonic()-started,3),voice=voice)
  if cancelled(folder):return
  write(folder/'request.json',data)
  while True:
   state=read(folder/'job.json')['status']
   if state in ['done','failed','cancelled']:break
   if cancelled(folder) and not (folder/'request.json').exists():break
   if worker_status().get('status')=='offline' or time.monotonic()-started>300:
    (folder/'cancel').touch()
    raise RuntimeError('模型服务离线或生成超时，请重启后重试')
   time.sleep(.3)
 except Exception as e:update(folder,status='failed',message=str(e))
 finally:
  if cancelled(folder):update(folder,status='cancelled',message='已取消')
  LOCK.release()

class Handler(SimpleHTTPRequestHandler):
 def send_json(self,code,data):
  body=json.dumps(data,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/api/avatars':return self.send_json(200,{'avatars':avatars.listing(),'busy':LOCK.locked()})
  if path.startswith('/api/avatars/'):
   try:return self.send_json(200,avatars.get(path.rsplit('/',1)[-1]))
   except ValueError as e:return self.send_json(404,{'error':str(e)})
  if path=='/api/dialogue/status':return self.send_json(200,{'provider':minimax_dialogue.status(),'worker':worker_status(),'busy':LOCK.locked()})
  if path.startswith('/api/dialogue/session/'):
   try:return self.send_json(200,DIALOGUE.session(path.rsplit('/',1)[-1]))
   except ValueError as e:return self.send_json(404,{'error':str(e)})
  if path=='/api/workbench':
   try:
    avatar=avatars.get(parse_qs(urlparse(self.path).query).get('avatar',['xiaoqing'])[0],ready=True)
    manifest=read(avatars.asset_root(avatar['id'])/'manifest.json');manifest['avatar']=avatar
   except ValueError as e:return self.send_json(400,{'error':str(e)})
   manifest['worker']=worker_status()
   manifest['busy']=LOCK.locked();manifest['jobs']=[j for p in sorted(JOBS.glob('*/job.json'),key=lambda p:p.stat().st_mtime,reverse=True) if (j:=read(p)).get('avatar_id','xiaoqing')==avatar['id']][:12]
   return self.send_json(200,manifest)
  if path.startswith('/api/jobs/'):
   key=path.rsplit('/',1)[-1]
   if len(key)!=32 or any(c not in '0123456789abcdef' for c in key):return self.send_json(404,{'error':'任务不存在'})
   p=JOBS/key/'job.json'
   if not p.exists():return self.send_json(404,{'error':'任务不存在'})
   data=read(p)
   if cancelled(p.parent):data.update(status='cancelled',message='已取消')
   return self.send_json(200,data)
  return super().do_GET()
 def do_POST(self):
  if self.headers.get('Origin') not in (None,'http://127.0.0.1:8022','http://localhost:8022'):return self.send_json(403,{'error':'仅支持本机页面'})
  path=urlparse(self.path).path
  if path.startswith('/api/avatars/') and path.endswith('/retry'):
   try:return self.send_json(202,AVATAR_SERVICE.retry(path.split('/')[-2],parse_qs(urlparse(self.path).query).get('regenerate')==['1']))
   except ValueError as e:return self.send_json(400,{'error':str(e)})
   except BlockingIOError as e:return self.send_json(409,{'error':str(e)})
  if path=='/api/avatars':
   try:
    length=int(self.headers.get('Content-Length',0))
    if not 0<length<=12*1024*1024:raise ValueError('照片需小于 12 MB')
    name=parse_qs(urlparse(self.path).query).get('name',['我的人物'])[0]
    return self.send_json(202,AVATAR_SERVICE.upload(self.rfile.read(length),name,parse_qs(urlparse(self.path).query).get('motion_backend',['local-facial'])[0]))
   except (ValueError,TypeError) as e:return self.send_json(400,{'error':str(e)})
   except BlockingIOError as e:return self.send_json(409,{'error':str(e)})
  if path=='/api/dialogue/session':
   try:
    length=int(self.headers.get('Content-Length',0))
    if not 0<=length<=8192:raise ValueError('请求过长')
    data=json.loads(self.rfile.read(length)) if length else {}
    if not isinstance(data,dict):raise ValueError('请求格式不正确')
    return self.send_json(201,DIALOGUE.create(data.get('avatar_id',avatars.DEFAULT)))
   except (ValueError,TypeError) as e:return self.send_json(400,{'error':str(e)})
  if path=='/api/dialogue/turn':
   try:
    length=int(self.headers.get('Content-Length',0))
    if not 0<length<=8192:raise ValueError('输入过长')
    data=json.loads(self.rfile.read(length))
    if not isinstance(data,dict):raise ValueError('请求格式不正确')
    return self.send_json(202,DIALOGUE.submit(data))
   except (ValueError,TypeError) as e:return self.send_json(400,{'error':str(e)})
   except BlockingIOError as e:return self.send_json(409,{'error':str(e)})
   except minimax_dialogue.ProviderError as e:return self.send_json(503,{'error':str(e)})
  if path.startswith('/api/cancel/'):
   key=path.rsplit('/',1)[-1]
   if len(key)!=32 or any(c not in '0123456789abcdef' for c in key) or not (JOBS/key/'job.json').exists():return self.send_json(404,{'error':'任务不存在'})
   folder=JOBS/key;state=read(folder/'job.json')['status']
   if state in ['done','failed','cancelled']:return self.send_json(200,{'status':state})
   (folder/'cancel').touch();return self.send_json(200,{'status':'cancelled'})
  if path!='/api/generate':return self.send_json(404,{'error':'接口不存在'})
  try:
   length=int(self.headers.get('Content-Length',0))
   if not 0<length<=4096:raise ValueError()
   data=json.loads(self.rfile.read(length));text=data.get('text','').strip();state=data.get('state');avatar=avatars.get(data.get('avatar_id','xiaoqing'),ready=True)
   if not 1<=len(text)<=80 or state not in NAMES:raise ValueError()
   audio_key=data.get('source_audio_job')
   if audio_key is not None:
    if not isinstance(audio_key,str) or len(audio_key)!=32 or any(c not in '0123456789abcdef' for c in audio_key):raise ValueError()
    if not (JOBS/audio_key/'audio.wav').is_file() or read(JOBS/audio_key/'job.json')['status']!='done':raise ValueError()
  except (ValueError,TypeError,AttributeError):return self.send_json(400,{'error':'请选择动作，输入 1–80 字台词'})
  if worker_status().get('status')!='ready':return self.send_json(503,{'error':'模型服务未就绪，请启动或等待预热'})
  if not LOCK.acquire(False):return self.send_json(409,{'error':'已有生成任务，请等待或取消'})
  key=uuid.uuid4().hex;folder=JOBS/key;folder.mkdir(parents=True);data={'id':key,'text':text,'state':state,'avatar_id':avatar['id'],'submitted_at':time.time(),'source_audio_job':audio_key}
  write(folder/'job.json',{**data,'status':'queued','message':'准备合成语音'})
  threading.Thread(target=generate,args=(folder,data),daemon=True).start();return self.send_json(202,data)
 def translate_path(self,path):
  path=unquote(urlparse(path).path)
  if path in ['/characters','/characters/']:return str(ROOT/'demo/characters.html')
  if path in ['/chat','/chat/']:return str(ROOT/'demo/dialogue.html')
  if path in ['/chat-classic','/chat-classic/']:return str(ROOT/'demo/dialogue-classic.html')
  if path=='/':return str(ROOT/'demo/performance.html')
  for prefix,root in [('/assets/',ASSETS),('/jobs/',JOBS),('/avatars-media/',avatars.AVATARS)]:
   if path.startswith(prefix):
    target=(root/path[len(prefix):]).resolve()
    if not target.is_relative_to(root.resolve()) or target.suffix not in ['.mp4','.jpg','.png','.mp3','.wav']:return str(root/'invalid')
    return str(target)
  return super().translate_path(path)

if __name__=='__main__':
 JOBS.mkdir(exist_ok=True);AVATAR_SERVICE.recover();print('Performance workbench http://127.0.0.1:8022/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8022),partial(Handler,directory=str(ROOT/'demo'))).serve_forever()
