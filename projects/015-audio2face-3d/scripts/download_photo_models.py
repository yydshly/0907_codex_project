"""Download upstream release weights for the independent photo talking-head demo."""
import concurrent.futures
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'vendor/photo-models'
FILES={
 'SadTalker_V0.0.2_256.safetensors':'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors',
 'mapping_00109-model.pth.tar':'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar',
 'mapping_00229-model.pth.tar':'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar',
 'alignment_WFLW_4HG.pth':'https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth',
 'detection_Resnet50_Final.pth':'https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth',
 'GFPGANv1.4.pth':'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth',
 'parsing_parsenet.pth':'https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth',
}
def download(item):
 name,url=item;path=OUT/name
 if not path.exists():
  print('Downloading '+name,flush=True)
  with urllib.request.urlopen(url,timeout=180) as response,path.with_suffix(path.suffix+'.part').open('wb') as output:
   while chunk:=response.read(1024*1024):output.write(chunk)
  path.with_suffix(path.suffix+'.part').replace(path)
  print('Saved '+name,flush=True)
 return {'file':name,'url':url,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(download,FILES.items()))
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2))
