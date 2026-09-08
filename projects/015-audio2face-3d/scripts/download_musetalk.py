"""Download the official inference weights only, at pinned HF revisions."""
import concurrent.futures
import hashlib
import json
import time
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'vendor/musetalk-models'
SOURCES=[
 ('TMElyralab/MuseTalk','3ef28bc5cff08c90ad8178a25f1b570cd800170f','musetalkV15/unet.pth','unet/unet.pth'),
 ('TMElyralab/MuseTalk','3ef28bc5cff08c90ad8178a25f1b570cd800170f','musetalkV15/musetalk.json','unet/config.json'),
 *[('stabilityai/sd-vae-ft-mse','31f26fdeee1355a5c34592e401dd41e45d25a493',x,'vae/'+x) for x in ['config.json','diffusion_pytorch_model.bin']],
 *[('openai/whisper-tiny','169d4a4341b33bc18d8881c4b69c2e104e1cc0af',x,'whisper/'+x) for x in ['config.json','preprocessor_config.json','pytorch_model.bin']],
]
def download(item):
 repo,revision,name,local=item;url=f'https://huggingface.co/{repo}/resolve/{revision}/{name}'
 path=DEST/local;path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():
  print('Downloading '+local,flush=True)
  with urllib.request.urlopen(url,timeout=120) as response,path.with_suffix(path.suffix+'.part').open('wb') as f:
   total=0;last=time.monotonic()
   while chunk:=response.read(4*1024*1024):
    f.write(chunk);total+=len(chunk)
    if time.monotonic()-last>20:print(local+' '+str(round(total/2**20))+' MB',flush=True);last=time.monotonic()
  path.with_suffix(path.suffix+'.part').replace(path)
 h=hashlib.sha256()
 with path.open('rb') as f:
  while chunk:=f.read(4*1024*1024):h.update(chunk)
 return {'file':local,'url':url,'bytes':path.stat().st_size,'sha256':h.hexdigest()}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(3) as pool:results=list(pool.map(download,SOURCES))
 (DEST/'manifest.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print('All MuseTalk weights ready',flush=True)
