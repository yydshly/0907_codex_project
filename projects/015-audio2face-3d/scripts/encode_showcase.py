"""Encode captured browser frames and align the original audio to media clocks."""
import hashlib,json,subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/public-recording'

def main():
 data=json.loads((OUT/'capture.json').read_text(encoding='utf-8'))
 frames=data['frames'];origin=frames[0]['at'];duration=(frames[-1]['at']-origin)/1000+.08
 lines=['ffconcat version 1.0']
 for i,frame in enumerate(frames):
  lines.append("file 'frames/"+frame['file']+"'")
  delay=(frames[i+1]['at']-frame['at'])/1000 if i+1<len(frames) else .08
  lines.append(f'duration {delay:.6f}')
 lines.append("file 'frames/"+frames[-1]['file']+"'")
 (OUT/'frames.ffconcat').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 cmd=['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(OUT/'frames.ffconcat')]
 filters=[];events=[]
 for i,e in enumerate(data['events'],1):
  relative=urlparse(e['src']).path.removeprefix('/complete/')
  source=(ROOT/'.cache/complete'/relative).resolve()
  if not source.is_relative_to((ROOT/'.cache/complete').resolve()) or not source.is_file():raise ValueError('Invalid capture source')
  cmd+=['-i',str(source)]
  start=(e['at']-origin)/1000-e['mediaTime']
  if start<0:raise ValueError('Audio begins before the recording')
  filters.append(f'[{i}:a]adelay={round(start*1000)}:all=1[a{i}]')
  events.append({'source':relative,'start_s':round(start,4),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
 filters.append(''.join(f'[a{i}]' for i in range(1,len(events)+1))+f'amix=inputs={len(events)}:normalize=0,apad[a]')
 cmd+=['-filter_complex',';'.join(filters),'-map','0:v','-map','[a]','-t',str(duration),'-r','30','-fps_mode','cfr','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(OUT/'showcase-8020.mp4')]
 subprocess.run(cmd,check=True)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'poster.png'),'-frames:v','1','-q:v','3',str(OUT/'showcase-poster.jpg')],check=True)
 report={'source_page':'http://127.0.0.1:8020/','method':data['method'],'duration_s':round(duration,3),'captured_frames':len(frames),'capture_average_fps':round(len(frames)/duration,2),'output_fps':30,'resolution':'1440x1000','scenes':events,'note':'Real viewport recording; original clip audio aligned from observed media clocks, not a microphone/system-audio recording. Encoded frame rate does not imply 30 unique captured frames per second.'}
 (OUT/'recording-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':main()
