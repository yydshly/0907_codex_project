"""Same-WAV acceptance across two identities using the public local API."""
import hashlib,json,time,urllib.request,urllib.error
from urllib.parse import quote
from performance_jobs import ROOT,JOBS,read,write

BASE='http://127.0.0.1:8022';SOURCE='e7a06c64995745aea2848f08a98a841f'
def api(path,data=None,raw=None):
 req=urllib.request.Request(BASE+path,data=raw if raw is not None else json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/octet-stream' if raw is not None else 'application/json'})
 with urllib.request.urlopen(req,timeout=40) as response:return json.load(response)
def wait_ready(key):
 end=time.monotonic()+1800
 while time.monotonic()<end:
  a=api('/api/avatars/'+key)
  if a['status']=='ready':return
  if a['status'] in ('failed','cancelled'):raise RuntimeError(a.get('message',a['status']))
  time.sleep(2)
 raise TimeoutError('Avatar preparation timed out')
def idle():
 end=time.monotonic()+300
 while time.monotonic()<end:
  if not api('/api/dialogue/status')['busy']:return
  time.sleep(.5)
 raise TimeoutError('Existing user task still busy')
def render(avatar,tag):
 record=ROOT/'.cache'/('body-compare-'+tag+'.json')
 if record.exists():job=read(record)
 else:
  idle();job=api('/api/generate',{'avatar_id':avatar,'state':'comfort','text':'你还好吗？今天辛苦了，慢慢来就好。','source_audio_job':SOURCE});write(record,job)
 end=time.monotonic()+180
 while time.monotonic()<end:
  data=api('/api/jobs/'+job['id'])
  if data['status']=='done':return data
  if data['status'] in ('failed','cancelled'):raise RuntimeError(data['message'])
  time.sleep(.5)
 raise TimeoutError('Comparison render timed out')
def case(name,avatar,old,new):
 sha=lambda key:hashlib.sha256((JOBS/key/'audio.wav').read_bytes()).hexdigest()
 assert sha(old['id'])==sha(new['id'])==sha(SOURCE)
 return {'name':name,'avatar_id':avatar,'before':old['video'],'after':new['video'],'old_job':old['id'],'new_job':new['id'],'audio_sha256':sha(SOURCE),'text':new['text'],'duration_s':new['metrics']['media_duration_s']}

def main():
 b=read(ROOT/'.cache/body-avatar-b.json')['id'];wait_ready(b);new_b=render(b,'b-new');old_b=read(JOBS/SOURCE/'job.json')
 cases=[case('若安',b,old_b,new_b)];write(ROOT/'demo/body-comparison.json',{'cases':cases});print('B same-audio comparison ready',flush=True)
 old_a=render('903a1d1dadb84a7fb3e3db832d3dab7e','a-old');record=ROOT/'.cache/body-avatar-a.json'
 if record.exists():a=read(record)
 else:
  idle();a=api('/api/avatars?name='+quote('小晴 · 自然半身')+'&motion_backend=minimax-body',raw=(ROOT/'.cache/companion/neutral.png').read_bytes());write(record,a)
 print('A preparation: '+a['id'],flush=True);wait_ready(a['id']);new_a=render(a['id'],'a-new');cases.append(case('小晴',a['id'],old_a,new_a))
 write(ROOT/'demo/body-comparison.json',{'cases':cases});print('PASS: two identities, identical source audio, old/new comparison videos',flush=True)

if __name__=='__main__':main()
