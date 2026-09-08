"""Local MuseTalk 1.5 with cached facexlib landmarks and lower-face blending.

Core VAE/audio/UNet inference is from upstream MuseTalk. Facial preprocessing
uses existing RetinaFace/FAN/ParseNet weights to avoid a Windows MMCV build.
Only lower-face pixels are blended; the motion source is retained elsewhere.
"""
import argparse
import gc
import json
import subprocess
import sys
import time
from pathlib import Path
import cv2
import numpy as np
import torch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/complete'
WEIGHTS=ROOT/'vendor/musetalk-models'
FACE=ROOT/'vendor/photo-models'
sys.path.insert(0,str(ROOT/'vendor/MuseTalk'))
torch.set_num_threads(4)

# ParseNet/GPEN ordering differs from MuseTalk's BiSeNet ordering:
# 1 skin, 10 mouth cavity, 11 upper lip, 12 lower lip, 13 hair.
PARSENET_FACE_LABELS=(1,10,11,12)

def parsing_face_mask(labels):
 return np.isin(labels,PARSENET_FACE_LABELS).astype(np.uint8)*255

def read_video(path):
 cap=cv2.VideoCapture(str(path));frames=[]
 while True:
  ok,f=cap.read()
  if not ok:break
  frames.append(f)
 cap.release();return frames

