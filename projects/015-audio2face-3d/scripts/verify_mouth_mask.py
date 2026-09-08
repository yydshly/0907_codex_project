"""Regression checks for ParseNet class mapping and regenerated mouth coverage."""
import json
import subprocess
import cv2
import numpy as np
import torch
from PIL import Image
from musetalk_complete import OUT, ROOT, Parser, read_video, parsing_face_mask
from stabilize_complete import normalized_crop, face_mask


class LegacyParser:
 def __init__(self,parser):self.net=parser.net
 def __call__(self,image):
  arr=np.asarray(image.resize((512,512))).astype(np.float32)/127.5-1
  labels=self.net(torch.from_numpy(arr.transpose(2,0,1).copy()).unsqueeze(0).cuda())[0].argmax(1)[0].cpu().numpy()
  return Image.fromarray(np.isin(labels,[1,11,12,13]).astype(np.uint8)*255)


def pcm(path):
 return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ar','16000','-ac','1','-'])


@torch.inference_mode()
def main():
 labels=np.arange(19,dtype=np.uint8)
 assert np.flatnonzero(parsing_face_mask(labels)).tolist()==[1,10,11,12]
 parser=Parser();old=LegacyParser(parser);report={'bug':'BiSeNet labels incorrectly used with ParseNet, excluding mouth cavity (10) and including hair (13).','clips':[]}
 for name in ['welcome','playful','soft']:
  folder=OUT/name;dest=folder/'mask-v3'
  scene=json.loads((folder/'scene.json').read_text(encoding='utf-8'))
  frames=read_video(scene['motion_source']);boxes=np.load(dest/'boxes.npy')
  video=read_video(dest/'result.mp4');assert len(video)==120
  assert pcm(dest/'result.mp4')==pcm(folder/'stable-v2/result.mp4')
  body_error=0
  for i in range(120):
   frame=cv2.imread(str(dest/'frames'/f'{i:05d}.png'));assert frame is not None
   body_error=max(body_error,int(np.abs(frame[410:].astype(int)-frames[i][410:].astype(int)).max()))
  assert body_error==0
  rows=[];coverage=[]
  for i in [20,40,60]:
   source=frames[i];box=boxes[i]
   before=face_mask(old,source,box);after=face_mask(parser,source,box)
   crop=normalized_crop(source,box)
   arr=cv2.resize(crop[:,:,::-1],(512,512)).astype(np.float32)/127.5-1
   classes=parser.net(torch.from_numpy(arr.transpose(2,0,1).copy()).unsqueeze(0).cuda())[0].argmax(1)[0].cpu().numpy()
   cavity=cv2.resize((classes==10).astype(np.uint8),(256,256),interpolation=cv2.INTER_NEAREST)>0
   if cavity.sum()>10:
    coverage.append({'frame':i,'cavity_pixels':int(cavity.sum()),'before_mean_alpha':round(float(before[cavity].mean()),4),'after_mean_alpha':round(float(after[cavity].mean()),4)})
   tiles=[]
   for label,frame in [('Source',source),('Rejected v2',cv2.imread(str(folder/'stable-v2/frames'/f'{i:05d}.png'))),('Mask fix v3',video[i])]:
    tile=normalized_crop(frame,box)[120:240,32:224]
    tile=cv2.resize(tile,(384,240));tile=cv2.copyMakeBorder(tile,26,0,0,0,cv2.BORDER_CONSTANT)
    cv2.putText(tile,f'{label} {i/30:.2f}s',(10,19),0,.5,(255,255,255),1);tiles.append(tile)
   rows.append(np.hstack(tiles))
  # Closed-mouth source frames may have no cavity pixels at all.
  assert all(c['after_mean_alpha']>=c['before_mean_alpha'] for c in coverage)
  cv2.imwrite(str(dest/'comparison.jpg'),np.vstack(rows))
  item={'id':name,'frames':120,'audio_identical':True,'body_max_error_before_encoding':body_error,'cavity_coverage':coverage}
  report['clips'].append(item);print(json.dumps(item),flush=True)
 improvements=[c for item in report['clips'] for c in item['cavity_coverage'] if c['after_mean_alpha']-c['before_mean_alpha']>.1]
 assert len(improvements)>=3,'Need actual open-mouth frame coverage improvements, not only label checks'
 (ROOT/'notes/mouth-mask-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
