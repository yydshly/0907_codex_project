"""Precompute geometry, deterministic VAE inputs and correct ParseNet masks."""
import gc,json,hashlib
import numpy as np,torch
import musetalk_complete as core
from stabilize_complete import normalized_crop,deterministic_latents,face_mask
from scipy.signal import savgol_filter
ROOT=core.ROOT;OUT=ROOT/'.cache/performance'

@torch.inference_mode()
def main(output=None,progress=lambda *args:None):
 global OUT
 if output is not None:OUT=output
 names=[a['id'] for a in json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))['assets']]
 for name in names:
  folder=OUT/name;cache=folder/'cache.json'
  if cache.exists() and json.loads(cache.read_text()).get('source_sha256')!=hashlib.sha256((folder/'motion.mp4').read_bytes()).hexdigest():
   (folder/'boxes.npy').unlink(missing_ok=True);cache.unlink()
 progress('自动跟踪人脸与嘴部',.68)
 if all(all((OUT/name/file).exists() for file in ['cache.json','boxes.npy','float_boxes.npy','masks.npy','latents.pt']) for name in names):
  progress('已复用全部口型缓存',.97);return
 core.OUT=OUT;core.prepare(names,check=lambda:progress('自动跟踪人脸与嘴部',.68))
 from musetalk.models.vae import VAE
 vae=VAE(str(core.WEIGHTS/'vae'),use_float16=True);parser=core.Parser()
 for name in names:
  folder=OUT/name
  if (folder/'cache.json').exists():continue
  frames=core.read_video(folder/'motion.mp4');boxes=savgol_filter(np.load(folder/'boxes.npy').astype(float),9,2,axis=0)
  latents=[];masks=[]
  for i,frame in enumerate(frames):
   if i%10==0:progress('准备嘴部缓存：'+name,.72+.25*(names.index(name)+i/len(frames))/len(names))
   latents.append(deterministic_latents(vae,normalized_crop(frame,boxes[i])).cpu())
   masks.append(face_mask(parser,frame,boxes[i]))
  masks=np.asarray(masks)
  smoothed=np.array([np.minimum(masks[max(0,i-1):min(len(masks),i+2)].mean(0),masks[i]) for i in range(len(masks))],dtype=np.float16)
  torch.save(torch.cat(latents),folder/'latents.pt');np.save(folder/'masks.npy',smoothed);np.save(folder/'float_boxes.npy',boxes)
  (folder/'cache.json').write_text(json.dumps({'frames':len(frames),'fps':25,'mask_labels':[1,10,11,12],'encoding':'deterministic posterior mode','source_sha256':hashlib.sha256((folder/'motion.mp4').read_bytes()).hexdigest()}))
  print(name+' cached',flush=True)

if __name__=='__main__':main()
