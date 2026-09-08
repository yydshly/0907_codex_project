"""Immutable visual identities. Voice and conversational persona remain independent."""
import hashlib,io,time,uuid
from performance_jobs import ROOT,ASSETS,JOBS,read,write

AVATARS=ROOT/'.cache/avatars'
DEFAULT='xiaoqing'
VERSION='portrait-pack-v1'
STATES=('listen','think','comfort','playful','annoyed','affirm')

def valid(key):
 return isinstance(key,str) and (key==DEFAULT or len(key)==32 and all(c in '0123456789abcdef' for c in key))

def get(key=DEFAULT,ready=False):
 if not valid(key):raise ValueError('人物不存在')
 if key==DEFAULT:
  return {'id':DEFAULT,'name':'小晴 · 原始角色','status':'ready','asset_base':'/assets','poster':'/assets/listen/poster.jpg','version':'legacy-v3','builtin':True}
 path=AVATARS/key/'avatar.json'
 if not path.exists():raise ValueError('人物不存在')
 data=read(path)
 if ready and data['status']!='ready':raise ValueError('此人物尚未准备好，请等待或重新上传照片')
 return data

def asset_root(key=DEFAULT):
 get(key,ready=True)
 return ASSETS if key==DEFAULT else AVATARS/key/'assets'

def asset_for(job):
 if job.get('state') not in STATES:raise ValueError('未知表情')
 return asset_root(job.get('avatar_id',DEFAULT))/job['state']

def listing():
 return [get()]+[get(p.parent.name) for p in sorted(AVATARS.glob('*/avatar.json'),key=lambda p:p.stat().st_mtime,reverse=True)]

def normalize(raw):
 from PIL import Image,ImageOps,UnidentifiedImageError
 if not raw or len(raw)>12*1024*1024:raise ValueError('照片需小于 12 MB')
 try:
  with Image.open(io.BytesIO(raw)) as im:
   if im.format not in ('JPEG','PNG','WEBP') or getattr(im,'n_frames',1)!=1:raise ValueError('请使用静态 JPG、PNG 或 WebP 照片')
   w,h=im.size
   if min(w,h)<256 or w*h>20_000_000:raise ValueError('照片短边至少 256 像素，总像素不超过 2000 万')
   im=ImageOps.exif_transpose(im).convert('RGBA')
   base=Image.new('RGBA',im.size,(238,235,230,255));base.alpha_composite(im)
   im=ImageOps.pad(base.convert('RGB'),(512,768),method=Image.Resampling.LANCZOS,color=(238,235,230))
   out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
 except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as e:raise ValueError('无法读取照片，请上传有效图片') from e

def create(raw,name,motion_backend="local-facial"):
 if motion_backend not in ("local-facial","minimax-body"):raise ValueError("未知动作模式")
 if not isinstance(name,str) or not 1<=len(name.strip())<=30:raise ValueError('人物名称需为 1–30 字')
 image=normalize(raw);key=uuid.uuid4().hex;folder=AVATARS/key;folder.mkdir(parents=True)
 (folder/'source.png').write_bytes(image)
 data={'id':key,'name':name.strip(),'status':'queued','created_at':time.time(),'version':'portrait-body-v2' if motion_backend=='minimax-body' else VERSION,'motion_backend':motion_backend,'source_sha256':hashlib.sha256(image).hexdigest(),'asset_base':f'/avatars-media/{key}/assets','poster':f'/avatars-media/{key}/source.png','scope':'单人照片；面部表情、眼神、眨眼和小幅头动；不生成手臂动作；声音独立配置'}
 if motion_backend=='minimax-body':data['scope']='MiniMax 生成面部、头肩和半身动作；动作片段存在循环边界；声音独立配置'
 write(folder/'avatar.json',data);return data

def change(key,**values):
 data=get(key);data.update(values);write(AVATARS/key/'avatar.json',data);return data
