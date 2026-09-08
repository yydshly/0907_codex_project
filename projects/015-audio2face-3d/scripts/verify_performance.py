"""Verify actual artifacts: template continuity, audio mux and silent-mouth release."""
import hashlib,json,subprocess
import cv2,numpy as np
from performance_jobs import ROOT,ASSETS,JOBS
from avatar_timing import read_pcm,envelope
from avatar_registry import asset_for

def frames(path):
 cap=cv2.VideoCapture(str(path));data=[]
 while True:
  ok,frame=cap.read()
  if not ok:break
  data.append(frame)
 fps=cap.get(cv2.CAP_PROP_FPS);cap.release();return data,fps

def main():
 report={'templates':[],'jobs':[]}
 for asset in json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))['assets']:
  folder=ASSETS/asset['id'];source,fps=frames(folder/'motion.mp4')
  cache=json.loads((folder/'cache.json').read_text())
  assert len(source)==100 and fps==25 and source[0].shape==(768,512,3)
  assert cache['source_sha256']==hashlib.sha256((folder/'motion.mp4').read_bytes()).hexdigest()
  first=cv2.imread(str(folder/'frames/00000.png'));last=cv2.imread(str(folder/'frames/00099.png'))
  seam=float(np.abs(first.astype(float)-last).mean());assert seam<.01
  movement=float(np.abs(source[50].astype(float)-source[0]).mean());assert movement>.05
  report['templates'].append({'state':asset['id'],'frames':100,'fps':25,'loop_endpoint_mean_difference':seam,'midframe_mean_difference':round(movement,3),'cache_matches':True})
 for path in JOBS.glob('*/job.json'):
  job=json.loads(path.read_text(encoding='utf-8'))
  if job['status']!='done' or job.get('mode')=='segmented' or job.get('kind')=='avatar_prepare':continue
  folder=path.parent;source,_=frames(asset_for(job)/'motion.mp4');result,fps=frames(folder/'result.mp4')
  phase=job.get('frame_offset',0)%len(source);source=source[phase:]+source[:phase]
  motion_path=folder/'motion.json'
  if motion_path.exists():
   positions=json.loads(motion_path.read_text(encoding='utf-8'))['positions'];original=source
   source=[cv2.addWeighted(original[int(np.floor(t))%len(original)],1-(t%1),original[(int(np.floor(t))+1)%len(original)],t%1,0) for t in positions]
  pcm,rate=read_pcm(folder/'audio.wav');weights,timeline=envelope(pcm,rate,fps,len(result))
  assert weights[-1]==0 and abs(len(result)/fps-len(pcm)/rate)<.081
  idle=np.flatnonzero(weights==0);active=np.flatnonzero(weights==1)
  audit_path=folder/'frame-audit.json'
  audit=json.loads(audit_path.read_text(encoding='utf-8')) if audit_path.exists() else None
  if audit:
   assert len(audit['frames'])==len(result)
   assert np.allclose([r['weight'] for r in audit['frames']],weights)
   for i in idle:assert audit['frames'][i]['sha256']==hashlib.sha256(source[i%len(source)].tobytes()).hexdigest()
   for i in audit['saved_samples']:
    frame=cv2.imread(str(folder/'frames'/f'{i:05d}.png'));assert hashlib.sha256(frame.tobytes()).hexdigest()==audit['frames'][i]['sha256']
  else:
   for i in idle:assert np.array_equal(cv2.imread(str(folder/'frames'/f'{i:05d}.png')),source[i%len(source)])
  decoded=subprocess.check_output(['ffmpeg','-v','error','-i',str(folder/'result.mp4'),'-f','s16le','-ar',str(rate),'-ac','1','-'])
  mux=np.frombuffer(decoded,np.int16).astype(float)/32768;n=min(len(pcm),len(mux));correlation=float(np.corrcoef(pcm[:n],mux[:n])[0,1]);assert correlation>.97
  i=int(active[len(active)//2])
  if audit:i=min((n for n in audit['saved_samples'] if weights[n]>0),key=lambda n:abs(n-i))
  change=float(np.abs(cv2.imread(str(folder/'frames'/f'{i:05d}.png')).astype(float)-source[i%len(source)]).mean());assert change>0
  report['jobs'].append({'id':job['id'],'text':job['text'],'state':job['state'],'metrics':job['metrics'],'silent_frames_identical_to_motion':len(idle),'audio_correlation':round(correlation,5),'speech_end':timeline['speech_end'],'mouth_release_end':timeline['events'][-1]['end']})
 assert len(report['jobs'])>=2,'Generate at least two new-text samples first'
 dest=ROOT/'notes/performance-verification.json';dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'PASS: {len(report["templates"])} templates, {len(report["jobs"])} audio-conditioned videos. Report: {dest}')

if __name__=='__main__':main()
