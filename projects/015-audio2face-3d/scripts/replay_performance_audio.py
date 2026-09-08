"""Local benchmark only: reuse an existing WAV; do not count this as new TTS latency."""
import json,shutil,time,uuid,sys
from performance_jobs import JOBS,write
def main(key):
 old=JOBS/key;source=json.loads((old/'job.json').read_text(encoding='utf-8'));folder=JOBS/uuid.uuid4().hex;folder.mkdir()
 for name in ['audio.wav','speech.mp3']:shutil.copy2(old/name,folder/name)
 data={'id':folder.name,'text':source['text'],'state':source['state'],'submitted_at':time.time(),'audit':True,'benchmark_replay_of':key}
 write(folder/'job.json',{**data,'status':'queued','message':'同音频性能对照','tts_s':0,'audio':f'/jobs/{folder.name}/speech.mp3'})
 write(folder/'request.json',data);print(folder.name,flush=True)
 deadline=time.monotonic()+90
 while time.monotonic()<deadline:
  job=json.loads((folder/'job.json').read_text(encoding='utf-8'))
  if job['status'] in ['done','failed','cancelled']:
   print(json.dumps(job,ensure_ascii=True),flush=True)
   if job['status']!='done':raise RuntimeError('Replay failed')
   return
  time.sleep(.3)
 raise TimeoutError('Worker did not finish')
if __name__=='__main__':main(sys.argv[1])
