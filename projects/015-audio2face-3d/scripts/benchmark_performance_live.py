"""Three fresh TTS requests on a warm worker; compare to recorded v1 samples."""
import json,time,urllib.request
from performance_jobs import ROOT,JOBS,write
BASE='http://127.0.0.1:8022'
BASELINES=['9ec4adc81859416c9f97cbcb87fd7033','6aa4859971084806ae41adeaf6cbb883','db79806c038546abafd46cb91924a724']
def get(path):
 with urllib.request.urlopen(BASE+path,timeout=10) as r:return json.load(r)
def main():
 deadline=time.monotonic()+45
 while time.monotonic()<deadline:
  worker=get('/api/workbench')['worker']
  if worker.get('pipeline_version')=='performance-v2' and worker['status']=='ready':break
  time.sleep(.3)
 else:raise TimeoutError('Optimized worker not ready')
 rows=[]
 for key in BASELINES:
  old=json.loads((JOBS/key/'job.json').read_text(encoding='utf-8'))
  while get('/api/workbench')['busy']:time.sleep(.3)
  req=urllib.request.Request(BASE+'/api/generate',data=json.dumps({'text':old['text'],'state':old['state']}).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=10) as r:job=json.load(r)
  deadline=time.monotonic()+90
  while time.monotonic()<deadline:
   result=get('/api/jobs/'+job['id'])
   if result['status'] in ['done','failed','cancelled']:break
   time.sleep(.3)
  assert result['status']=='done',result
  row={'state':old['state'],'text':old['text'],'baseline_job':key,'new_job':job['id'],'baseline_metrics':old['metrics'],'new_metrics':result['metrics'],'total_wait_reduction_percent':round((1-result['metrics']['total_s']/old['metrics']['total_s'])*100,1)}
  rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 write(ROOT/'notes/performance-v2-live-benchmark.json',{'warm_worker':worker,'fresh_tts':True,'samples':rows})
if __name__=='__main__':main()
