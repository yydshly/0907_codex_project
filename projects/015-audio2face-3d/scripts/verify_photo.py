"""Check a generated artifact: decodable moving frames, duration and original audio."""
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def main():
 jobs=[]
 for p in (ROOT/'.cache/photo-jobs').glob('*/job.json'):
  j=json.loads(p.read_text(encoding='utf-8'))
  if j['status']=='done' and j.get('sample'):jobs.append((p.stat().st_mtime,p,j))
 assert jobs,'No successfully generated sample video'
 _,path,job=max(jobs)
 video=path.parent/'result.mp4'
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
 streams=probe['streams'];v=next(s for s in streams if s['codec_type']=='video');a=next(s for s in streams if s['codec_type']=='audio')
 assert int(v['nb_frames'])>=200
 assert abs(float(probe['format']['duration'])-job['duration'])<.2
 cap=cv2.VideoCapture(str(video));frames=[]
 for second in [0,3.5,6.5]:
  cap.set(cv2.CAP_PROP_POS_MSEC,second*1000);ok,frame=cap.read();assert ok,'Cannot decode result frame';frames.append(frame)
 cap.release()
 difference=float(np.abs(frames[0].astype('f4')-frames[1]).mean())
 assert difference>.5,'Output appears static'
 def pcm(file):
  return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(file),'-vn','-ac','1','-ar','16000','-f','f32le','pipe:1']),dtype='<f4')
 original=pcm(path.parent/'audio.wav');decoded=pcm(video);length=min(len(original),len(decoded))
 correlation=float(np.corrcoef(original[:length],decoded[:length])[0,1]);assert correlation>.95,'Output audio differs from source'
 for i,frame in enumerate(frames):cv2.imwrite(str(ROOT/'.cache/photo-sample'/f'preview-{i}.png'),frame)
 report={'job_id':job['id'],'pipeline_seconds':job['seconds'],'input_audio_seconds':job['duration'],
  'output_seconds':float(probe['format']['duration']),'width':v['width'],'height':v['height'],'fps':v['avg_frame_rate'],
  'frames':int(v['nb_frames']),'video_codec':v['codec_name'],'audio_codec':a['codec_name'],
  'decoded_frame_difference':difference,'source_audio_correlation':correlation,
  'native_face_resolution':256,'enhancer':'GFPGAN v1.4','source_revision':'cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8',
  'note':'Frame differences and audio correlation check technical integrity, not perceptual lip-sync quality.'}
 (ROOT/'notes/photo-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
