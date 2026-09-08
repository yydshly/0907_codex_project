"""Check actual media integrity; not a perceptual/emotion benchmark."""
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'.cache/companion'
def probe(path):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
def sound(path):
 return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ar','16000','-ac','1','-']),dtype=np.float32)

report={'note':'Media integrity only; no claim of natural emotion or professional lip-sync evaluation.','clips':[]}
manifest=json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))
assert len(manifest['clips'])==4
for clip in manifest['clips']:
 folder=ASSETS/clip['id'];video=folder/'result.mp4';info=probe(video)
 v=next(s for s in info['streams'] if s['codec_type']=='video');a=next(s for s in info['streams'] if s['codec_type']=='audio')
 assert (v['width'],v['height'])==(512,768) and int(v['nb_frames'])>100
 assert a['codec_name']=='aac'
 cap=cv2.VideoCapture(str(video));frames=[]
 for second in [1.,3.]:
  cap.set(cv2.CAP_PROP_POS_MSEC,second*1000);ok,frame=cap.read();assert ok;frames.append(frame)
 cap.release()
 change=float(np.abs(frames[0][170:355,145:370].astype(float)-frames[1][170:355,145:370]).mean());assert change>.5
 cv2.imwrite(str(folder/'verification-preview.jpg'),frames[1])
 audio=sound(video);source=sound(folder/'audio.wav');count=min(len(audio),len(source));corr=float(np.corrcoef(audio[:count],source[:count])[0,1]);assert corr>.95
 report['clips'].append({'id':clip['id'],'duration':info['format']['duration'],'frames':v['nb_frames'],'face_region_difference':round(change,3),'audio_correlation':round(corr,6),'render_seconds':clip['render_seconds']})
(ROOT/'notes/companion-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
