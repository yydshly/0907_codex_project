"""Live local acceptance. Creates rejection/cancellation fixtures, never alters ready avatars."""
import io,json,time,urllib.request,urllib.error
from pathlib import Path
from PIL import Image
from performance_jobs import ROOT,read
from avatar_registry import AVATARS,STATES,asset_for

BASE='http://127.0.0.1:8022'
def api(path,data=None,raw=None):
 body=raw if raw is not None else json.dumps(data).encode() if data is not None else None
 req=urllib.request.Request(BASE+path,data=body,headers={'Content-Type':'application/octet-stream' if raw is not None else 'application/json'})
 with urllib.request.urlopen(req,timeout=20) as response:return json.load(response)
def rejects(path,code,data=None,raw=None):
 try:api(path,data,raw)
 except urllib.error.HTTPError as e:assert e.code==code,(path,e.code);return
 raise AssertionError('Request should have been rejected: '+path)
def idle():
 end=time.monotonic()+180
 while time.monotonic()<end:
  if not api('/api/dialogue/status')['busy']:return
  time.sleep(.5)
 raise TimeoutError('Existing task still busy; stopped acceptance without interrupting it')
def terminal(avatar):
 end=time.monotonic()+120
 while time.monotonic()<end:
  job=api('/api/jobs/'+avatar['job'])
  if job['status'] in ('done','failed','cancelled'):
   idle();return api('/api/avatars/'+avatar['id'])
  time.sleep(.3)
 raise TimeoutError('Fixture timeout')

def main():
 import cv2,numpy as np
 report={'avatars':[],'http_checks':[]}
 for letter in ('a','b'):
  key=read(ROOT/f'.cache/avatar-test-{letter}.json')['id'];avatar=api('/api/avatars/'+key);assert avatar['status']=='ready'
  manifest=api('/api/workbench?avatar='+key);assert manifest['avatar']['id']==key
  assert {a['id'] for a in manifest['assets']}==set(STATES)
  for a in manifest['assets']:
   assert a['video'].startswith(avatar['asset_base']+'/')
   folder=AVATARS/key/'assets'/a['id']
   first=cv2.imread(str(folder/'frames/00000.png'));last=cv2.imread(str(folder/'frames/00099.png'));assert np.abs(first.astype(float)-last).mean()<.01
  assert read(AVATARS/key/'validation.json')['passed']
  report['avatars'].append({'id':key,'name':avatar['name'],'source_sha256':avatar['source_sha256'],'preparation_s':round(avatar['ready_at']-avatar['created_at'],3),'states':list(STATES),'loop_continuity_passed':True})
 assert report['avatars'][0]['source_sha256']!=report['avatars'][1]['source_sha256']
 rejects('/api/avatars/not-an-id',404)
 idle();rejects('/api/avatars?name=invalid',400,raw=b'not a photo')
 report['http_checks']+=['invalid id 404','invalid image 400']
 # Blank synthetic image tests the real face detector, not a mocked response.
 stream=io.BytesIO();Image.new('RGB',(512,768),(180,180,180)).save(stream,'PNG')
 idle();blank=api('/api/avatars?name=No-face-validation',raw=stream.getvalue())
 rejects('/api/dialogue/session',400,{'avatar_id':blank['id']})
 failure=terminal(blank);assert failure['status']=='failed' and '人脸' in failure.get('message',''),failure
 report['no_face']={'id':blank['id'],'status':failure['status'],'message':failure.get('message')}
 idle();cancel=api('/api/avatars?name=Cancellation-validation',raw=(ROOT/'.cache/avatar-samples/auburn.png').read_bytes())
 end=time.monotonic()+30
 while time.monotonic()<end:
  current=api('/api/jobs/'+cancel['job'])
  if current['status']=='preparing' and current.get('progress',0)>=.05:break
  if current['status'] in ('failed','done','cancelled'):raise AssertionError(current)
  time.sleep(.2)
 time.sleep(2);start=time.monotonic();api('/api/cancel/'+cancel['job'],{});result=terminal(cancel)
 assert result['status']=='cancelled';report['cancel']={'id':cancel['id'],'job':cancel['job'],'release_s':round(time.monotonic()-start,3),'status':result['status']}
 time.sleep(3);assert api('/api/avatars/'+cancel['id'])['status']=='cancelled'
 rejects('/api/dialogue/session',400,{'avatar_id':cancel['id']})
 report['http_checks']+=['unready session rejected','cancelled session rejected','resource lock released after cancellation']
 # Session binding after the server/worker restart and after cancellation.
 for item in report['avatars']:
  session=api('/api/dialogue/session',{'avatar_id':item['id']});assert api('/api/dialogue/session/'+session['id'])['avatar_id']==item['id']
  rejects('/api/dialogue/turn',400,{'session':session['id'],'avatar_id':'xiaoqing','text':'hello'})
 report['http_checks']+=['ready avatars persist across restart','cross-avatar turn rejected']
 report['worker_after']=api('/api/dialogue/status')['worker'];assert report['worker_after']['status']=='ready'
 report['passed']=True;dest=ROOT/'notes/user-avatars-verification.json';dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS: two independent avatar packs, HTTP isolation, no-face rejection, cancellation and restart persistence')

if __name__=='__main__':main()
