"""Retire the lip generator after the final audible sound; retain moving source.

Only terminal silence is handled. Internal pauses and all speech frames remain
unchanged. Versioned output preserves mask-v3 for a meaningful A/B comparison.
"""
import json
import subprocess
import wave
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/complete'
VERSION='tail-v4'
FPS=30


def read_video(path):
 cap=cv2.VideoCapture(str(path));frames=[]
 while True:
  ok,frame=cap.read()
  if not ok:break
  frames.append(frame)
 cap.release();return frames


def speech_end(path):
 with wave.open(str(path)) as wav:
  assert wav.getsampwidth()==2 and wav.getnchannels()==1
  rate=wav.getframerate()
  audio=np.frombuffer(wav.readframes(wav.getnframes()),dtype=np.int16).astype(np.float64)/32768
 hop=rate//100
 rms=np.array([np.sqrt(np.mean(audio[i:i+hop]**2)) for i in range(0,len(audio),hop)])
 # Conservative -60 dBFS keeps quiet tail consonants; this is tailored to clean
 # synthesized speech, not a general voice activity detector for noisy inputs.
 active=np.flatnonzero(rms>10**(-60/20))
 return min(len(audio)/rate,(int(active[-1])+1)*hop/rate) if len(active) else 0.


def encode(folder,dest,audio=None):
 cmd=['ffmpeg','-v','error','-y','-framerate',str(FPS),'-i',str(folder/'%05d.png')]
 if audio:cmd+=['-i',str(audio)]
 cmd+=['-c:v','libx264','-crf','18','-pix_fmt','yuv420p']
 if audio:cmd+=['-c:a','aac','-shortest']
 cmd+=['-movflags','+faststart',str(dest)]
 subprocess.run(cmd,check=True)


def main():
 for name in ['welcome','playful','soft']:
  folder=OUT/name;dest=folder/VERSION;render=dest/'frames';render.mkdir(parents=True,exist_ok=True)
  scene=json.loads((folder/'scene.json').read_text(encoding='utf-8'))
  source=read_video(scene['motion_source']);count=120
  end=speech_end(folder/'audio.wav');start=end+.10;finish=start+.22
  if finish>count/FPS:raise ValueError(f'{name}: insufficient terminal silence')
  weights=[]
  for i in range(count):
   old=cv2.imread(str(folder/'mask-v3/frames'/f'{i:05d}.png'));assert old is not None
   t=np.clip((i/FPS-start)/(finish-start),0,1)
   weight=1-t*t*(3-2*t);weights.append(float(weight))
   if weight==1:frame=old
   elif weight==0:frame=source[i]
   else:frame=np.rint(old.astype(float)*weight+source[i]*(1-weight)).astype(np.uint8)
   cv2.imwrite(str(render/f'{i:05d}.png'),frame)
  encode(render,dest/'result.mp4',folder/'audio.wav')
  # Matching source tail with eased ping-pong motion. First and last frames equal
  # the clip's settled endpoint; avoid jumping to an unrelated idle pose.
  idle=dest/'idle-frames';idle.mkdir(exist_ok=True)
  last=count-1;first=max(int(np.ceil(finish*FPS)),last-24)
  for i in range(90):
   index=round(last-(last-first)*(1-np.cos(2*np.pi*i/89))/2)
   cv2.imwrite(str(idle/f'{i:05d}.png'),source[index])
  encode(idle,dest/'idle.mp4')
  meta={'id':name,'version':VERSION,'detected_audio_end':end,'release_start':start,'release_end':finish,
   'generated_mouth_weight':weights,'frames':count,'fps':FPS,'idle_frames':90,'idle_source_range':[first,last],
   'note':'Terminal-silence gate for clean TTS; original moving face resumes after release. Source animation imperfections remain.'}
  (dest/'render.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
  print(f'{name}: speech ends {end:.2f}s; release {start:.2f}-{finish:.2f}s',flush=True)


if __name__=='__main__':main()
