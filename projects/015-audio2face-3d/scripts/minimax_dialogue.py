"""MiniMax-only conversation and expressive speech adapter. Credentials stay server-side."""
import json,re,urllib.request,urllib.error,queue,threading
from pathlib import Path
from urllib.parse import urlparse
from companion_media import settings

INTENTS={'listen','think','comfort','playful','annoyed','affirm'}
STYLE={'listen':('calm',1.0,0),'think':('calm',.96,0),'comfort':('calm',.94,-1),'playful':('happy',1.04,2),'annoyed':('angry',.98,-1),'affirm':('happy',1.02,1)}
SYSTEM='''你是小晴，一位原创成年女性虚拟陪伴角色。温柔、自然，有一点俏皮，用台湾华语常见的自然口语交流，避免刻意堆叠语气词。
结合用户的对话上下文回应；疲惫时先接住感受，完成任务时具体肯定。你可以读取本次会话最近六轮上下文；用户问是否记得刚才的内容时，直接根据前文回答，不要说自己没有记忆功能。未出现在上下文中的细节则诚实说明，不编造。不要主动解释技术实现。
每次只说1到2句、通常15到30个中文字符、最多45字，最多问一个问题。调皮或轻微不满只在明确的玩笑情境下使用，不贬低、操控用户，不宣称排他关系或真实人类身份。不要假称已经设置提醒、查看日历或执行你没有的工具。
只返回JSON对象，不输出说明或Markdown：{"reply":"可直接朗读的短回复","intent":"comfort"}。
intent只能是listen、think、comfort、playful、annoyed、affirm，必须与回复语气一致。不要输出动作描写、括号舞台指令或内部思考。'''

class ProviderError(RuntimeError):
 def __init__(self,message,code=None):super().__init__(message);self.code=code

# Cancelled callers detach from HTTP, but in-flight provider calls retain a slot.
# This bounds remote work even when a user repeatedly interrupts.
HTTP_SLOTS=threading.BoundedSemaphore(2)
def cancellable_post(url,key,payload,check):
 while not HTTP_SLOTS.acquire(timeout=.1):check()
 try:check()
 except BaseException:
  HTTP_SLOTS.release();raise
 result=queue.Queue(maxsize=1)
 def request():
  try:result.put((True,post(url,key,payload)))
  except Exception as e:result.put((False,e))
  finally:HTTP_SLOTS.release()
 threading.Thread(target=request,daemon=True).start()
 while True:
  check()
  try:ok,value=result.get(timeout=.1)
  except queue.Empty:continue
  check()
  if not ok:raise value
  return value

def config():
 local=settings();shared={};path=local.get('MINIMAX_CONFIG_FILE')
 if path and Path(path).is_file():
  for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
   if '=' in line and not line.lstrip().startswith('#'):
    k,v=line.split('=',1);shared[k.strip()]=v.strip().strip('\"\'')
 c={**shared,**{k:v for k,v in local.items() if v}};base=(c.get('MINIMAX_BASE_URL') or c.get('MINIMAX_API_BASE') or 'https://api.minimax.cn').rstrip('/')
 if base.endswith('/v1'):base=base[:-3]
 return {'chat_key':c.get('MINIMAX_CHAT_API_KEY') or c.get('MINIMAX_API_KEY',''),'speech_key':c.get('MINIMAX_SPEECH_API_KEY') or c.get('MINIMAX_API_KEY',''),
  'chat_url':c.get('MINIMAX_CHAT_URL') or base+'/v1/chat/completions','speech_url':c.get('MINIMAX_TTS_URL') or base+'/v1/t2a_v2',
  'chat_model':c.get('MINIMAX_CHAT_MODEL') or 'MiniMax-M3','chat_thinking':c.get('MINIMAX_CHAT_THINKING') or 'disabled','speech_model':c.get('MINIMAX_SPEECH_MODEL') or 'speech-2.8-hd',
  'voice_id':c.get('MINIMAX_VOICE_ID') or 'Chinese (Mandarin)_Warm_Girl'}

def status():
 c=config();missing=[name for name,key in [('对话 API Key','chat_key'),('语音 API Key','speech_key')] if not c[key]]
 return {'provider':'MiniMax','configured':not missing,'missing':missing,'chat_model':c['chat_model'],'chat_thinking':c['chat_thinking'] if c['chat_model']=='MiniMax-M3' else 'model_default','speech_model':c['speech_model'],'voice_id':c['voice_id'],'accent_verified':False}

