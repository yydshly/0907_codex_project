"""Versioned, deterministic MuseTalk render with subpixel crops and temporal cleanup.

Keeps baseline files and upstream code unchanged. All temporal filters are centered
on the current frame; audio and the frame timeline are never shifted.
"""
import argparse
import gc
import json
import subprocess
import time
import cv2
import numpy as np
import torch
from PIL import Image
from scipy.signal import savgol_filter
from musetalk_complete import OUT, WEIGHTS, Parser, read_video


def crop_matrix(box):
 x,y,x2,y2=box
 return np.float32([[(x2-x)/256,0,x], [0,(y2-y)/256,y]])


def normalized_crop(frame,box):
 return cv2.warpAffine(frame,crop_matrix(box),(256,256),
  flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT_101)


def deterministic_latents(vae,crop):
 parts=[]
 for masked in [True,False]:
  image=vae.preprocess_img(crop,half_mask=masked).to(vae.vae.dtype)
  parts.append(vae.vae.encode(image).latent_dist.mode()*vae.scaling_factor)
 return torch.cat(parts,dim=1)


def face_mask(parser,frame,box):
 # Keep the original parser's expanded face context, then align its mask to
 # the same floating-point crop as the generator.
 from musetalk.utils.blending import get_crop_box
 expanded,_=get_crop_box(np.round(box).astype(int),1.5)
 l,t,r,b=expanded
 image=Image.fromarray(frame[:,:,::-1]).crop(expanded)
 mask=np.asarray(parser(image).resize(image.size)).copy()
 local=box-np.array([l,t,l,t])
 mask=normalized_crop(mask,local).astype(np.float32)/255
 mask[:128]=0
 # Feather entirely inside the crop to avoid rectangular edge seams.
 mask[:,:5]=0;mask[:,-5:]=0;mask[-5:]=0
 return cv2.GaussianBlur(mask,(17,17),0)


def temporal_clean(faces,index):
 """Light bidirectional, motion-compensated denoising, with mismatch rejection.

 Optical flow tracks lip opening rather than averaging unaligned mouths. Large
 motion, inconsistent flow or different textures receive little/no smoothing.
 """
 current=faces[index].astype(np.float32)
 gray=cv2.cvtColor(faces[index],cv2.COLOR_BGR2GRAY)
 yy,xx=np.mgrid[:256,:256].astype(np.float32)
 total=current.copy();weights=np.ones((256,256),np.float32)
 for j in [index-1,index+1]:
  if not 0<=j<len(faces):continue
  other=faces[j];other_gray=cv2.cvtColor(other,cv2.COLOR_BGR2GRAY)
  flow=cv2.calcOpticalFlowFarneback(gray,other_gray,None,.5,3,19,3,5,1.2,0)
  back=cv2.calcOpticalFlowFarneback(other_gray,gray,None,.5,3,19,3,5,1.2,0)
  mx=xx+flow[:,:,0];my=yy+flow[:,:,1]
  warped=cv2.remap(other.astype(np.float32),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
  backward=cv2.remap(back,mx,my,cv2.INTER_LINEAR)
  error=np.linalg.norm(flow+backward,axis=2)
  difference=np.abs(warped-current).mean(axis=2)
  weight=.24*np.exp(-(error/1.5)**2-(difference/18)**2)
  weight[np.linalg.norm(flow,axis=2)>12]=0
  total+=warped*weight[:,:,None];weights+=weight
 return total/weights[:,:,None]


@torch.inference_mode()
def generate(names,version='mask-v3'):
 from accelerate import init_empty_weights
 from diffusers import UNet2DConditionModel
 from musetalk.models.vae import VAE
 from musetalk.models.unet import PositionalEncoding
 config=json.loads((WEIGHTS/'unet/config.json').read_text())
 with init_empty_weights():unet=UNet2DConditionModel.from_config(config)
 state=torch.load(str(WEIGHTS/'unet/unet.pth'),map_location='cpu',mmap=True,weights_only=True)
 unet.load_state_dict(state,assign=True);del state
 unet.to(device='cuda',dtype=torch.float16).eval();gc.collect()
 vae=VAE(str(WEIGHTS/'vae'),use_float16=True)
 pe=PositionalEncoding().to(device='cuda',dtype=torch.float16)
 parser=Parser()
 for name in names:
  start=time.monotonic();folder=OUT/name;dest=folder/version;dest.mkdir(exist_ok=True)
  scene=json.loads((folder/'scene.json').read_text(encoding='utf-8'))
  frames=read_video(scene['motion_source'])
  boxes=savgol_filter(np.load(folder/'boxes.npy').astype(np.float32),9,2,axis=0)
  audio=torch.load(str(folder/'audio_features.pt'),weights_only=True).cuda()
  count=min(len(frames),len(audio));faces=[];masks=[]
  np.save(dest/'boxes.npy',boxes)
  for i in range(count):
   crop=normalized_crop(frames[i],boxes[i])
   latent=deterministic_latents(vae,crop)
   prediction=unet(latent,torch.tensor([0],device='cuda'),encoder_hidden_states=pe(audio[i:i+1])).sample
   faces.append(vae.decode_latents(prediction)[0])
   masks.append(face_mask(parser,frames[i],boxes[i]))
   if i%30==0:print(f'{name}: deterministic inference {i}/{count}',flush=True)
  output=dest/'frames';output.mkdir(exist_ok=True)
  for i in range(count):
   face=temporal_clean(faces,i)
   mask=np.mean(masks[max(0,i-1):min(count,i+2)],axis=0)
   # Current-frame mask vetoes newly occluded regions instead of trailing hands.
   mask=np.minimum(mask,masks[i])
   size=(frames[i].shape[1],frames[i].shape[0]);matrix=crop_matrix(boxes[i])
   alpha=cv2.warpAffine(mask,matrix,size,flags=cv2.INTER_LINEAR)
   patch=cv2.warpAffine(face*mask[:,:,None],matrix,size,flags=cv2.INTER_LINEAR)
   combined=np.clip(np.round(frames[i]*(1-alpha[:,:,None])+patch),0,255).astype(np.uint8)
   cv2.imwrite(str(output/f'{i:05d}.png'),combined)
  subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(output/'%05d.png'),'-i',str(folder/'audio.wav'),
   '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(dest/'result.mp4')],check=True)
  (dest/'render.json').write_text(json.dumps({'id':name,'frames':count,'seconds':round(time.monotonic()-start,1),
   'changes':['deterministic VAE posterior mode','centered subpixel crop smoothing','centered mask smoothing with current-frame veto',
   'motion-compensated adjacent-frame texture denoising','correct ParseNet mouth cavity and hair label mapping'],
   'version':version,'audio_changed':False},indent=2),encoding='utf-8')
  print(f'{name}: {version} ready in {time.monotonic()-start:.1f}s',flush=True)


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('scenes',nargs='*',default=['welcome','playful','soft'])
 parser.add_argument('--version',default='mask-v3');args=parser.parse_args()
 generate(args.scenes,args.version)
