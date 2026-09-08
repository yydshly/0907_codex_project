"""Continuous source-time scheduling from speech energy, without changing audio."""
import numpy as np

def schedule(audio,rate,fps,count,phase=0.):
 hop=rate/fps
 rms=np.array([np.sqrt(np.mean(audio[int(i*hop):min(len(audio),int((i+1)*hop))]**2)) if int(i*hop)<len(audio) else 0. for i in range(count)])
 # Fixed gain reference is shared by segments; no per-segment peak normalization.
 activity=np.clip((20*np.log10(np.maximum(rms,1e-8))+45)/30,0,1)
 width=9;kernel=np.ones(width)/width
 activity=np.convolve(np.pad(activity,(width//2,width//2),mode='edge'),kernel,mode='valid')
 speed=.8+.45*activity
 positions=float(phase)+np.r_[0.,np.cumsum(speed[:-1])]
 return positions,float(phase+speed.sum()),{'speed_min':float(speed.min()),'speed_max':float(speed.max()),'method':'smoothed speech-energy source-time; not semantic gesture alignment'}

def sample_video(source,boxes,masks,positions):
 import cv2
 count=len(source);low=np.floor(positions).astype(int)%count;fraction=positions-np.floor(positions);high=(low+1)%count
 frames=[];out_boxes=[];out_masks=[]
 for a,b,t in zip(low,high,fraction):
  frames.append(cv2.addWeighted(source[a],1-float(t),source[b],float(t),0))
  out_boxes.append(boxes[a]*(1-t)+boxes[b]*t)
  out_masks.append(np.asarray(masks[a],np.float32)*(1-t)+np.asarray(masks[b],np.float32)*t)
 return frames,np.asarray(out_boxes),np.asarray(out_masks,dtype=np.float16),low,high,fraction
