"""Verify generated video integrity and record motion, not semantic success."""
import hashlib
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/motion'
report={'source_sha256':hashlib.sha256((ROOT/'.cache/companion/neutral.png').read_bytes()).hexdigest(),
 'note':'Frame differences demonstrate changing video pixels, not correct gestures, identity preservation or a static camera. See manual assessment.',
 'clips':[],'assessment':json.loads((OUT/'selection.json').read_text(encoding='utf-8'))}
for name in ['listen','listen-v2','playful','annoyed']:
 path=OUT/name/'result.mp4'
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
 stream=next(x for x in info['streams'] if x['codec_type']=='video')
 assert (stream['width'],stream['height'])==(512,768)
 assert int(stream['nb_frames'])==121 and stream['r_frame_rate']=='30/1'
 assert not any(x['codec_type']=='audio' for x in info['streams'])
 cap=cv2.VideoCapture(str(path));frames=[]
 for second in [.1,1.1,2.1,3.1]:
  cap.set(cv2.CAP_PROP_POS_MSEC,1000*second);ok,frame=cap.read();assert ok;frames.append(frame)
 cap.release()
 torso=[f[370:710,80:430].astype(float) for f in frames]
 motion=float(np.mean([np.abs(torso[i+1]-torso[i]).mean() for i in range(3)]));assert motion>1
 report['clips'].append({'id':name,'duration':float(info['format']['duration']),'frames':121,'fps':30,'audio':False,
   'torso_region_frame_difference':round(motion,3),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT/'notes/motion-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True,indent=2))