def post(url,key,payload):
 if not key:raise ProviderError('请先在本机 .env.companion 配置 MiniMax API Key')
 parsed=urlparse(url)
 if parsed.scheme!='https' or parsed.hostname not in {'api.minimax.cn','api.minimax.io','api.minimaxi.com','api-bj.minimaxi.com'}:
  raise ProviderError('MiniMax 接口地址须使用官方 HTTPS 域名')
 req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=60) as response:data=json.load(response)
 except urllib.error.HTTPError as e:
  raise ProviderError(f'MiniMax HTTP {e.code}：请检查密钥、接口区域、模型权限和额度') from None
 except (urllib.error.URLError,TimeoutError,OSError):raise ProviderError('MiniMax 连接失败或超时，请稍后重试') from None
 except ValueError:raise ProviderError('MiniMax 返回了无法解析的数据') from None
 if not isinstance(data,dict):raise ProviderError('MiniMax 响应格式异常')
 code=data.get('base_resp',{}).get('status_code',0)
 if code==2056:raise ProviderError('MiniMax 当前时段资源额度已用尽（2056），请等待额度恢复后重试；已有视频可继续播放',code=code)
 if code:raise ProviderError(f'MiniMax 返回错误码 {code}，请检查模型/音色权限与账户额度',code=code)
 return data

def parse_reply(content):
 if not isinstance(content,str):raise ProviderError('对话模型没有返回文字')
 # Never display or speak provider reasoning fields or embedded thinking blocks.
 content=re.sub(r'<think>.*?</think>','',content,flags=re.S).strip()
 if '<think>' in content:raise ProviderError('对话输出尚未完成，请重试')
 content=re.sub(r'^```(?:json)?\s*|\s*```$','',content).strip()
 try:item=json.loads(content)
 except ValueError:
  try:item,_=json.JSONDecoder().raw_decode(content[content.index('{'):])
  except (ValueError,TypeError):raise ProviderError('对话模型未返回有效的回复与表情，请重试') from None
 if not isinstance(item,dict):raise ProviderError('对话结果结构不正确')
 reply=item.get('reply');intent=item.get('intent')
 if not isinstance(reply,str) or not 1<=len(reply.strip())<=60 or not isinstance(intent,str) or intent not in INTENTS:raise ProviderError('回复过长或表情格式不正确，请重试')
 if any(c in reply for c in '<>{}') or re.search(r'\b(?:https?://)',reply):raise ProviderError('回复包含不适合直接朗读的内容，请重试')
 return {'reply':reply.strip(),'intent':intent}

def reply(history,text,event=None,check=lambda:None):
 c=config();messages=[{'role':'system','content':SYSTEM}]
 # Keep historical assistant turns in the same response format as the next turn.
 # Plain historical answers otherwise encourage the model to abandon JSON.
 for m in history[-12:]:
  if m['role']=='user':messages.append({'role':'user','content':m['content']})
  elif m['role']=='assistant':messages.append({'role':'assistant','content':json.dumps({'reply':m['content'],'intent':m.get('intent','listen')},ensure_ascii=False)})
 content=text if event is None else '用户主动报告完成了一项任务，请给予具体、简短的肯定。用户的话：'+text
 messages.append({'role':'user','content':content})
 usages=[]
 for attempt in range(2):
  check()
  payload={'model':c['chat_model'],'messages':messages,'max_completion_tokens':512 if c['chat_model']=='MiniMax-M3' else 4096,'reasoning_split':True,'stream':False,'temperature':.8 if attempt==0 else .3}
  if c['chat_model']=='MiniMax-M3':payload['thinking']={'type':c['chat_thinking']}
  data=cancellable_post(c['chat_url'],c['chat_key'],payload,check)
  check()
  usages.append(data.get('usage',{}))
  try:
   choice=data['choices'][0]
   if choice.get('finish_reason')=='length':raise ProviderError('MiniMax 回复达到长度上限，请重试')
   result=parse_reply(choice['message']['content'])
   return {**result,'provider':'MiniMax','model':c['chat_model'],'usage':{'attempts':usages,'format_retries':attempt}}
  except (KeyError,IndexError,TypeError,ProviderError):
   if attempt:raise ProviderError('MiniMax 连续两次未返回有效短回复，请重试') from None
   messages[0]={'role':'system','content':SYSTEM+'\n严格按接口格式输出。你上次的输出未通过格式校验。只输出一个含 reply 和 intent 的 JSON 对象。不要解释，reply 不超过30字。'}

def speak(text,intent,target,check=lambda:None):
 c=config();emotion,speed,pitch=STYLE[intent]
 data=cancellable_post(c['speech_url'],c['speech_key'],{'model':c['speech_model'],'text':text,'stream':False,'output_format':'hex',
  'voice_setting':{'voice_id':c['voice_id'],'speed':speed,'vol':1,'pitch':pitch,'emotion':emotion},
  'audio_setting':{'sample_rate':32000,'bitrate':128000,'format':'mp3','channel':1},'language_boost':'Chinese'},check)
 try:audio=bytes.fromhex(data['data']['audio'])
 except (KeyError,TypeError,ValueError):raise ProviderError('MiniMax 没有返回有效语音') from None
 if not audio:raise ProviderError('MiniMax 返回了空语音')
 check();target.write_bytes(audio)
 return {'provider':'MiniMax','model':c['speech_model'],'voice':c['voice_id'],'emotion_control':True,'emotion':emotion,'speed':speed,'pitch':pitch}
