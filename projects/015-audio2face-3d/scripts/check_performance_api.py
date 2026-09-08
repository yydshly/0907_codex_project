"""Local integration check: invalid inputs, busy guard, actual GPU cancellation."""
import json,time,urllib.request,urllib.error,sys
from performance_jobs import ROOT,JOBS
BASE='http://127.0.0.1:8022'
def call(path,payload=None,origin=None):
 headers={'Content-Type':'application/json'}
 if origin:headers['Origin']=origin
 request=urllib.request.Request(BASE+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
 try:
  with urllib.request.urlopen(request,timeout=10) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,json.load(e)
def main():
 postprocess='--postprocess' in sys.argv
 encoding='--encoding' in sys.argv
 assert call('/api/generate',{'text':'','state':'think'})[0]==400
 sample={'text':'让我想一想，今天我们可以先整理一下心情，然后再慢慢开始。','state':'think'}
 assert call('/api/generate',sample,origin='https://example.com')[0]==403
 status,job=call('/api/generate',sample);assert status==202,(status,job)
 assert call('/api/generate',sample)[0]==409
 deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  _,current=call('/api/jobs/'+job['id'])
  if current['status']=='rendering' and ((JOBS/job['id']/'encoding.mp4').exists() if encoding else current.get('progress',0)>=.85 if postprocess else current.get('progress',0)>0):break
  assert current['status'] not in ('failed','done'),current
  time.sleep(.1)
 else:raise AssertionError('No active GPU batch observed')
 start=time.monotonic();assert call('/api/cancel/'+job['id'],{})[0]==200
 while time.monotonic()-start<10:
  _,workbench=call('/api/workbench')
  disk=json.loads((JOBS/job['id']/'job.json').read_text(encoding='utf-8'))
  if not workbench['busy'] and disk['status']=='cancelled' and not (JOBS/job['id']/'request.json').exists():break
  time.sleep(.1)
 else:raise AssertionError('Backend did not release cancelled work')
 assert not (JOBS/job['id']/'result.mp4').exists()
 assert not (JOBS/job['id']/'encoding.mp4').exists()
 result={'invalid_input':400,'foreign_origin':403,'busy_guard':409,'cancelled_job':job['id'],'cancel_after_progress':current['progress'],'backend_cancel_s':round(time.monotonic()-start,3),'backend_request_removed':True,'no_completed_video':True}
 name='performance-api-check-v2-encoding.json' if encoding else 'performance-api-check-v2-postprocess.json' if postprocess else 'performance-api-check.json'
 (ROOT/'notes'/name).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
