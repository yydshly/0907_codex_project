"""Public interactive replay; only explicitly selected fictional demo assets."""
import json,re

def build(root,target,copy):
 states={'listen':'倾听','think':'思考','comfort':'安慰','playful':'调皮','annoyed':'轻微不满','affirm':'肯定'}
 people=[]
 for key,name,folder,reply in [('qing','小晴 · 本地面部',None,'media/welcome-result.mp4'),('ruoan','若安 · 自然半身','371ea1eac99f4bdfa994b7f8796d5e69','media/ruoan-body.mp4')]:
  base=root/'.cache/avatars'/folder/'assets' if folder else root/'.cache/performance'
  motions=[]
  for state,label in states.items():
   candidates=[base/state/'motion.mp4',base/'assets'/state/'motion.mp4']
   source=next((p for p in candidates if p.exists()),None)
   if source is None:raise FileNotFoundError(str(candidates))
   dest=f'media/{key}-{state}.mp4';copy(source,dest)
   motions.append({'id':state,'label':label,'video':dest})
  people.append({'id':key,'name':name,'reply':reply,'motions':motions})
 (target/'experience-data.json').write_text(json.dumps(people,ensure_ascii=False),encoding='utf-8')
 for name in ['experience.html','experience.js','dialogue-entry.html']:copy(root/'demo'/name,name)
 for name in ['dialogue.css','characters.css','public-workflow.js']:copy(root/'demo'/name,name)
 for source,dest,kind in [('characters.html','characters.html','characters'),('dialogue.html','chat.html','chat')]:
  html=(root/'demo'/source).read_text(encoding='utf-8')
  html=re.sub(r'<header>.*?</header>','<header><a class="brand" href="index.html">数字人物实验室</a><nav><a href="characters.html">人物选择</a><a href="chat.html">人物对话</a><a href="experience.html">六种动作</a><a href="implementation-guide.html">实施指引</a></nav></header>',html,count=1)
  html=html.replace('href="/dialogue.css"','href="dialogue.css"').replace('href="/characters.css"','href="characters.css"')
  html=re.sub(r'<script src="[^"]+"></script>','<script src="public-workflow.js"></script>',html)
  html=html.replace('<body>','<body data-preview="'+kind+'">')
  notice='<aside style="margin:18px auto;padding:18px;max-width:1200px;background:#e6d3ad;color:#253126;border-radius:12px"><strong>页面留档 · 公开静态预览</strong><p>保留本地人物选择和对话界面，方便回顾操作流程。可以选择预设人物并进入对话页、播放已保存片段；上传、发送新消息和生成新视频需本地服务。这里不会调用模型或保存聊天记录。</p><a href="dialogue-entry.html" style="color:#253126;text-decoration:underline">查看本地运行说明</a></aside>'
  html=html.replace('</header>','</header>'+notice,1)
  # Disable backend-dependent controls in the HTML itself, even before JS loads.
  if kind=='characters':
   html=html.replace('<form id="upload-form">','<form id="upload-form"><fieldset disabled style="border:0;padding:0;margin:0">').replace('</form>','</fieldset></form>',1)
   html=html.replace('首次准备需要生成六组动作和嘴部缓存，通常需要数分钟。','公开版保留上传流程界面；上传并准备人物需本地 8022 服务。')
  else:
   html=html.replace('<textarea id="message"','<textarea disabled id="message"').replace('例如：今天工作好累……','公开预览不能发送消息；请在本地对话页输入。')
   html=html.replace('id="send"','disabled id="send"').replace('id="new-session"','disabled id="new-session"')
   html=html.replace('<button data-text=','<button disabled data-text=').replace('id="task-done"','disabled id="task-done"')
   html=html.replace('正在准备对话…','静态预览：发送功能未连接后端。').replace('完成一轮后显示真实等待时间。','本地运行后，此处显示对话、语音与口型生成耗时。')
   html=html.replace('这里是你和 AI 伙伴的对话。回复由 MiniMax 根据上下文生成。','流程说明：本地输入消息 → MiniMax 生成回复与语音 → MuseTalk 生成分段视频 → 人物播放回应。这里没有加载任何私人会话。')
   html=html.replace('<div class="suggestions">','<button id="preview-reply" type="button">播放已保存的人物片段（不是新回复）</button><div class="suggestions">')
  (target/dest).write_text(html,encoding='utf-8')
