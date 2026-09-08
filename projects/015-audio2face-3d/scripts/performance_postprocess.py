"""Reuse adjacent optical flows and send identical composite frames directly to FFmpeg."""
import hashlib,subprocess,time
from concurrent.futures import ThreadPoolExecutor
import cv2,numpy as np
from stabilize_complete import crop_matrix
from performance_jobs import write

def clean_faces(faces,check=lambda:None):
 """Same filtering math/order as temporal_clean; each directed flow computed once."""
 gray={i:cv2.cvtColor(f,cv2.COLOR_BGR2GRAY) for i,f in enumerate(faces) if f is not None}
 edges=[i for i in gray if i+1 in gray]
 def pair(i):
  check()
  a,b=gray[i],gray[i+1]
  return i,(cv2.calcOpticalFlowFarneback(a,b,None,.5,3,19,3,5,1.2,0),cv2.calcOpticalFlowFarneback(b,a,None,.5,3,19,3,5,1.2,0))
 with ThreadPoolExecutor(max_workers=4) as pool:flows=dict(pool.map(pair,edges))
 yy,xx=np.mgrid[:256,:256].astype(np.float32)
 def clean(i):
  check();current=faces[i].astype(np.float32);total=current.copy();weights=np.ones((256,256),np.float32)
  for j in [i-1,i+1]:
   if j not in gray:continue
   flow,back=flows[i] if j>i else flows[j][::-1]
   mx=xx+flow[:,:,0];my=yy+flow[:,:,1]
   warped=cv2.remap(faces[j].astype(np.float32),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
   backward=cv2.remap(back,mx,my,cv2.INTER_LINEAR)
   error=np.linalg.norm(flow+backward,axis=2);difference=np.abs(warped-current).mean(axis=2)
   weight=.24*np.exp(-(error/1.5)**2-(difference/18)**2)
   weight[np.linalg.norm(flow,axis=2)>12]=0
   total+=warped*weight[:,:,None];weights+=weight
  return i,total/weights[:,:,None]
 with ThreadPoolExecutor(max_workers=4) as pool:return dict(pool.map(clean,gray))

def composite(original,face,box,mask,weight):
 if weight==0:return original
 mask=np.asarray(mask,np.float32)*weight;matrix=crop_matrix(box);size=(original.shape[1],original.shape[0])
 alpha=cv2.warpAffine(mask,matrix,size);patch=cv2.warpAffine(face*mask[:,:,None],matrix,size)
 # Preserve the original full-canvas affine sampling, but blend only its support.
 # Translating the affine origin into a smaller canvas changes OpenCV rounding.
 x,y,r,b=box;margin=int(np.ceil(max(abs(r-x),abs(b-y))/256))+2
 left=max(0,int(np.floor(min(x,r)))-margin);top=max(0,int(np.floor(min(y,b)))-margin)
 right=min(size[0],int(np.ceil(max(x,r)))+margin);bottom=min(size[1],int(np.ceil(max(y,b)))+margin)
 if right<=left or bottom<=top:return original
 full=original.copy();region=original[top:bottom,left:right]
 full[top:bottom,left:right]=np.clip(np.rint(region*(1-alpha[top:bottom,left:right,None])+patch[top:bottom,left:right]),0,255).astype(np.uint8)
 return full

def render(faces,source,boxes,masks,weights,folder,check=lambda:None,keep_frames=False):
 start=time.monotonic();cleaned=clean_faces(faces,check);clean_s=time.monotonic()-start
 frames=folder/'frames';frames.mkdir(exist_ok=True)
 active=np.flatnonzero(weights>0);samples={0,len(weights)-1}
 if len(active):samples.update([int(active[0]),int(active[len(active)//2]),int(active[-1])])
 target=folder/'encoding.mp4';height,width=source[0].shape[:2];audit=[];encode_start=time.monotonic()
 cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate','25','-i','pipe:0','-i',str(folder/'audio.wav'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(target)]
 with (folder/'encoder.log').open('wb') as log:
  process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log,stdout=subprocess.DEVNULL)
  try:
   for i,w in enumerate(weights):
    check();idx=i%len(source);full=composite(source[idx],cleaned.get(i),boxes[idx],masks[idx],w)
    audit.append({'frame':i,'weight':float(w),'sha256':hashlib.sha256(full.tobytes()).hexdigest()})
    if keep_frames or i in samples:cv2.imwrite(str(frames/f'{i:05d}.png'),full)
    # PNG decoding supplied RGB24 to FFmpeg in v1; preserve that conversion path.
    process.stdin.write(cv2.cvtColor(full,cv2.COLOR_BGR2RGB).tobytes())
   process.stdin.close();finish_start=time.monotonic()
   if process.wait(timeout=30)!=0:raise RuntimeError('Video encoder failed; see encoder.log')
   check();target.replace(folder/'result.mp4')
  finally:
   if process.poll() is None:process.kill();process.wait()
   if process.stdin and not process.stdin.closed:process.stdin.close()
   target.unlink(missing_ok=True)
 write(folder/'frame-audit.json',{'frames':audit,'saved_samples':sorted(samples),'all_frames_saved':keep_frames})
 return {'temporal_clean_s':round(clean_s,3),'composite_encode_s':round(time.monotonic()-encode_start,3),'encode_s':round(time.monotonic()-finish_start,3),'postprocess_s':round(time.monotonic()-start,3)}
