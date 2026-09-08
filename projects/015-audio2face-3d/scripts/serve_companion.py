"""Local companion scene player and custom speech/video generation, port 8018."""
import json
import threading
import time
import uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote
from companion_media import ROOT, ASSETS, STATES, settings, synthesize, render

JOBS = {}
LOCK = threading.Lock()
OUTPUT = ROOT/'.cache/companion-jobs'

def generate(job):
 folder = OUTPUT/job['id']; folder.mkdir(parents=True,exist_ok=True)
 start = time.monotonic()
 def progress(message): job.update(message=message)
 try:
  job.update(status='running',message='正在合成台湾口音语音…' if job['provider']=='edge' else '正在调用 MiniMax 语音…')
  audio = folder/'speech.mp3'
  voice = synthesize(job['text'],job['state'],audio,job['provider'])
  job.update(audio=f'/jobs/{job["id"]}/speech.mp3',voice=voice)
  source = ASSETS/(('neutral' if job['state']=='comfort' else job['state'])+'.png')
  timing = render(source,audio,folder,job['state'],progress)
  job.update(status='done',message='新台词视频已生成',video=f'/jobs/{job["id"]}/result.mp4',
    poster=f'/jobs/{job["id"]}/portrait.png',seconds=round(time.monotonic()-start,1),**timing)
 except Exception as error:
  job.update(status='failed',message=str(error) if isinstance(error,(ValueError,RuntimeError)) else '生成服务暂时失败，请查看本机配置或网络连接')
 finally:
  (folder/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8'); LOCK.release()

class Handler(SimpleHTTPRequestHandler):
 def json_response(self,code,data):
  raw=json.dumps(data,ensure_ascii=False).encode(); self.send_response(code)
  self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw)))
  self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
 def translate_path(self,path):
  clean=unquote(urlparse(path).path)
  if clean=='/':return str(ROOT/'demo/companion.html')
  for prefix,root in [('/media/',ASSETS),('/jobs/',OUTPUT)]:
   if clean.startswith(prefix):
    dest=(root/clean[len(prefix):]).resolve()
    if not dest.is_relative_to(root.resolve()) or dest.suffix not in ('.png','.jpg','.mp3','.mp4','.wav'):
     return str(root/'invalid')
    return str(dest)
  return super().translate_path(path)
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/api/status':
   manifest=ASSETS/'manifest.json'
   data=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {'clips':[]}
   config=settings()
   data.update(busy=LOCK.locked(),minimax_ready=bool(config.get('MINIMAX_API_KEY') and config.get('MINIMAX_VOICE_ID')),chat_ready=False)
   return self.json_response(200,data)
  if path.startswith('/api/jobs/'):
   key=path.rsplit('/',1)[-1]
   if key not in JOBS:return self.json_response(404,{'error':'任务不存在，请重新生成'})
   return self.json_response(200,JOBS[key].copy())
  return super().do_GET()
 def do_POST(self):
  if urlparse(self.path).path!='/api/generate':return self.json_response(404,{'error':'接口不存在'})
  origin=self.headers.get('Origin')
  if origin and origin not in ('http://127.0.0.1:8018','http://localhost:8018'):
   return self.json_response(403,{'error':'仅支持本机页面'})
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<4096:raise ValueError('请求过大或为空')
   data=json.loads(self.rfile.read(length)); text=data.get('text','')
   if not isinstance(text,str) or not 1<=len(text.strip())<=70:raise ValueError('请输入 1–70 个字的台词')
   state=data.get('state','neutral'); provider=data.get('provider','edge')
   if state not in STATES or provider not in ('edge','minimax'):raise ValueError('请选择有效的情绪和语音服务')
   if provider=='minimax':
    config=settings()
    if not config.get('MINIMAX_API_KEY') or not config.get('MINIMAX_VOICE_ID'):raise ValueError('MiniMax 尚未配置，请选择台湾女声或在本机配置')
  except (ValueError,TypeError,AttributeError):return self.json_response(400,{'error':'台词应为 1–70 字，且情绪、语音服务必须有效；MiniMax 需要本机配置'})
  if not LOCK.acquire(False):return self.json_response(409,{'error':'已有视频生成中，请稍后再试'})
  job={'id':uuid.uuid4().hex,'text':text.strip(),'state':state,'provider':provider,'status':'queued','message':'正在准备'}
  JOBS[job['id']]=job
  threading.Thread(target=generate,args=(job,),daemon=True).start()
  return self.json_response(202,job)

if __name__=='__main__':
 OUTPUT.mkdir(parents=True,exist_ok=True)
 print('Companion prototype: http://127.0.0.1:8018/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8018),partial(Handler,directory=str(ROOT/'demo'))).serve_forever()
