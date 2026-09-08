"""Replay exactly the same inferred faces through old and new postprocessing."""
import hashlib,json,shutil,time
import cv2,numpy as np
from performance_jobs import ROOT,ASSETS,JOBS,write
from avatar_timing import read_pcm,envelope
from stabilize_complete import temporal_clean
from performance_postprocess import composite,render
from musetalk_complete import read_video
from render_avatar_timing import encode

def main(key):
 folder=JOBS/key;job=json.loads((folder/'job.json').read_text(encoding='utf-8'));asset=ASSETS/job['state']
 source=read_video(asset/'motion.mp4');raw=np.load(folder/'inference-faces.npy');pcm,rate=read_pcm(folder/'audio.wav');weights,_=envelope(pcm,rate,25,len(raw))
 faces=[raw[i] if w>0 else None for i,w in enumerate(weights)];boxes=np.load(asset/'float_boxes.npy');masks=np.load(asset/'masks.npy',mmap_mode='r')
 base=folder/'benchmark-v1';fast=folder/'benchmark-v2';base.mkdir(exist_ok=True);fast.mkdir(exist_ok=True)
 for dest in [base,fast]:shutil.copy2(folder/'audio.wav',dest/'audio.wav')
 start=time.monotonic();cleaned={};runs=[];run=[]
 for i,f in enumerate(faces):
  if f is not None:run.append(i)
  elif run:runs.append(run);run=[]
 if run:runs.append(run)
 for run in runs:
  seq=[faces[i] for i in run]
  for j,i in enumerate(run):cleaned[i]=temporal_clean(seq,j)
 clean_s=time.monotonic()-start;frames=base/'frames';frames.mkdir(exist_ok=True);hashes=[]
 for i,w in enumerate(weights):
  idx=i%len(source);full=composite(source[idx],cleaned.get(i),boxes[idx],masks[idx],w)
  hashes.append(hashlib.sha256(full.tobytes()).hexdigest());cv2.imwrite(str(frames/f'{i:05d}.png'),full)
 encode(frames,base/'result.mp4',25,base/'audio.wav');old_s=time.monotonic()-start
 cv2.setNumThreads(1);post=render(faces,source,boxes,masks,weights,fast)
 audit=json.loads((fast/'frame-audit.json').read_text());assert hashes==[r['sha256'] for r in audit['frames']],'Composite frame mismatch'
 before=read_video(base/'result.mp4');after=read_video(fast/'result.mp4');assert len(before)==len(after)
 mse=float(np.mean([np.mean((a.astype(float)-b.astype(float))**2) for a,b in zip(before,after)]))
 assert mse==0,'Encoded video pixels differ'
 report={'job':key,'state':job['state'],'frames':len(faces),'old_temporal_clean_s':round(clean_s,3),'old_postprocess_s':round(old_s,3),'new':post,'identical_input_frames':len(hashes),'decoded_video_mse':mse,'speedup':round(old_s/post['postprocess_s'],3)}
 write(ROOT/'notes'/f'performance-v2-benchmark-{job["state"]}.json',report);print(json.dumps(report))
if __name__=='__main__':
 import sys
 main(sys.argv[1])
