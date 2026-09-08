"""Durable MiniMax I2V requests. Never blindly resubmit a paid request."""
import base64,hashlib,json,time,urllib.request
from urllib.parse import urlsplit,urlencode
from performance_jobs import read,write
from minimax_dialogue import config,post,ProviderError

MODEL='MiniMax-Hailuo-2.3'
COMMON='[Static shot] A continuous natural conversational portrait of the same person in the reference. Preserve face identity, age, hairstyle, clothing, framing, background and lighting. Realistic skin and human timing. Visible but gentle shoulder breathing and relaxed upper torso movement. Keep the face near frontal and unobstructed. Lips softly closed when resting, no talking. No camera motion, zoom, cuts or large gestures. '
PROMPTS={
 'listen':'Listen attentively, shift posture slightly forward, tilt the head, briefly glance aside then return warm eye contact, blink naturally and give one small nod.',
 'think':'Consider a question: eyes briefly glance up to the side, eyebrows gently lift, head inclines with a small shoulder shift, then return attention to the viewer.',
 'comfort':'Offer quiet reassurance with compassionate eyes, soften into a warm small smile, lean the upper torso slightly toward the viewer, slowly nod once and relax.',
 'playful':'React playfully: raise one eyebrow, give a restrained mischievous smile, tilt the head, make a small amused shoulder lift, then relax with friendly eye contact.',
 'annoyed':'React with mild playful displeasure, gently knit the eyebrows, press lips softly together, give one small head shake with a slight shoulder shift, then relax. No broad smile or anger outburst.',
 'affirm':'Show warm approval, brighten the eyes, smile modestly, give two small natural nods with a subtle forward upper body movement, then settle.'}

def connection():
 c=config();u=urlsplit(c['speech_url'])
 if u.scheme!='https' or u.hostname not in {'api.minimax.cn','api.minimax.io','api.minimaxi.com','api-bj.minimaxi.com'}:raise ProviderError('Invalid MiniMax host')
 return u.scheme+'://'+u.netloc,c['speech_key']

def get(path,values):
 base,key=connection();req=urllib.request.Request(base+path+'?'+urlencode(values),headers={'Authorization':'Bearer '+key})
 with urllib.request.urlopen(req,timeout=30) as r:data=json.load(r)
 code=data.get('base_resp',{}).get('status_code',0)
 if code and not (path=='/v1/query/video_generation' and data.get('status')=='Fail'):raise ProviderError('MiniMax 视频接口错误码 '+str(code))
 return data

def generate(source,folder,state,check=lambda:None,progress=lambda text:None):
 folder.mkdir(parents=True,exist_ok=True);metadata=folder/'generation.json';target=folder/'generated.mp4'
 sha=hashlib.sha256(source.read_bytes()).hexdigest()
 if metadata.exists():
  info=read(metadata)
  if info.get('source_sha256')!=sha:raise ValueError('Cached video belongs to another source')
  if target.exists() and info.get('status')=='downloaded':return target
  if info.get('status') in ('prepared','rejected') and not info.get('task_id'):
   metadata.unlink();return generate(source,folder,state,check,progress)
  if not info.get('task_id'):raise ProviderError('上次视频提交结果不确定或失败，未自动重复扣费；请查看准备日志')
 else:
  prompt=COMMON+PROMPTS[state]+' Finish in a relaxed pose close to the reference image.'
  info={'model':MODEL,'source_sha256':sha,'prompt':prompt,'duration':6,'resolution':'768P','submitted_at':time.time(),'status':'submitting'}
  # Cancellation before POST is known not to have submitted a paid task.
  info['status']='prepared';write(metadata,info);check();base,key=connection()
  info['status']='submitting';write(metadata,info)
  try:
   result=post(base+'/v1/video_generation',key,{'model':MODEL,'first_frame_image':'data:image/png;base64,'+base64.b64encode(source.read_bytes()).decode(),'prompt':prompt,'duration':6,'resolution':'768P','prompt_optimizer':False})
  except ProviderError as e:
   if e.code in (2056,1008,1004,1002):info.update(status='rejected',error_code=e.code);write(metadata,info)
   raise
  info.update(task_id=result['task_id'],status='submitted');write(metadata,info)
 deadline=time.monotonic()+900
 while True:
  check();data=get('/v1/query/video_generation',{'task_id':info['task_id']});status=data['status'];progress(status)
  info.update(status=status);write(metadata,info)
  if status=='Success':break
  if status=='Fail':raise ProviderError('MiniMax 未能生成这段动作，请查看准备记录')
  if time.monotonic()>deadline:raise TimeoutError('MiniMax 视频任务仍未完成，任务 ID 已保存')
  for _ in range(40):check();time.sleep(.25)
 file=get('/v1/files/retrieve',{'file_id':data['file_id']})['file'];url=file['download_url']
 if urlsplit(url).scheme!='https':raise ProviderError('Video download requires HTTPS')
 # The provider returns a signed media URL. Never send API credentials to it.
 temp=folder/'download.tmp';total=0
 try:
  with urllib.request.urlopen(url,timeout=60) as r,temp.open('wb') as out:
   while True:
    check();chunk=r.read(1024*1024)
    if not chunk:break
    total+=len(chunk)
    if total>150*1024*1024:raise ValueError('Video exceeds local download limit')
    out.write(chunk)
  check();temp.replace(target)
 finally:temp.unlink(missing_ok=True)
 info.update(status='downloaded',file_id=data['file_id'],finished_at=time.time(),video_sha256=hashlib.sha256(target.read_bytes()).hexdigest());write(metadata,info)
 return target
