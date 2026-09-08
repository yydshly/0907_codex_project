"""Reproducible Windows setup for the local photo talking-head experiment."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENV=ROOT/'.cache/sadtalker-venv'
PYTHON=ENV/'Scripts/python.exe'
REPO=ROOT/'vendor/SadTalker'
REVISION='cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8'

def run(args,cwd=ROOT):subprocess.run([str(a) for a in args],cwd=cwd,check=True)

if __name__=='__main__':
 if not (REPO/'inference.py').exists():
  run(['git','clone','https://github.com/OpenTalker/SadTalker.git',REPO])
  run(['git','checkout',REVISION],REPO)
 if not PYTHON.exists():run([sys.executable,'-m','venv',ENV])
 run([PYTHON,'-m','pip','install','--upgrade','pip'])
 run([PYTHON,'-m','pip','install','torch==2.1.2+cu121','torchvision==0.16.2+cu121','torchaudio==2.1.2+cu121','--extra-index-url','https://download.pytorch.org/whl/cu121'])
 run([PYTHON,'-m','pip','install','setuptools==69.5.1','wheel'])
 run([PYTHON,'-m','pip','install','-r',ROOT/'scripts/photo-requirements.txt','--no-build-isolation'])
 run([sys.executable,ROOT/'scripts/download_photo_models.py'])
 weights=REPO/'gfpgan/weights';weights.mkdir(parents=True,exist_ok=True)
 for name in ['alignment_WFLW_4HG.pth','detection_Resnet50_Final.pth','GFPGANv1.4.pth','parsing_parsenet.pth']:
  dest=weights/name;src=ROOT/'vendor/photo-models'/name
  if not dest.exists():
   try:os.link(src,dest)
   except OSError:shutil.copyfile(src,dest)
 sample=ROOT/'.cache/photo-sample';sample.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(REPO/'examples/source_image/people_0.png',sample/'portrait.png')
 shutil.copyfile(ROOT/'demo/assets/hello-neutral.wav',sample/'audio.wav')
 run([PYTHON,REPO/'inference.py','--help'],REPO)
 run([PYTHON,'-c','import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))'])
 (ROOT/'.cache/photo-runtime-ready.json').write_text(json.dumps({'source':REVISION,'torch':'2.1.2+cu121','size':256,'batch_size':1}))
 print('Ready. Run: python scripts/serve_photo.py')
