"""Public interactive replay; only explicitly selected fictional demo assets."""
import json

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
 for name in ['experience.html','experience.js']:copy(root/'demo'/name,name)
