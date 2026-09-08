"""Same two previously generated audio segments; no new TTS latency claims."""
import json,time,uuid,shutil
import numpy as np
from musetalk_complete import read_video
from performance_jobs import ROOT,JOBS,write
from verify_dialogue_live import call,idle

def main():
 idle();keys=['ec6bfbcc5edc445da2f2157103b21781','413a95e3e20943c780f9945f5eb44d8b'];rows=[];start=time.time()
 for key in keys:
  old=JOBS/key;original=json.loads((old/'job.json').read_text(encoding='utf-8'));folder=JOBS/uuid.uuid4().hex;folder.mkdir()
  for name in ['audio.wav','speech.mp3']:shutil.copy2(old/name,folder/name)
  job={'id':folder.name,'state':original['state'],'text':original['text'],'frame_offset':original.get('frame_offset',0),'submitted_at':start,'audit':True,'benchmark_replay_of':key,'status':'queued','tts_s':0}
  write(folder/'job.json',job);write(folder/'request.json',job);rows.append({'old':original,'folder':folder,'new':job})
 deadline=time.monotonic()+90
 while time.monotonic()<deadline:
  for row in rows:row['new']=json.loads((row['folder']/'job.json').read_text(encoding='utf-8'))
  if all(row['new']['status']=='done' and not (row['folder']/'request.json').exists() for row in rows):break
  assert not any(row['new']['status'] in ('failed','cancelled') for row in rows),rows
  time.sleep(.1)
 assert all(row['new']['status']=='done' for row in rows)
 for row in rows:
  a=read_video(JOBS/row['old']['id']/'result.mp4');b=read_video(row['folder']/'result.mp4');assert len(a)==len(b)
  mse=float(np.mean([np.mean((x.astype(float)-y.astype(float))**2) for x,y in zip(a,b)]))
  row['decoded_video_mse']=mse;assert mse==0,('Quality regression',mse)
  row.pop('folder');print(json.dumps({'old':row['old']['id'],'new':row['new']['id'],'mse':mse,'metrics':row['new']['metrics']}),flush=True)
 first,second=[row['new']['metrics'] for row in rows]
 overlap=max(0,min(first['post_finished_at'],second['gpu_finished_at'])-max(first['post_started_at'],second['gpu_started_at']))
 assert overlap>0,'CPU and GPU did not overlap'
 # Available-time estimate, separate from actual browser playback gap.
 gap=max(0,second['total_s']-first['total_s']-first['media_duration_s'])
 report={'source':'same existing WAVs, no LLM or TTS included','rows':rows,'cpu_gpu_overlap_s':round(overlap,3),'estimated_gap_s':round(gap,3)}
 write(ROOT/'notes/avatar-overlap-benchmark.json',report);print('PASS '+json.dumps({'overlap_s':overlap,'estimated_gap_s':gap}),flush=True)

if __name__=='__main__':main()
