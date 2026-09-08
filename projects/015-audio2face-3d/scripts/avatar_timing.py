"""Reusable offline speech-state envelope for clean synthesized speech."""
from dataclasses import asdict,dataclass
import wave
import numpy as np

@dataclass(frozen=True)
class TimingConfig:
 threshold_db:float=-60.
 hold_s:float=.10
 release_s:float=.22
 attack_s:float=.08
 min_pause_s:float=.60

def read_pcm(path):
 with wave.open(str(path)) as w:
  if w.getsampwidth()!=2 or w.getnchannels()!=1:raise ValueError('Expected mono PCM16 WAV')
  rate=w.getframerate();audio=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float64)/32768
 return audio,rate

def smooth(value):
 value=np.clip(value,0,1)
 return value*value*(3-2*value)

def envelope(audio,rate,fps,frame_count,config=TimingConfig()):
 if rate<=0 or fps<=0 or frame_count<1:raise ValueError('Invalid timing dimensions')
 if min(config.hold_s,config.min_pause_s)<0 or min(config.attack_s,config.release_s)<=0:raise ValueError('Invalid timing configuration')
 hop=max(1,round(rate*.01));times=np.arange(frame_count)/fps
 rms=np.array([np.sqrt(np.mean(audio[i:i+hop]**2)) for i in range(0,len(audio),hop)])
 active=rms>10**(config.threshold_db/20)
 weights=np.ones(frame_count);events=[]
 if not np.any(active):
  return np.zeros(frame_count),{'config':asdict(config),'events':[{'type':'silent','start':0,'end':frame_count/fps}],'speech_start':None,'speech_end':None}
 first=int(np.flatnonzero(active)[0])*hop/rate
 end=(int(np.flatnonzero(active)[-1])+1)*hop/rate
 if first>0:
  weights=np.minimum(weights,smooth((times-max(0,first-config.attack_s))/min(first,config.attack_s)))
  events.append({'type':'attack','start':max(0,first-config.attack_s),'end':first})
 # Internal pauses must be long enough for a complete release and restart.
 change=np.diff(np.r_[False,~active,False].astype(int))
 for a,b in zip(np.flatnonzero(change==1),np.flatnonzero(change==-1)):
  start=a*hop/rate;stop=b*hop/rate
  if start<=first or stop>=end:continue
  if stop-start<max(config.min_pause_s,config.hold_s+config.release_s+config.attack_s):continue
  down=1-smooth((times-(start+config.hold_s))/config.release_s)
  up=smooth((times-(stop-config.attack_s))/config.attack_s)
  weights=np.minimum(weights,np.maximum(down,up))
  events.append({'type':'pause','start':start,'end':stop})
 weights=np.minimum(weights,1-smooth((times-(end+config.hold_s))/config.release_s))
 events.append({'type':'release','start':end+config.hold_s,'end':end+config.hold_s+config.release_s})
 return weights,{'config':asdict(config),'events':events,'speech_start':first,'speech_end':end}
