"""Validate audio, actual lower-face changes, and preserved motion footage."""
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/complete'
report={'note':'Checks audiovisual integrity and preservation of body frames; not a professional phoneme-sync or identity quality score.','clips':[]}
def pcm(path):
 return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ar','16000','-ac','1','-']),dtype=np.float32)
for name in ['welcome','playful','soft']:
 folder=OUT/name;meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(folder/'result.mp4')]))
 video=next(s for s in info['streams'] if s['codec_type']=='video');audio=next(s for s in info['streams'] if s['codec_type']=='audio')
 assert (video['width'],video['height'],int(video['nb_frames']))==(512,768,120)
 assert video['r_frame_rate']=='30/1' and audio['codec_name']=='aac'
 before=pcm(folder/'audio.wav');after=pcm(folder/'result.mp4');count=min(len(before),len(after));correlation=float(np.corrcoef(before[:count],after[:count])[0,1]);assert correlation>.98
 frames=[];original=cv2.VideoCapture(meta['motion_source']);boxes=np.load(folder/'boxes.npy');body_error=[];mouth_change=[]
 for i in [20,40,60]:
  original.set(cv2.CAP_PROP_POS_FRAMES,i);ok,source=original.read();assert ok
  rendered=cv2.imread(str(folder/'frames'/f'{i:05d}.png'));assert rendered is not None
  body_error.append(int(np.abs(rendered[410:].astype(int)-source[410:].astype(int)).max()))
  x,y,x2,y2=boxes[i];mouth_change.append(float(np.abs(rendered[y+(y2-y)//2:y2,x:x2].astype(float)-source[y+(y2-y)//2:y2,x:x2]).mean()))
  frames.append(source[410:])
 original.release();assert max(body_error)==0 and np.mean(mouth_change)>1
 motion=float(np.abs(frames[0].astype(float)-frames[-1].astype(float)).mean());assert motion>1
 report['clips'].append({'id':name,'duration':float(info['format']['duration']),'frames':120,'audio_correlation':round(correlation,6),
   'body_pixel_max_difference_before_encoding':max(body_error),'lower_face_pixel_change':round(float(np.mean(mouth_change)),3),
   'source_body_temporal_change':round(motion,3),'render_seconds':meta['seconds']})
(ROOT/'notes/complete-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
