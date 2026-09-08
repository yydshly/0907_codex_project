"""Serve the verified immutable playback snapshot on its own port."""
import argparse,hashlib,importlib.util,json
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8021);a=p.parse_args()
 baseline=ROOT/'.cache/releases/accepted-tail-v4'
 record=json.loads((baseline/'baseline.json').read_text(encoding='utf-8'))
 for item in record['files']:
  assert hashlib.sha256((baseline/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
 spec=importlib.util.spec_from_file_location('saved_complete',baseline/'scripts/serve_complete.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 print(f'Accepted baseline: http://127.0.0.1:{a.port}/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',a.port),partial(module.Handler,directory=str(baseline/'demo'))).serve_forever()