@torch.inference_mode()
def prepare(scenes,check=lambda:None):
 from facexlib.detection import init_detection_model
 from facexlib.alignment import init_alignment_model,landmark_98_to_68
 detector=init_detection_model('retinaface_resnet50',device='cuda',model_rootpath=str(FACE))
 align=init_alignment_model('awing_fan',device='cuda',model_rootpath=str(FACE))
 for name in scenes:
  folder=OUT/name
  if (folder/'boxes.npy').exists():continue
  scene=json.loads((folder/'scene.json').read_text(encoding='utf-8'))
  frames=read_video(scene['motion_source']);boxes=[]
  for i,frame in enumerate(frames):
   check()
   detections=detector.detect_faces(frame,conf_threshold=.9)
   if len(detections)==0:raise RuntimeError(f'Face detection failed: {name} frame {i}')
   d=max(detections,key=lambda a:(a[2]-a[0])*(a[3]-a[1]))
   x,y,x2,y2=d[:4];w=x2-x;h=y2-y
   l=max(0,int(x-.15*w));r=min(frame.shape[1],int(x2+.15*w))
   t=max(0,int(y-.18*h));b=min(frame.shape[0],int(y2+.1*h))
   landmarks=landmark_98_to_68(align.get_landmarks(frame[t:b,l:r]));landmarks+=np.array([l,t])
   middle=landmarks[29,1];bottom=landmarks[:,1].max()
   top=max(0,middle-(bottom-middle))
   box=[max(0,landmarks[:,0].min()),top,min(frame.shape[1],landmarks[:,0].max()),min(frame.shape[0],bottom+10)]
   boxes.append(box)
   if i%30==0:print(f'{name} tracking {i}/{len(frames)}',flush=True)
  boxes=np.asarray(boxes)
  # Centered smoothing avoids extra frame delay.
  boxes=np.array([np.mean(boxes[max(0,i-2):min(len(boxes),i+3)],axis=0) for i in range(len(boxes))]).round().astype(int)
  np.save(folder/'boxes.npy',boxes)
  x,y,x2,y2=boxes[len(boxes)//2];cv2.imwrite(str(folder/'face-crop.jpg'),frames[len(frames)//2][y:y2,x:x2])
  print(name+' face track cached',flush=True)
 del detector,align;gc.collect();torch.cuda.empty_cache()

class Parser:
 def __init__(self):
  from facexlib.parsing import init_parsing_model
  self.net=init_parsing_model('parsenet',device='cuda',model_rootpath=str(FACE))
 def __call__(self,image,mode='raw'):
  arr=np.asarray(image.resize((512,512))).astype(np.float32)/127.5-1
  tensor=torch.from_numpy(arr.transpose(2,0,1).copy()).unsqueeze(0).cuda()
  labels=self.net(tensor)[0].argmax(1)[0].cpu().numpy()
  # Do not use BiSeNet's [1,11,12,13]: it omits ParseNet's mouth cavity.
  mask=parsing_face_mask(labels)
  return Image.fromarray(mask)

@torch.inference_mode()
def prepare_audio(scenes):
 from transformers import WhisperModel
 from musetalk.utils.audio_processor import AudioProcessor
 processor=AudioProcessor(str(WEIGHTS/'whisper'))
 whisper=WhisperModel.from_pretrained(str(WEIGHTS/'whisper'),torch_dtype=torch.float16).cuda().eval()
 for name in scenes:
  folder=OUT/name
  features,length=processor.get_audio_feature(str(folder/'audio.wav'))
  chunks=processor.get_whisper_chunk(features,'cuda',torch.float16,whisper,length,fps=30)
  torch.save(chunks.cpu(),folder/'audio_features.pt');print(name+' audio cached',flush=True)

@torch.inference_mode()
def generate(scenes):
 from accelerate import init_empty_weights
 from diffusers import UNet2DConditionModel
 from musetalk.models.vae import VAE
 from musetalk.models.unet import PositionalEncoding
 from musetalk.utils.blending import get_image
 print('Loading MuseTalk UNet (memory-mapped weights)',flush=True)
 config=json.loads((WEIGHTS/'unet/config.json').read_text())
 with init_empty_weights():unet=UNet2DConditionModel.from_config(config)
 state=torch.load(str(WEIGHTS/'unet/unet.pth'),map_location='cpu',mmap=True,weights_only=True)
 unet.load_state_dict(state,assign=True);del state
 unet=unet.to(device='cuda',dtype=torch.float16).eval();gc.collect()
 vae=VAE(str(WEIGHTS/'vae'),use_float16=True)
 pe=PositionalEncoding().to(device='cuda',dtype=torch.float16)
 parser=Parser()
 print('Models ready',flush=True)
 for name in scenes:
  folder=OUT/name
  if (folder/'result.mp4').exists():continue
  start=time.monotonic();torch.manual_seed(2026)
  scene=json.loads((folder/'scene.json').read_text(encoding='utf-8'))
  frames=read_video(scene['motion_source']);boxes=np.load(folder/'boxes.npy')
  audio=torch.load(str(folder/'audio_features.pt'),weights_only=True).cuda()
  count=min(len(frames),len(audio));generated=folder/'frames';generated.mkdir(exist_ok=True)
  changes=[];body_diffs=[]
  for i in range(count):
   frame=frames[i];x,y,x2,y2=boxes[i]
   crop=cv2.resize(frame[y:y2,x:x2],(256,256),interpolation=cv2.INTER_LANCZOS4)
   latent=vae.get_latents_for_unet(crop)
   prediction=unet(latent,torch.tensor([0],device='cuda'),encoder_hidden_states=pe(audio[i:i+1])).sample
   face=vae.decode_latents(prediction)[0]
   face=cv2.resize(face,(x2-x,y2-y),interpolation=cv2.INTER_LANCZOS4)
   combined=get_image(frame,face,[x,y,x2,y2],fp=parser,mode='raw')
   changes.append(float(np.abs(combined[y+(y2-y)//2:y2,x:x2].astype(float)-frame[y+(y2-y)//2:y2,x:x2]).mean()))
   body_diffs.append(float(np.abs(combined[max(y2+30,400):].astype(float)-frame[max(y2+30,400):]).max()))
   cv2.imwrite(str(generated/f'{i:05d}.png'),combined)
   if i%20==0:print(f'{name} lip sync {i}/{count}',flush=True)
  subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(generated/'%05d.png'),'-i',str(folder/'audio.wav'),
   '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(folder/'result.mp4')],check=True)
  scene.update(video=f'/complete/{name}/result.mp4',source_video=f'/motion/{scene["motion"]}/result.mp4',
    model='MuseTalk 1.5',fps=30,frames=count,seconds=round(time.monotonic()-start,1),
    lower_face_change_mean=round(float(np.mean(changes)),4),body_pixel_max_change_before_encoding=max(body_diffs),status='done')
  (folder/'result.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2),encoding='utf-8')
  print(f'{name} complete in {scene["seconds"]} seconds',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--audio',action='store_true');parser.add_argument('scenes',nargs='*',default=['welcome','playful','soft']);args=parser.parse_args()
 if args.prepare:prepare(args.scenes)
 elif args.audio:prepare_audio(args.scenes)
 else:generate(args.scenes)
