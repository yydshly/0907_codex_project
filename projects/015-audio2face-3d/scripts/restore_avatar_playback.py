"""Explicitly restore the accepted UI/media at 8020; retain newer code/results."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 saved=ROOT/'.cache/releases/accepted-tail-v4'
 manifest=json.loads((saved/'baseline.json').read_text(encoding='utf-8'))
 for item in manifest['files']:
  source=saved/item['path']
  assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256'],item['path']
 # Limit restoration to the playback surface and media, not unrelated project code.
 for item in manifest['files']:
  path=Path(item['path'])
  if str(path).replace('\\','/').startswith('demo/complete.') or (path.parts[0]=='.cache' and path.suffix in ['.mp4','.png']):
   target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(saved/path,target)
 data=json.loads((saved/'playback.json').read_text(encoding='utf-8'));data['version']='accepted-tail-v4'
 target=ROOT/'.cache/complete/active-release.json';temp=target.with_suffix('.tmp')
 temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(target)
 print('Accepted UI and media restored. Refresh http://127.0.0.1:8020/. Newer code and results are retained.')
