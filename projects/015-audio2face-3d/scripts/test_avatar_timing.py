"""Behavioral regression tests: protect phonemes and accepted terminal release."""
import json
import subprocess
import unittest
from pathlib import Path
import cv2
import numpy as np
from avatar_timing import envelope,read_pcm

ROOT=Path(__file__).resolve().parents[1]

class TimingTests(unittest.TestCase):
 def test_short_pause_keeps_mouth_ready(self):
  audio=np.ones(16000*3)*.1;audio[16000:20000]=0
  weights,meta=envelope(audio,16000,30,90)
  self.assertFalse(any(e['type']=='pause' for e in meta['events']))
  self.assertTrue(np.all(weights[30:38]==1))
 def test_long_pause_releases_and_restarts(self):
  audio=np.ones(16000*4)*.1;audio[16000:32000]=0
  weights,meta=envelope(audio,16000,30,120)
  self.assertEqual(weights[45],0);self.assertEqual(weights[60],1)
  self.assertEqual(sum(e['type']=='pause' for e in meta['events']),1)
 def test_variable_fps_and_quiet_tail(self):
  audio=np.zeros(16000*7);audio[8000:32000]=.1;audio[32000:36000]=.0012
  for fps in [25,30,60]:
   weights,meta=envelope(audio,16000,fps,7*fps)
   self.assertEqual(meta['speech_end'],2.25)
   self.assertEqual(weights[round(2.2*fps)],1)
   self.assertEqual(weights[3*fps],0)
   self.assertEqual(weights[0],0)
 def test_all_silent(self):
  w,m=envelope(np.zeros(16000),16000,25,25)
  self.assertTrue(np.all(w==0));self.assertIsNone(m['speech_end'])
 def test_speech_at_end_not_cut(self):
  w,_=envelope(np.ones(16000)*.1,16000,30,30)
  self.assertEqual(w[-1],1)
 def test_real_clips_preserve_accepted_speech_and_tail(self):
  results=[]
  for name in ['welcome','playful','soft']:
   folder=ROOT/'.cache/complete'/name;meta=json.loads((folder/'timing-v5/timeline.json').read_text())
   audio,rate=read_pcm(folder/'audio.wav');speech_start=meta['speech_start']
   max_error=0
   for i in range(meta['frames']):
    if i/meta['fps']<speech_start:continue
    old=cv2.imread(str(folder/'tail-v4/frames'/f'{i:05d}.png'))
    new=cv2.imread(str(folder/'timing-v5/frames'/f'{i:05d}.png'))
    max_error=max(max_error,int(np.abs(old.astype(int)-new.astype(int)).max()))
   self.assertEqual(max_error,0)
   def pcm(path):return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','s16le','-ac','1','-ar','16000','-'])
   self.assertEqual(pcm(folder/'tail-v4/result.mp4'),pcm(folder/'timing-v5/result.mp4'))
   self.assertEqual((folder/'tail-v4/idle.mp4').read_bytes(),(folder/'timing-v5/idle.mp4').read_bytes())
   results.append({'id':name,'speech_and_tail_pixel_max_error':max_error,'audio_identical':True,'accepted_idle_identical':True,'internal_pause_modified':False})
  (ROOT/'notes/timing-v5-verification.json').write_text(json.dumps({'behavioral_cases':6,'clips':results},indent=2),encoding='utf-8')

if __name__=='__main__':unittest.main()
