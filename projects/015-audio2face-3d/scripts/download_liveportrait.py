"""Fetch pinned official weights and validate their recorded SHA-256 hashes."""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 manifest=json.loads((ROOT/'config/liveportrait-models.json').read_text(encoding='utf-8'))
 dest=ROOT/'vendor/LivePortrait/pretrained_weights'
 for item in manifest['files']:
  path=dest/item['path'];path.parent.mkdir(parents=True,exist_ok=True)
  if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']:
   print(item['path']+' verified');continue
  url=f"https://huggingface.co/{manifest['repo']}/resolve/{manifest['revision']}/{item['path']}"
  temp=path.with_suffix('.download')
  with urllib.request.urlopen(url,timeout=120) as response,temp.open('wb') as stream:
   while block:=response.read(4*1024*1024):stream.write(block)
  if hashlib.sha256(temp.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Model checksum mismatch: '+item['path'])
  temp.replace(path);print(item['path']+' downloaded and verified')
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if __name__=='__main__':main()
