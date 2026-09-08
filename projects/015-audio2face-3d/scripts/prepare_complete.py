"""Create short Taiwanese Mandarin lines sized to existing motion footage."""
import json
import subprocess
from pathlib import Path
from companion_media import synthesize
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/complete'
SCENES={
 'welcome':{'name':'欢迎回来','motion':'listen-v2','style':'neutral','text':'你來啦，今天還好嗎？'},
 'playful':{'name':'调皮提醒','motion':'playful','style':'playful','text':'被我發現了吧，你又熬夜喔！'},
 'soft':{'name':'轻松回应','motion':'annoyed','style':'playful','text':'好啦，逗你的，別緊張嘛。'},
}
if __name__=='__main__':
 for name,scene in SCENES.items():
  folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
  speech=folder/'speech.mp3'
  voice=synthesize(scene['text'],scene['style'],speech)
  duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(speech)]))
  # Preserve the full utterance; speed up only if it would exceed the source video.
  speed=max(1.,duration/3.85)
  filt=f'atempo={speed:.6f},apad=whole_dur=4.033334'
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(speech),'-af',filt,'-t','4.033334','-ar','16000','-ac','1',str(folder/'audio.wav')],check=True)
  item={**scene,'id':name,'voice':voice,'tts_seconds':duration,'audio_speed_adjustment':speed,'motion_source':str(ROOT/'.cache/motion'/scene['motion']/'result.mp4')}
  (folder/'scene.json').write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
  print(name+' speech ready: '+str(duration)+' s',flush=True)
