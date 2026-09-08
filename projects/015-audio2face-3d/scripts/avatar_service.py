"""Upload admission and durable GPU jobs. Preparation never shares a GPU turn."""
import threading,time,uuid
import avatar_registry as registry
from performance_jobs import JOBS,write,read,update

class AvatarService:
 def __init__(self,lock,worker_status):self.lock=lock;self.worker_status=worker_status
 def upload(self,raw,name,motion_backend="local-facial"):
  if self.worker_status().get('status')!='ready':raise BlockingIOError('模型服务尚未就绪')
  if not self.lock.acquire(False):raise BlockingIOError('正在生成内容，请先停止对话或等待人物准备完成')
  try:
   avatar=registry.create(raw,name,motion_backend);key=uuid.uuid4().hex;folder=JOBS/key
   data={'id':key,'kind':'avatar_prepare','avatar_id':avatar['id'],'status':'queued','message':'照片已上传，等待自动检查','progress':0,'submitted_at':time.time()}
   write(folder/'job.json',data);registry.change(avatar['id'],job=key)
   write(folder/'request.json',data)
   threading.Thread(target=self.wait,args=(folder,),daemon=True).start()
   return registry.get(avatar['id'])
  except Exception:self.lock.release();raise
 def wait(self,folder):
  try:
   while (folder/'request.json').exists():time.sleep(.3)
  finally:self.lock.release()
 def retry(self,key,regenerate=False):
  avatar=registry.get(key)
  if avatar['status'] not in ('failed','cancelled'):raise ValueError('只有未完成的人物可以继续准备')
  if self.worker_status().get('status')!='ready' or not self.lock.acquire(False):raise BlockingIOError('生成资源正在使用，请稍后重试')
  try:
   if regenerate:
    # Explicit UI action, unlike a normal retry. Archive the paid request
    # record; successful or still-identified tasks continue to be reused.
    for path in (registry.AVATARS/key/'assets').glob('*/generation.json'):
     previous=read(path)
     if previous.get('status')=='Fail' or not previous.get('task_id'):
      write(path.with_name('replaced-'+uuid.uuid4().hex+'.json'),{'previous':previous,'reason':'explicit regenerate action; may incur another provider charge','at':time.time()});path.unlink()
   folder=JOBS/uuid.uuid4().hex
   data={'id':folder.name,'kind':'avatar_prepare','avatar_id':key,'status':'queued','message':'继续准备，复用已完成的视频任务','progress':0,'submitted_at':time.time()}
   write(folder/'job.json',data);registry.change(key,status='queued',job=folder.name,message=data['message']);write(folder/'request.json',data)
   threading.Thread(target=self.wait,args=(folder,),daemon=True).start();return registry.get(key)
  except Exception:self.lock.release();raise
 def recover(self):
  # Server restart must not admit dialogue over an already running preparation.
  for p in JOBS.glob('*/request.json'):
   if read(p).get('kind')=='avatar_prepare' and self.lock.acquire(False):
    threading.Thread(target=self.wait,args=(p.parent,),daemon=True).start();break
