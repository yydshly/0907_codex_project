"""Speech and offline half-body animation for the local companion prototype."""
import asyncio
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / '.cache/companion'
RUNTIME = ROOT / '.cache/sadtalker-venv/Scripts/python.exe'
REPO = ROOT / 'vendor/SadTalker'
STATES = {
 'neutral': {'name':'温柔欢迎','text':'你來啦，今天過得怎麼樣？坐一下，慢慢跟我說。','rate':'-5%','pitch':'+0Hz','emotion':'calm','pose':0},
 'playful': {'name':'调皮一下','text':'你是不是又偷偷熬夜了？被我抓到了吧。好啦，下次早一點睡嘛。','rate':'+6%','pitch':'+3Hz','emotion':'happy','pose':3},
 'angry': {'name':'假装生气','text':'哼，你剛剛是不是故意逗我？我才沒有生氣呢。好啦，算你會說話。','rate':'+2%','pitch':'-2Hz','emotion':'angry','pose':5},
 'comfort': {'name':'安慰陪伴','text':'今天真的辛苦了。不用急著打起精神，先休息一下，我聽你說。','rate':'-10%','pitch':'-2Hz','emotion':'calm','pose':1},
}

def settings():
 config = {}
 path = ROOT / '.env.companion'
 if path.exists():
  for line in path.read_text(encoding='utf-8-sig').splitlines():
   if '=' in line and not line.lstrip().startswith('#'):
    key,value = line.split('=',1); config[key.strip()] = value.strip().strip('\"\'')
 return {**config, **os.environ}

def synthesize(text, state, target, provider='edge'):
 config = settings(); style = STATES[state]
 if provider == 'minimax':
  key = config.get('MINIMAX_API_KEY'); voice = config.get('MINIMAX_VOICE_ID')
  if not key or not voice: raise ValueError('请在本机 .env.companion 配置 MINIMAX_API_KEY 和 MINIMAX_VOICE_ID')
  endpoint = config.get('MINIMAX_TTS_URL','https://api.minimax.io/v1/t2a_v2')
  payload = {'model':config.get('MINIMAX_SPEECH_MODEL','speech-2.8-hd'),'text':text,'stream':False,'output_format':'hex',
   'voice_setting':{'voice_id':voice,'speed':1,'vol':1,'pitch':0,'emotion':style['emotion']},
   'audio_setting':{'sample_rate':32000,'bitrate':128000,'format':'mp3','channel':1}}
  request = urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
  with urllib.request.urlopen(request,timeout=90) as response: result = json.load(response)
  if result.get('base_resp',{}).get('status_code') != 0: raise RuntimeError('MiniMax 语音合成失败，请检查账户、音色和模型配置')
  target.write_bytes(bytes.fromhex(result['data']['audio']))
  return {'provider':'MiniMax','voice':voice,'emotion_control':True}
 import edge_tts
 async def run():
  await asyncio.wait_for(edge_tts.Communicate(text,'zh-TW-HsiaoChenNeural',rate=style['rate'],pitch=style['pitch']).save(str(target)),timeout=90)
 asyncio.run(run())
 return {'provider':'Edge TTS','voice':'zh-TW-HsiaoChenNeural','emotion_control':False,'rate':style['rate'],'pitch':style['pitch']}

def render(image, audio, folder, state, progress=lambda text:None):
 from PIL import Image
 folder.mkdir(parents=True,exist_ok=True)
 portrait = folder/'portrait.png'
 with Image.open(image) as picture:
  picture = picture.convert('RGB'); picture.thumbnail((512,768)); picture.save(portrait)
 wav = folder/'audio.wav'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(audio),'-ar','16000','-ac','1',str(wav)],check=True,timeout=30)
 import wave
 with wave.open(str(wav)) as source: duration = source.getnframes()/source.getframerate()
 if duration > 25: raise ValueError('当前原型支持 25 秒以内的语音，请缩短台词')
 progress('正在生成半身人物口型和轻微头部动作…')
 command = [str(RUNTIME),str(REPO/'inference.py'),'--source_image',str(portrait),'--driven_audio',str(wav),
  '--checkpoint_dir',str(ROOT/'vendor/photo-models'),'--result_dir',str(folder/'render'),'--size','256','--batch_size','1',
  '--preprocess','full','--still','--enhancer','gfpgan','--pose_style',str(STATES[state]['pose'])]
 start = time.monotonic()
 with (folder/'render.log').open('w',encoding='utf-8') as log:
  process = subprocess.run(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,timeout=1800,
    env={**os.environ,'PYTHONIOENCODING':'utf-8','OMP_NUM_THREADS':'4'})
 if process.returncode: raise RuntimeError('人物生成失败，详情见本机 render.log')
 video = max((folder/'render').glob('*.mp4'),key=lambda p:p.stat().st_mtime)
 output = folder/'result.mp4'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf','scale=512:768','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',
  '-c:a','aac','-movflags','+faststart',str(output)],check=True,timeout=90)
 return {'duration':round(duration,2),'render_seconds':round(time.monotonic()-start,1),'width':512,'height':768,'fps':25}

def build_samples():
 ASSETS.mkdir(parents=True,exist_ok=True)
 manifest = {'character':'小晴','fictional':True,'mode':'prerendered','clips':[]}
 for state,style in STATES.items():
  folder = ASSETS/state; folder.mkdir(exist_ok=True)
  metadata = folder/'metadata.json'
  if (folder/'result.mp4').exists() and metadata.exists():
   item = json.loads(metadata.read_text(encoding='utf-8'))
  else:
   source = ASSETS/(('neutral' if state=='comfort' else state)+'.png')
   if not source.exists():
    print('Waiting for image: '+str(source),flush=True)
    continue
   audio = folder/'speech.mp3'
   voice = synthesize(style['text'],state,audio)
   print('Rendering '+state,flush=True)
   timing = render(source,audio,folder,state,lambda s:print(s,flush=True))
   item = {'id':state,'name':style['name'],'text':style['text'],'video':f'/media/{state}/result.mp4',
     'poster':f'/media/{state}/portrait.png','audio':f'/media/{state}/speech.mp3',**voice,**timing}
   metadata.write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
  manifest['clips'].append(item)
  temp = ASSETS/'manifest.tmp'; temp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(ASSETS/'manifest.json')
  print(json.dumps(item,ensure_ascii=False),flush=True)
 return manifest

if __name__=='__main__': build_samples()
