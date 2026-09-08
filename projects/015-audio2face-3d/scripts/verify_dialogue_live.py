"""Real MiniMax conversation, speech, GPU video and cancelled-generation acceptance."""
import json,time,urllib.request
from performance_jobs import ROOT,JOBS,write
BASE='http://127.0.0.1:8022'
def call(path,data=None):
 request=urllib.request.Request(BASE+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(request,timeout=10) as r:return json.load(r)
def idle():
 deadline=time.monotonic()+75
 while call('/api/dialogue/status')['busy']:
  if time.monotonic()>deadline:raise TimeoutError('Service stayed busy')
  time.sleep(.3)
def turn(session,text,event=None):
 idle();job=call('/api/dialogue/turn',{'session':session,'text':text,'event':event});deadline=time.monotonic()+120;stages=[]
 while time.monotonic()<deadline:
  result=call('/api/jobs/'+job['id'])
  if result['status'] not in stages:stages.append(result['status'])
  if result['status'] in ['done','failed','cancelled']:break
  time.sleep(.3)
 assert result['status']=='done',result
 assert result['provider']=='MiniMax' and result['voice']['provider']=='MiniMax'
 assert (JOBS/job['id']/'result.mp4').is_file()
 item={'job':result['id'],'input':text,'reply':result['text'],'intent':result['state'],'voice':result['voice'],'chat_s':result['chat_s'],'metrics':result['metrics'],'observed_stages':stages}
 print(json.dumps(item,ensure_ascii=True),flush=True);return item
def main():
 session=call('/api/dialogue/session',{})['id'];print('session='+session,flush=True)
 first=turn(session,'我今天修了一整天网页，很累。')
 second=turn(session,'你还记得我今天在做什么吗？')
 assert '网页' in second['reply'],second
 assert '没有' not in second['reply'] or '记忆' not in second['reply'],second
 third=turn(session,'我刚完成了一个任务，想听你鼓励一下。','task_done')
 assert third['intent'] in ['affirm','playful'],third
 assert len(call('/api/dialogue/session/'+session)['messages'])==6
 # Separate cancellation session keeps the user-facing example clean.
 idle();cancel_session=call('/api/dialogue/session',{})['id'];job=call('/api/dialogue/turn',{'session':cancel_session,'text':'陪我聊两句吧。'})
 start=time.monotonic();call('/api/cancel/'+job['id'],{});idle()
 state=json.loads((JOBS/job['id']/'job.json').read_text(encoding='utf-8'))
 assert state['status']=='cancelled' and not (JOBS/job['id']/'request.json').exists() and not (JOBS/job['id']/'speech.mp3').exists() and not (JOBS/job['id']/'result.mp4').exists()
 report={'session':session,'turns':[first,second,third],'context_verified':True,'task_event_verified':True,'cancel':{'job':job['id'],'backend_release_s':round(time.monotonic()-start,3),'no_speech_or_video':True}}
 write(ROOT/'notes/minimax-dialogue-live.json',report);print('PASS: real dialogue, context, task event and cancellation',flush=True)
if __name__=='__main__':main()
