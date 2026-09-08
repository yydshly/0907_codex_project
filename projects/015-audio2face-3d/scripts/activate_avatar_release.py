"""Build and atomically activate a verified local playback release."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/complete'
if __name__=='__main__':
 profile=json.loads((ROOT/'config/companion-timing.json').read_text())
 checks=json.loads((ROOT/'notes/timing-v5-verification.json').read_text())
 assert {c['id'] for c in checks['clips']}=={c['id'] for c in profile['clips']}
 clips=[];inputs=[]
 for spec in profile['clips']:
  folder=ROOT/spec['input'];dest=ROOT/spec['output'];render=json.loads((dest/'manifest.json').read_text())
  assert hashlib.sha256((dest/'result.mp4').read_bytes()).hexdigest()==render['output_sha256']
  scene=json.loads((folder/'scene.json').read_text(encoding='utf-8'))
  timeline=json.loads((dest/'timeline.json').read_text())
  item={k:scene[k] for k in ['id','name','text']}
  item.update(video=f'/complete/{spec["id"]}/{profile["version"]}/result.mp4',before_video=f'/complete/{spec["id"]}/tail-v4/result.mp4',
   idle_video=f'/complete/{spec["id"]}/{profile["version"]}/idle.mp4',source_video=f'/motion/{scene["motion"]}/result.mp4',
   fps=timeline['fps'],frames=timeline['frames'],seconds=render['postprocess_s'],media_duration_s=render['media_duration_s'])
  clips.append(item);inputs.append(dest/'result.mp4')
 target=OUT/f'showcase-{profile["version"]}.mp4';cmd=['ffmpeg','-v','error','-y']
 for path in inputs:cmd+=['-i',str(path)]
 filters=';'.join(f'[{i}:a]atrim=0:{clips[i]["media_duration_s"]},asetpts=PTS-STARTPTS[a{i}]' for i in range(len(inputs)))
 filters+=';'+''.join(f'[{i}:v][a{i}]' for i in range(len(inputs)))+f'concat=n={len(inputs)}:v=1:a=1[v][a]'
 subprocess.run(cmd+['-filter_complex',filters,'-map','[v]','-map','[a]','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(target)],check=True)
 release={'version':profile['version'],'clips':clips,'idle':'/motion/listen-v2/result.mp4','montage':f'/complete/{target.name}','baseline_url':'http://127.0.0.1:8021/'}
 temp=OUT/'active-release.tmp';temp.write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(OUT/'active-release.json')
 (OUT/f'release-{profile["version"]}.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Activated '+profile['version'])
