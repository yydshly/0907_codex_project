"""Join observed browser timings with real jobs; retain failed attempts in the denominator."""
import statistics
from performance_jobs import ROOT,JOBS,read,write

def main():
 observed=read(ROOT/'notes/first-response-browser-measurements.json');rows=[]
 for i,measurement in enumerate(observed['rounds']):
  job=read(JOBS/measurement['job']/'job.json');assert job['chat_model']=='MiniMax-M3'
  rows.append({'round':i+1,**measurement,'input':job['user_text'],'reply':job['text'],'intent':job['state'],'status':job['status'],
   'chat_s':job['chat_s'],'chat_usage':job['chat_usage'],'segments':job.get('segments',[]),'metrics':job.get('metrics')})
 success=[r for r in rows if r['complete']];first=[r['first_play_s'] for r in success];gaps=[g for r in success for g in r['gaps_s']]
 checks={'webpage_recall':'网页' in rows[1]['reply'],'login_page_recall':'登录' in rows[5]['reply'],'test_notes_recall':'测试' in rows[8]['reply']}
 assert all(checks.values()),checks
 retry=read(JOBS/observed['post_fix_retry']['job']/'job.json');assert retry['status']=='done'
 summary={'attempted':len(rows),'completed':len(success),'failed':len(rows)-len(success),
  'first_play_median_s':round(statistics.median(first),3),'first_play_min_s':round(min(first),3),'first_play_max_s':round(max(first),3),
  'gap_median_s':round(statistics.median(gaps),3),'gap_max_s':round(max(gaps),3),'chat_median_s':round(statistics.median(r['chat_s'] for r in rows),3),
  'chat_max_s':round(max(r['chat_s'] for r in rows),3),'format_retries':sum(r['chat_usage']['format_retries'] for r in rows)}
 report={'session':observed['session'],'source':observed['source'],'model':'MiniMax-M3','thinking':'disabled','speech_model':'speech-2.8-hd',
  'summary':summary,'context_checks':checks,'rounds':rows,'post_fix_retry':{**observed['post_fix_retry'],'reply':retry['text'],'metrics':retry['metrics']},
  'limitations':['Nine successful rounds contribute latency statistics; the failed round is not silently dropped from success rate.',
   'A metadata-read contention repair was applied between rounds eight and nine. The extra retry is reported separately.',
   'Previous version has only sparse, different-text browser samples; this is not a matched ten-round A/B benchmark.']}
 write(ROOT/'notes/first-response-ten-rounds.json',report);print(summary);print(checks)

if __name__=='__main__':main()
