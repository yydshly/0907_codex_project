"""Build the public read-only showcase with an explicit page/media allowlist.

Requires prepared Mark samples and a locally recorded 8020 demonstration.
No generation requests, credentials, user uploads or Camila assets are published.
"""
from pathlib import Path
import hashlib,json,re,shutil

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT.parents[1]/'docs/demos/015-audio2face-3d'
REPO='https://github.com/yydshly/0907_codex_project/blob/main/projects/015-audio2face-3d/'

def copy(source,relative):
 dest=TARGET/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)

def main():
 TARGET.mkdir(parents=True,exist_ok=True)
 copy(ROOT/'demo/public-index.html','index.html')
 for name in ['effects.css','style.css','app.js','THIRD_PARTY_NOTICES.md']:
  copy(ROOT/'demo'/name,name)
 for source in (ROOT/'demo/licenses').glob('*.txt'):copy(source,'licenses/'+source.name)
 mark=(ROOT/'demo/mark.html').read_text(encoding='utf-8')
 mark=re.sub(r'<nav>.*?</nav>','<nav><a href="./">效果总览</a><a href="implementation-guide.html">从零实施</a><a href="#lab">三维效果</a></nav>',mark,count=1,flags=re.S)
 mark=mark.replace('本地能力展示','预生成样例回放').replace('本机真实推理','本地推理后导出')
 (TARGET/'mark.html').write_text(mark,encoding='utf-8',newline='\n')
 for source in (ROOT/'demo/assets').iterdir():
  if source.is_file() and source.suffix in {'.bin','.wav','.json','.js'}:copy(source,'assets/'+source.name)
 guide=(ROOT/'demo/implementation-guide.html').read_text(encoding='utf-8')
 guide=re.sub(r'http://127\.0\.0\.1:\d+[^"\s<]*',REPO+'README.md',guide)
 guide=guide.replace('effects.html?view=3d#showcase','mark.html#lab').replace('effects.html','index.html')
 guide=guide.replace('进入人物准备 ↗','阅读本地人物准备说明 ↗').replace('进入三维人物体验 ↗','阅读本地三维启动说明 ↗').replace('同音频前后对照 ↗','阅读项目效果记录 ↗')
 (TARGET/'implementation-guide.html').write_text(guide,encoding='utf-8',newline='\n')
 media={
  'showcase-8020.mp4':ROOT/'.cache/public-recording/showcase-8020.mp4',
  'showcase-poster.jpg':ROOT/'.cache/public-recording/showcase-poster.jpg',
  'performance-clips.mp4':ROOT/'.cache/complete/showcase-timing-v5.mp4',
  'portrait.jpg':ROOT/'.cache/public-recording/portrait.jpg',
  'mark-preview.png':ROOT/'assets/showcase.png',
  'recording-report.json':ROOT/'.cache/public-recording/recording-report.json',
 }
 for name,source in media.items():copy(source,'media/'+name)
 from build_public_sections import build
 build(ROOT,TARGET,copy,REPO)
 (TARGET/'.gitattributes').write_text('* text=auto eol=lf\n*.bin binary\n*.wav binary\n*.mp4 binary\n*.png binary\n*.jpg binary\n',encoding='utf-8',newline='\n')
 manifest=[]
 for p in sorted(TARGET.rglob('*')):
  if not p.is_file() or p.name=='publication-manifest.json':continue
  if p.suffix in {'.html','.js','.css','.json','.md','.txt'}:
   # Match Git text normalization so the published hashes remain reproducible.
   p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8',newline='\n')
  if p.suffix in {'.html','.js','.css'}:
   text=p.read_text(encoding='utf-8')
   if 'http://127.0.0.1:' in text or 'http://localhost:' in text:raise ValueError('Local URL in public content: '+str(p))
  if any(x in p.parts for x in ['Camila','vendor','.env','avatars-media']):raise ValueError('Private asset path')
  manifest.append({'path':p.relative_to(TARGET).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (TARGET/'publication-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
 print(f'Prepared {len(manifest)} public files ({sum(x["bytes"] for x in manifest)/1024**2:.1f} MiB). No deployment performed.')

if __name__=='__main__':main()
