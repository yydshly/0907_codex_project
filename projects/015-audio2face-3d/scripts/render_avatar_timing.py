"""Config-driven postprocess: no fixed scene count, video length or frame rate."""
import argparse
import hashlib
import json
import time
from pathlib import Path
import cv2
import numpy as np
from avatar_timing import TimingConfig,envelope,read_pcm
from settle_speech_tail import read_video
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def encode(frames,target,fps,audio=None):
 cmd=['ffmpeg','-v','error','-y','-framerate',str(fps),'-i',str(frames/'%05d.png')]
 if audio:cmd+=['-i',str(audio)]
 cmd+=['-c:v','libx264','-crf','18','-pix_fmt','yuv420p']
 if audio:cmd+=['-c:a','aac','-shortest']
 subprocess.run(cmd+['-movflags','+faststart',str(target)],check=True)

def run(profile_path):
 profile=json.loads(profile_path.read_text(encoding='utf-8'));config=TimingConfig(**profile['timing'])
 for spec in profile['clips']:
  start=time.monotonic();base=ROOT/spec['input'];dest=ROOT/spec['output'];dest.mkdir(parents=True,exist_ok=True)
  scene=json.loads((base/'scene.json').read_text(encoding='utf-8'))
  source=read_video(scene['motion_source'])
  cap=cv2.VideoCapture(scene['motion_source']);fps=cap.get(cv2.CAP_PROP_FPS);cap.release()
  paths=sorted((base/spec['generated_frames']).glob('*.png'));count=len(paths)
  if not paths or len(source)<count:raise ValueError('Missing generated frames or insufficient source video')
  audio,rate=read_pcm(base/'audio.wav')
  if len(audio)/rate>count/fps+1/fps+.001:raise ValueError('Audio exceeds available frames; provide a longer motion source')
  weights,timeline=envelope(audio,rate,fps,count,config)
  frames=dest/'frames';frames.mkdir(exist_ok=True)
  for i,path in enumerate(paths):
   generated=cv2.imread(str(path));w=weights[i]
   if generated.shape!=source[i].shape:raise ValueError('Source and generated frame dimensions differ')
   combined=np.rint(generated.astype(float)*w+source[i]*(1-w)).astype(np.uint8)
   cv2.imwrite(str(frames/f'{i:05d}.png'),combined)
  encode(frames,dest/'result.mp4',fps,base/'audio.wav')
  # Preserve the accepted matching idle when the terminal output is identical.
  import shutil
  accepted=base/'tail-v4'
  endpoint=cv2.imread(str(accepted/'frames'/f'{count-1:05d}.png')) if accepted.exists() else None
  if endpoint is not None and np.array_equal(endpoint,cv2.imread(str(frames/f'{count-1:05d}.png'))):
   shutil.copy2(accepted/'idle.mp4',dest/'idle.mp4')
  else:
   # Reusable fallback: keep moving source only when the gate fully released.
   if weights[-1]!=0:raise ValueError('No settled endpoint; extend the source/audio with terminal silence')
   idle=dest/'idle-frames';idle.mkdir(exist_ok=True)
   first=max(0,count-1-round(.8*fps));idle_count=max(2,round(3*fps))
   for i in range(idle_count):
    j=round(count-1-(count-1-first)*(1-np.cos(2*np.pi*i/(idle_count-1)))/2)
    cv2.imwrite(str(idle/f'{i:05d}.png'),source[j])
   encode(idle,dest/'idle.mp4',fps)
  timeline.update(fps=fps,frames=count,weights=weights.tolist())
  (dest/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
  # Hash input content including raw generation, not merely their filenames.
  hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [base/'audio.wav',Path(scene['motion_source']),profile_path]}
  digest=hashlib.sha256()
  for p in paths:digest.update(p.read_bytes())
  hashes['generated_frames_sha256']=digest.hexdigest()
  manifest={'id':spec['id'],'version':profile['version'],'media_duration_s':count/fps,'postprocess_s':round(time.monotonic()-start,3),'input_hashes':hashes,'output_sha256':hashlib.sha256((dest/'result.mp4').read_bytes()).hexdigest()}
  (dest/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
  print(json.dumps(manifest),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('profile',type=Path);run(p.parse_args().profile.resolve())
