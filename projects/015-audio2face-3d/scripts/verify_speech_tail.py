"""Verify speech preservation and complete removal of generated silent-tail lips."""
import json
import subprocess
import cv2
import numpy as np
from settle_speech_tail import ROOT,OUT,VERSION,read_video

def audio(path):
 return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','s16le','-ac','1','-ar','16000','-'])

report={'clips':[]}
for name in ['welcome','playful','soft']:
 folder=OUT/name;dest=folder/VERSION
 meta=json.loads((dest/'render.json').read_text())
 scene=json.loads((folder/'scene.json').read_text(encoding='utf-8'))
 source=read_video(scene['motion_source'])
 assert len(read_video(dest/'result.mp4'))==120
 assert audio(dest/'result.mp4')==audio(folder/'mask-v3/result.mp4')
 before_error=tail_error=body_error=0;rows=[]
 for i,weight in enumerate(meta['generated_mouth_weight']):
  new=cv2.imread(str(dest/'frames'/f'{i:05d}.png'))
  old=cv2.imread(str(folder/'mask-v3/frames'/f'{i:05d}.png'))
  if weight==1:before_error=max(before_error,int(np.abs(new.astype(int)-old.astype(int)).max()))
  if weight==0:tail_error=max(tail_error,int(np.abs(new.astype(int)-source[i].astype(int)).max()))
  body_error=max(body_error,int(np.abs(new[410:].astype(int)-source[i][410:].astype(int)).max()))
  if name=='welcome' and i in [68,74,80,95]:
   x,y,x2,y2=np.load(folder/'mask-v3/boxes.npy')[i].round().astype(int)
   tiles=[]
   for label,f in [('Before',old),('Tail fix',new)]:
    tile=cv2.resize(f[y+(y2-y)//2:y2,x:x2],(384,200))
    tile=cv2.copyMakeBorder(tile,28,0,0,0,cv2.BORDER_CONSTANT)
    cv2.putText(tile,f'{label} {i/30:.2f}s',(10,20),0,.55,(255,255,255),1);tiles.append(tile)
   rows.append(np.hstack(tiles))
 assert before_error==tail_error==body_error==0
 endpoint=cv2.imread(str(dest/'frames/00119.png'))
 assert np.array_equal(endpoint,cv2.imread(str(dest/'idle-frames/00000.png')))
 assert np.array_equal(endpoint,cv2.imread(str(dest/'idle-frames/00089.png')))
 assert len(read_video(dest/'idle.mp4'))==90
 item={'id':name,'audio_identical':True,'speech_frame_max_error':before_error,'silent_tail_vs_source_max_error':tail_error,
  'body_max_error':body_error,'idle_endpoint_exact_before_encoding':True,'release_start':meta['release_start'],'release_end':meta['release_end']}
 report['clips'].append(item);print(json.dumps(item),flush=True)
 if rows:cv2.imwrite(str(dest/'tail-comparison.jpg'),np.vstack(rows))
(ROOT/'notes/speech-tail-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
