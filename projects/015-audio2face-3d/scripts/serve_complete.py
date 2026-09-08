"""Read-only player for actual speech + lip sync + full motion results."""
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,unquote
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/complete'
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  if urlparse(self.path).path=='/api/complete':
   active=OUT/'active-release.json'
   if active.exists():
    raw=active.read_bytes();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
   clips=[]
   for name in ['welcome','playful','soft']:
    path=OUT/name/'result.json'
    if path.exists():
     item=json.loads(path.read_text(encoding='utf-8'))
     clip={k:item[k] for k in ['id','name','text','video','source_video','fps','frames','seconds']}
     clip['before_video']=item.get('before_video',item['video'])
     clip['idle_video']=item.get('idle_video','/motion/listen-v2/result.mp4')
     clips.append(clip)
   montage=next((name for name in ['showcase-tail-v4.mp4','showcase-mask-v3.mp4','showcase-stable-v2.mp4','showcase.mp4'] if (OUT/name).exists()),None)
   data={'clips':clips,'idle':'/motion/listen-v2/result.mp4','montage':f'/complete/{montage}' if montage else None}
   raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
  return super().do_GET()
 def translate_path(self,path):
  clean=unquote(urlparse(path).path)
  if clean=='/':return str(ROOT/'demo/complete.html')
  if clean=='/source.png':return str(ROOT/'.cache/companion/neutral.png')
  for prefix,root in [('/complete/',OUT),('/motion/',ROOT/'.cache/motion')]:
   if clean.startswith(prefix):
    dest=(root/clean[len(prefix):]).resolve()
    if not dest.is_relative_to(root.resolve()) or dest.suffix not in ('.mp4','.png','.jpg','.wav','.mp3'):return str(root/'invalid')
    return str(dest)
  return super().translate_path(path)
if __name__=='__main__':
 print('Complete companion: http://127.0.0.1:8020/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8020),partial(Handler,directory=str(ROOT/'demo'))).serve_forever()
