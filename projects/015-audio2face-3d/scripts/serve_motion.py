"""Read-only original-photo / actual generated-motion comparison, port 8019."""
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,unquote
ROOT=Path(__file__).resolve().parents[1]
MEDIA=ROOT/'.cache/motion'
LABELS={'listen':('倾听','侧头、点头与上半身轻微移动'),'playful':('调皮','微笑、侧头与肩膀动作'),'annoyed':('佯怒','皱眉、转头与表情恢复')}
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  if urlparse(self.path).path=='/api/motion':
   clips=[]
   selection_path=MEDIA/'selection.json'
   selection=json.loads(selection_path.read_text(encoding='utf-8')) if selection_path.exists() else {}
   for key,(name,description) in LABELS.items():
    chosen=selection.get(key,{})
    variant=chosen.get('variant',key)
    info=MEDIA/variant/'generation.json'
    if not info.exists():continue
    data=json.loads(info.read_text(encoding='utf-8'))
    if data['status']!='done':continue
    clips.append({'id':key,'name':name,'description':description,'video':f'/motion/{variant}/result.mp4',
      'prompt':data['prompt'],'seconds':data['elapsed_seconds'],'seed':data['seed'],
      'assessment':chosen.get('assessment','待评估'),'verdict':chosen.get('verdict','待评估'),
      'previous':f'/motion/{key}/result.mp4' if variant!=key else None})
   raw=json.dumps({'clips':clips,'source':'/source.png','provider':'LTX-Video 13B 0.9.8 distilled','remote':True},ensure_ascii=False).encode()
   self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
  return super().do_GET()
 def translate_path(self,path):
  clean=unquote(urlparse(path).path)
  if clean=='/':return str(ROOT/'demo/motion.html')
  if clean=='/source.png':return str(ROOT/'.cache/companion/neutral.png')
  if clean.startswith('/motion/'):
   dest=(MEDIA/clean[len('/motion/'):]).resolve()
   if not dest.is_relative_to(MEDIA.resolve()) or dest.suffix not in ('.mp4','.png','.jpg'):return str(MEDIA/'invalid')
   return str(dest)
  return super().translate_path(path)
if __name__=='__main__':
 print('Motion comparison: http://127.0.0.1:8019/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8019),partial(Handler,directory=str(ROOT/'demo'))).serve_forever()
