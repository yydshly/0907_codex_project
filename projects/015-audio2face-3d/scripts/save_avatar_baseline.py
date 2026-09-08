"""Save a self-contained playback baseline plus code/provenance, never secrets."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NAME='accepted-tail-v4'
DEST=ROOT/'.cache/releases'/NAME

def save():
 if DEST.exists():raise FileExistsError(f'Baseline already exists: {DEST}')
 DEST.mkdir(parents=True)
 paths=set()
 for directory,patterns in [('scripts',['*.py','*.txt']),('demo',['complete.*']),('notes',['*.md','*.json'])]:
  for pattern in patterns:paths.update((ROOT/directory).glob(pattern))
 paths.update([ROOT/'README.md',ROOT/'start-complete.ps1',ROOT/'vendor/musetalk-models/manifest.json',ROOT/'.cache/companion/neutral.png'])
 clips=[]
 for name in ['welcome','playful','soft']:
  folder=ROOT/'.cache/complete'/name
  item=json.loads((folder/'result.json').read_text(encoding='utf-8'))
  clips.append({k:item[k] for k in ['id','name','text','video','source_video','fps','frames','seconds','before_video','idle_video']})
  paths.update(folder.glob('*.json'));paths.update([folder/'audio.wav',folder/'speech.mp3',folder/'boxes.npy',folder/'audio_features.pt'])
  for version in ['mask-v3','tail-v4']:
   paths.update((folder/version).glob('*.mp4'));paths.update((folder/version).glob('*.json'))
  paths.add(Path(item['motion_source']))
 paths.add(ROOT/'.cache/complete/showcase-tail-v4.mp4')
 files=[]
 for path in sorted(paths):
  if not path.is_file():continue
  relative=path.relative_to(ROOT);target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(path,target)
  files.append({'path':relative.as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 api={'clips':clips,'idle':'/motion/listen-v2/result.mp4','montage':'/complete/showcase-tail-v4.mp4'}
 (DEST/'playback.json').write_text(json.dumps(api,ensure_ascii=False,indent=2),encoding='utf-8')
 manifest={'name':NAME,'status':'user-accepted baseline before further optimization','files':files,
  'scope':'Self-contained cached playback, audio/motion inputs, scripts, model provenance and reports. Model weights and Python runtime remain external prerequisites for regeneration.'}
 (DEST/'baseline.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 archive=DEST.with_suffix('.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for path in DEST.rglob('*'):
   if path.is_file():z.write(path,path.relative_to(DEST))
 # Verify the actual archive, not just the source folder.
 with zipfile.ZipFile(archive) as z:
  for item in files:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
 print(json.dumps({'baseline':str(DEST),'archive':str(archive),'files':len(files),'archive_bytes':archive.stat().st_size}))

if __name__=='__main__':save()
