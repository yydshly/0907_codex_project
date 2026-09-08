"""Local-only photo + audio -> SadTalker video jobs. Independent of Audio2Face."""
import cgi
import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,unquote

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'.cache/photo-jobs'
RUNTIME=ROOT/'.cache/sadtalker-venv/Scripts/python.exe'
REPO=ROOT/'vendor/SadTalker'
MODELS=ROOT/'vendor/photo-models'
SAMPLE=ROOT/'.cache/photo-sample'
JOBS={}
LOCK=threading.Lock()

def save(job):
 (OUTPUT/job['id']/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')

def generate(job):
 folder=OUTPUT/job['id'];start=time.monotonic()
 try:
  job.update(status='running',message='正在识别人脸并生成口型，请保持页面打开。');save(job)
  command=[str(RUNTIME),str(REPO/'inference.py'),'--source_image',str(folder/'portrait.png'),
           '--driven_audio',str(folder/'audio.wav'),'--checkpoint_dir',str(MODELS),
           '--result_dir',str(folder/'render'),'--size','256','--batch_size','1',
           '--preprocess','crop','--still','--enhancer','gfpgan']
  with (folder/'render.log').open('w',encoding='utf-8') as log:
   result=subprocess.run(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,timeout=1800,
                         env={**os.environ,'PYTHONIOENCODING':'utf-8','OMP_NUM_THREADS':'4'})
  if result.returncode:raise RuntimeError('模型运行失败，请查看本机任务日志。')
  videos=sorted((folder/'render').glob('*.mp4'),key=lambda p:p.stat().st_mtime)
  if not videos:raise RuntimeError('模型未输出视频，请查看本机任务日志。')
  shutil.copyfile(videos[-1],folder/'result.mp4')
  job.update(status='done',message='视频已生成，可以播放或下载。',video=f'/results/{job["id"]}/result.mp4',
             seconds=round(time.monotonic()-start,1),model='SadTalker v0.0.2 + GFPGAN',face_resolution=256)
 except subprocess.TimeoutExpired:job.update(status='failed',message='生成超过 30 分钟，任务已停止。')
 except Exception as e:job.update(status='failed',message=str(e))
 finally:save(job);LOCK.release()

class Handler(SimpleHTTPRequestHandler):
 def json_response(self,code,data):
  raw=json.dumps(data,ensure_ascii=False).encode('utf-8');self.send_response(code)
  self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)))
  self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
 def translate_path(self,path):
  clean=unquote(urlparse(path).path)
  if clean=='/':return str(ROOT/'demo/photo.html')
  for prefix,root in [('/results/',OUTPUT),('/sample/',SAMPLE)]:
   if clean.startswith(prefix):
    dest=(root/clean[len(prefix):]).resolve()
    if not dest.is_relative_to(root.resolve()):return str(root/'invalid')
    return str(dest)
  return super().translate_path(path)
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/api/status':
   examples=[]
   for file in sorted(OUTPUT.glob('*/job.json'),key=lambda p:p.stat().st_mtime):
    item=json.loads(file.read_text(encoding='utf-8'))
    if item.get('status')=='done' and item.get('sample'):examples.append(item)
   return self.json_response(200,{'ready':(ROOT/'.cache/photo-runtime-ready.json').exists() and (MODELS/'manifest.json').exists(),
      'busy':LOCK.locked(),'sample_image':'/sample/portrait.png','sample_audio':'/sample/audio.wav',
      'example':examples[-1] if examples else None})
  if path.startswith('/api/jobs/'):
   key=path.rsplit('/',1)[-1]
   if key not in JOBS:return self.json_response(404,{'error':'任务不存在'})
   return self.json_response(200,JOBS[key])
  return super().do_GET()
 def do_POST(self):
  if urlparse(self.path).path!='/api/generate':return self.json_response(404,{'error':'接口不存在'})
  origin=self.headers.get('Origin')
  if origin and origin not in ['http://127.0.0.1:8017','http://localhost:8017']:
   return self.json_response(403,{'error':'仅接受本机演示页面请求'})
  try:length=int(self.headers.get('Content-Length','0'))
  except ValueError:return self.json_response(400,{'error':'上传格式无效'})
  if not 0<length<25*1024*1024:return self.json_response(400,{'error':'照片和录音合计请小于 25MB'})
  if not self.headers.get('Content-Type','').startswith('multipart/form-data'):
   return self.json_response(400,{'error':'请从演示页面上传照片和音频'})
  if not (ROOT/'.cache/photo-runtime-ready.json').exists():
   return self.json_response(503,{'error':'本机模型环境尚未准备完成'})
  if not LOCK.acquire(False):return self.json_response(409,{'error':'已有视频生成中，请等待完成'})
  try:
   form=cgi.FieldStorage(fp=self.rfile,headers=self.headers,environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers['Content-Type'],'CONTENT_LENGTH':str(length)})
   key=uuid.uuid4().hex;folder=OUTPUT/key;folder.mkdir(parents=True)
   use_sample=form.getfirst('sample')=='1'
   if use_sample:
    shutil.copyfile(SAMPLE/'portrait.png',folder/'portrait.png');shutil.copyfile(SAMPLE/'audio.wav',folder/'audio.wav')
   else:
    if 'image' not in form or 'audio' not in form:raise ValueError('请选择人物照片和录音')
    from PIL import Image
    image=Image.open(form['image'].file)
    if image.width*image.height>30_000_000:raise ValueError('请使用 3000 万像素以内的照片')
    image=image.convert('RGB');image.thumbnail((2048,2048));image.save(folder/'portrait.png')
    (folder/'input-audio').write_bytes(form['audio'].file.read())
    decoded=subprocess.run(['ffmpeg','-v','error','-y','-i',str(folder/'input-audio'),'-t','16','-ar','16000','-ac','1',str(folder/'audio.wav')],capture_output=True,timeout=45)
    if decoded.returncode:raise ValueError('无法解码录音，请尝试 WAV 或 MP3 文件')
   import wave
   with wave.open(str(folder/'audio.wav')) as wav:duration=wav.getnframes()/wav.getframerate()
   if not .25<=duration<=15.1:raise ValueError('第一版请使用 0.25–15 秒的录音')
   job={'id':key,'status':'queued','message':'正在准备生成','sample':use_sample,'duration':duration,
        'image':f'/results/{key}/portrait.png','audio':f'/results/{key}/audio.wav'}
   JOBS[key]=job;save(job);threading.Thread(target=generate,args=(job,),daemon=True).start()
   return self.json_response(202,job)
  except Exception as e:
   LOCK.release();return self.json_response(400,{'error':str(e)})

if __name__=='__main__':
 OUTPUT.mkdir(parents=True,exist_ok=True)
 server=ThreadingHTTPServer(('127.0.0.1',8017),partial(Handler,directory=str(ROOT/'demo')))
 print('Photo talking-head demo: http://127.0.0.1:8017/',flush=True);server.serve_forever()
