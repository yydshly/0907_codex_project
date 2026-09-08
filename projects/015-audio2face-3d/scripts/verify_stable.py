"""Compare temporal residuals without confusing head movement with lip flicker."""
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/complete'

def read_video(path):
 cap=cv2.VideoCapture(str(path));frames=[]
 while True:
  ok,f=cap.read()
  if not ok:break
  frames.append(f)
 cap.release();return frames

def crop(frame,box):
 x,y,x2,y2=box
 return cv2.warpAffine(frame,np.float32([[(x2-x)/256,0,x],[0,(y2-y)/256,y]]),
  (256,256),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT_101)

def temporal_metrics(faces):
 residual=[];motion=[];sharpness=[]
 yy,xx=np.mgrid[:256,:256].astype(np.float32)
 roi=np.s_[145:228,48:208]
 for i in range(1,len(faces)-1):
  gray=cv2.cvtColor(faces[i],cv2.COLOR_BGR2GRAY)
  aligned=[]
  for j in [i-1,i+1]:
   other=cv2.cvtColor(faces[j],cv2.COLOR_BGR2GRAY)
   flow=cv2.calcOpticalFlowFarneback(gray,other,None,.5,3,19,3,5,1.2,0)
   aligned.append(cv2.remap(other.astype(np.float32),xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101))
  residual.append(float(np.abs(gray.astype(float)-(aligned[0]+aligned[1])/2)[roi].mean()))
  motion.append(float(np.abs(gray.astype(float)-cv2.cvtColor(faces[i-1],cv2.COLOR_BGR2GRAY).astype(float))[roi].mean()))
  sharpness.append(float(cv2.Laplacian(gray,cv2.CV_32F)[roi].var()))
 return dict(flow_aligned_temporal_residual=round(float(np.mean(residual)),4),
  unaligned_temporal_change=round(float(np.mean(motion)),4),mouth_laplacian_variance=round(float(np.mean(sharpness)),4))

def pcm(path):
 return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ar','16000','-ac','1','-']),dtype=np.float32)

report={'note':'Motion-compensated pixel residual is a flicker proxy, not a perceptual quality or phoneme-sync score. Both renders are measured with identical baseline boxes. Body preservation is checked before encoding.','clips':[]}
for name in ['welcome','playful','soft']:
 folder=OUT/name;scene=json.loads((folder/'scene.json').read_text(encoding='utf-8'))
 boxes=np.load(folder/'boxes.npy');source=read_video(scene['motion_source'])
 before=read_video(folder/'result.mp4');after=read_video(folder/'stable-v2/result.mp4')
 assert len(before)==len(after)==120
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(folder/'stable-v2/result.mp4')]))
 vs=next(s for s in info['streams'] if s['codec_type']=='video')
 assert vs['r_frame_rate']=='30/1' and (vs['width'],vs['height'])==(512,768)
 a=pcm(folder/'result.mp4');b=pcm(folder/'stable-v2/result.mp4');assert len(a)==len(b)
 assert np.array_equal(a,b),'Audio must remain sample-identical'
 metrics={key:temporal_metrics([crop(f,boxes[i]) for i,f in enumerate(frames[:120])])
  for key,frames in [('source',source),('before',before),('after',after)]}
 body_error=0
 for i in range(120):
  frame=cv2.imread(str(folder/'stable-v2/frames'/f'{i:05d}.png'))
  body_error=max(body_error,int(np.abs(frame[410:].astype(int)-source[i][410:].astype(int)).max()))
 assert body_error==0
 change=1-metrics['after']['flow_aligned_temporal_residual']/metrics['before']['flow_aligned_temporal_residual']
 report['clips'].append({'id':name,'metrics':metrics,'temporal_residual_reduction_percent':round(change*100,1),'audio_samples_identical':True,'body_max_error':body_error,'frames':120})
 # Consecutive mouth frames: source / baseline / stable, common face coordinates.
 rows=[]
 for label,frames in [('Source',source),('Before',before),('Stable',after)]:
  tiles=[]
  for i in range(36,48,2):
   face=crop(frames[i],boxes[i])[120:240,32:224]
   tile=cv2.copyMakeBorder(face,24,0,0,0,cv2.BORDER_CONSTANT,value=(25,25,25))
   cv2.putText(tile,f'{label} {i/30:.2f}s',(8,16),cv2.FONT_HERSHEY_SIMPLEX,.4,(240,240,240),1)
   tiles.append(tile)
  rows.append(np.hstack(tiles))
 cv2.imwrite(str(folder/'stable-v2/comparison.jpg'),np.vstack(rows))
 print(json.dumps(report['clips'][-1]),flush=True)
(ROOT/'notes/stability-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
