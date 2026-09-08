"""Real MiniMax candidate comparison; never changes the product configuration."""
import json,time
import minimax_dialogue as provider
from performance_jobs import ROOT,write

def main():
 c=provider.config();rows=[]
 cases=[([], '我今天修了一整天网页，很累。'),
  ([{'role':'user','content':'我今天一直在修网页。'},{'role':'assistant','content':'修网页很费精神，辛苦啦。'}],'你记得我今天在做什么吗？'),
  ([], '我刚完成了一个任务，想听你鼓励一下。')]
 for model in ['MiniMax-M2.7-highspeed','MiniMax-M3','M2-her']:
  for i,(history,text) in enumerate(cases):
   payload={'model':model,'messages':[{'role':'system','content':provider.SYSTEM},*history,{'role':'user','content':text}],
    'max_completion_tokens':4096 if model.startswith('MiniMax-M2') else 512,'temperature':.8,'stream':False}
   if model=='MiniMax-M3':payload['thinking']={'type':'disabled'}
   if model!='M2-her':payload['reasoning_split']=True
   start=time.monotonic();row={'model':model,'case':i,'input':text,'thinking':payload.get('thinking')}
   try:
    data=provider.post(c['chat_url'],c['chat_key'],payload);row['latency_s']=round(time.monotonic()-start,3)
    row['reply']=provider.parse_reply(data['choices'][0]['message']['content']);row['usage']=data.get('usage',{});row['ok']=True
   except Exception as e:row.update(ok=False,latency_s=round(time.monotonic()-start,3),error=str(e))
   rows.append(row);write(ROOT/'notes/minimax-first-reply-benchmark.json',rows);print(json.dumps(row,ensure_ascii=True),flush=True)
   if not row['ok'] and ('HTTP' in row.get('error','') or '错误码' in row.get('error','')):break
if __name__=='__main__':main()
