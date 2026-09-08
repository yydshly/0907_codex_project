"""One-photo preparation CLI, also consumed by the exclusive GPU queue."""
import argparse,hashlib,json,traceback
from avatar_registry import AVATARS,STATES,get,change
from performance_jobs import JOBS,read,write,update,cancelled

def main():
 parser=argparse.ArgumentParser();parser.add_argument('avatar');parser.add_argument('job');parser.add_argument('phase',choices=['motion','cache','validate']);args=parser.parse_args()
 avatar=get(args.avatar);root=AVATARS/avatar['id'];out=root/'assets';job=JOBS/args.job
 def progress(message,value):
  if cancelled(job):raise InterruptedError('已取消人物准备')
  update(job,status='preparing',message=message,progress=round(value,3))
 try:
  if args.phase=='motion':
   if avatar.get('motion_backend')=='minimax-body':
    from build_body_assets import main as build
   else:
    from build_performance_assets import main as build
   build(root/'source.png',out,progress)
  elif args.phase=='cache':
   from prepare_performance_cache import main as cache
   cache(out,progress)
  else:
   import cv2,numpy as np,torch
   progress('校验六种动作与嘴部缓存',.98)
   manifest=read(out/'manifest.json')
   if {a['id'] for a in manifest['assets']}!=set(STATES):raise ValueError('动作资产不完整')
   evidence=[]
   for asset in manifest['assets']:
    folder=out/asset['id'];cap=cv2.VideoCapture(str(folder/'motion.mp4'));count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS);cap.release()
    boxes=np.load(folder/'float_boxes.npy');masks=np.load(folder/'masks.npy',mmap_mode='r');latents=torch.load(folder/'latents.pt',weights_only=True)
    if count!=asset['frames'] or fps!=25 or len(boxes)!=count or len(masks)!=count or len(latents)!=count:raise ValueError('动作或嘴部缓存帧数不一致')
    if not np.isfinite(boxes).all() or not np.isfinite(masks).all() or not torch.isfinite(latents).all():raise ValueError('人物缓存包含无效数值')
    if not (boxes[:,2]>boxes[:,0]).all() or not (boxes[:,3]>boxes[:,1]).all() or float(masks.mean())<=0:raise ValueError('人脸范围或嘴部遮罩无效')
    sha=hashlib.sha256((folder/'motion.mp4').read_bytes()).hexdigest()
    if read(folder/'cache.json')['source_sha256']!=sha or asset['source_sha256']!=avatar['source_sha256']:raise ValueError('人物资产来源不一致')
    first=cv2.imread(str(folder/'frames/00000.png'));middle=cv2.imread(str(folder/f'frames/{count//2:05d}.png'));last=cv2.imread(str(folder/f'frames/{count-1:05d}.png'))
    if first is None or middle is None or last is None:raise ValueError('缺少动作校验帧')
    seam=float(np.abs(first.astype(float)-last).mean());movement=float(np.abs(first.astype(float)-middle).mean())
    if (avatar.get('motion_backend')!='minimax-body' and seam>=.01) or movement<=.05:raise ValueError('动作循环不连续或没有有效运动')
    asset['video']=avatar['asset_base']+'/'+asset['id']+'/motion.mp4';asset['poster']=avatar['asset_base']+'/'+asset['id']+'/poster.jpg'
    write(folder/'asset.json',asset);evidence.append({'state':asset['id'],'frames':count,'motion_sha256':sha,'loop_difference':seam,'movement':movement})
   manifest.update(avatar_id=avatar['id'],character=avatar['name'],version=avatar['version']);write(out/'manifest.json',manifest)
   write(root/'validation.json',{'passed':True,'assets':evidence,'scope':avatar['scope']})
 except Exception as e:
  change(avatar['id'],message=str(e));raise

if __name__=='__main__':main()
