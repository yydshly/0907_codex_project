"""Compare only the affected face rectangle with original full-frame composition."""
import json,time
import cv2,numpy as np
from performance_jobs import ROOT,ASSETS,write
from performance_postprocess import composite
from stabilize_complete import crop_matrix
from musetalk_complete import read_video

def full_composite(original,face,box,mask,weight):
 if weight==0:return original
 mask=np.asarray(mask,np.float32)*weight;matrix=crop_matrix(box);size=(original.shape[1],original.shape[0])
 alpha=cv2.warpAffine(mask,matrix,size);patch=cv2.warpAffine(face*mask[:,:,None],matrix,size)
 return np.clip(np.rint(original*(1-alpha[:,:,None])+patch),0,255).astype(np.uint8)

def main():
 cv2.setNumThreads(1);faces=np.load(ROOT/'.cache/inference-benchmark/original.npy');report=[]
 for state in ['comfort','annoyed']:
  asset=ASSETS/state;source=read_video(asset/'motion.mp4');boxes=np.load(asset/'float_boxes.npy');masks=np.load(asset/'masks.npy',mmap_mode='r')
  outputs=[];times=[]
  for fn in [full_composite,composite]:
   start=time.monotonic();out=[fn(source[i],faces[i%len(faces)].astype(np.float32),boxes[i],masks[i],1 if i%5 else .33) for i in range(100)];times.append(time.monotonic()-start);outputs.append(out)
  equal=sum(np.array_equal(a,b) for a,b in zip(*outputs));mae=float(np.mean([np.abs(a.astype(float)-b).mean() for a,b in zip(*outputs)]));maximum=max(int(np.abs(a.astype(np.int16)-b).max()) for a,b in zip(*outputs))
  row={'state':state,'frames':100,'old_s':times[0],'roi_s':times[1],'identical_frames':equal,'pixel_mae':mae,'pixel_max':maximum};report.append(row);print(json.dumps(row),flush=True)
 write(ROOT/'notes/avatar-composite-benchmark.json',report)
if __name__=='__main__':main()
