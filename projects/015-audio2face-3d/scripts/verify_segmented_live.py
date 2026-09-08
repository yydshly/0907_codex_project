"""Real provider/GPU acceptance. Uses isolated sessions; never injects fake replies."""
import json,time
from verify_dialogue_live import call,idle
from performance_jobs import ROOT,JOBS,write

def wait(job,predicate,timeout=120):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  item=call('/api/jobs/'+job['id'])
  if predicate(item):return item
  if item['status'] in ('failed','cancelled'):raise AssertionError(item)
  time.sleep(.1)
 raise TimeoutError(job['id'])

def submit(session,text):
 return call('/api/dialogue/turn',{'session':session,'text':text,'mode':'segmented'})

def cancel(job):
 start=time.monotonic();call('/api/cancel/'+job['id'],{});idle();elapsed=round(time.monotonic()-start,3)
 item=call('/api/jobs/'+job['id']);assert item['status']=='cancelled'
 assert not any((JOBS/key/'request.json').exists() for key in item.get('children',[]))
 return {'job':job['id'],'release_s':elapsed}

def main(report_name='dialogue-segments-live.json',overlap_cancel=False):
 idle();session=call('/api/dialogue/session',{})['id'];job=submit(session,'陪我聊两句吧。');time.sleep(.3)
 llm_cancel=cancel(job);print('LLM cancel '+json.dumps(llm_cancel),flush=True)
 # The new request is accepted while the old HTTP operation may still be in flight.
 job=submit(session,'我刚修好了网页，想听你说两句鼓励的话。')
 complete=wait(job,lambda x:x['status']=='done');idle()
 parts=complete['segments'];assert ''.join(p['text'] for p in parts)==complete['text']
 phase=0
 for p in parts:
  assert p['frame_offset']==phase and p['voice']['provider']=='MiniMax'
  assert (JOBS/p['id']/'result.mp4').is_file()
  phase+=round(p['metrics']['media_duration_s']*25)
 print('Completed '+complete['id'],flush=True)
 job=submit(session,'我有点累，先安慰我一句，再建议我怎么休息。')
 def cancel_stage(item):
  if not overlap_cancel:return item['status']=='rendering'
  children=[call('/api/jobs/'+key) for key in item.get('children',[])]
  if len(children)==2 and children[0].get('progress',0)>=.85 and children[1]['status']=='rendering':return True
  if item['status']=='done':raise AssertionError('No overlapping cancellation window observed')
  return False
 wait(job,cancel_stage);gpu_cancel=cancel(job);gpu_cancel['overlap_requested']=overlap_cancel;print('GPU cancel '+json.dumps(gpu_cancel),flush=True)
 # Wait past the detached first response; it must not start a stale speech/video job.
 old=JOBS/llm_cancel['job'];assert not (old/'speech.mp3').exists() and not (old/'result.mp4').exists()
 report={'session':session,'completed_turn':complete,'llm_cancel':llm_cancel,'gpu_cancel':gpu_cancel,'new_turn_after_cancel':True}
 write(ROOT/'notes'/report_name,report);print('PASS: real segmented reply, phase offsets, cancel and immediate next submission',flush=True)

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--report',default='dialogue-segments-live.json');parser.add_argument('--overlap-cancel',action='store_true');args=parser.parse_args();main(args.report,args.overlap_cancel)
