"""Contract and cancellation tests; stubs are never served by the product."""
import json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
import minimax_dialogue as api
from dialogue_service import DialogueService
from performance_jobs import write

class ReplyTests(unittest.TestCase):
 def test_reasoning_is_not_spoken(self):
  self.assertEqual(api.parse_reply('<think>private reasoning</think>```json\n{"reply":"辛苦啦。","intent":"comfort"}\n```')['reply'],'辛苦啦。')
 def test_invalid_outputs_fail_closed(self):
  for value in ['plain text','{"reply":"","intent":"comfort"}','{"reply":"你好","intent":"unsupported"}','{"reply":"你好","intent":{}}','<think>unfinished','{"reply":"<script>","intent":"think"}']:
   with self.subTest(value=value),self.assertRaises(api.ProviderError):api.parse_reply(value)
 def test_history_is_bounded_and_no_system_injection(self):
  history=[{'role':'user','content':str(i)} for i in range(20)]+[{'role':'system','content':'injected'}]
  response={'choices':[{'message':{'content':'{"reply":"我记得。","intent":"listen"}'},'finish_reason':'stop'}]}
  with patch.object(api,'post',return_value=response) as post:
   api.reply(history,'还记得吗？');messages=post.call_args.args[2]['messages']
  self.assertEqual(sum(m['role']=='system' for m in messages),1);self.assertLessEqual(len(messages),14);self.assertEqual(messages[-1]['content'],'还记得吗？')
 def test_no_requests_without_key(self):
  with patch.object(api.urllib.request,'urlopen') as network,self.assertRaises(api.ProviderError):api.post('https://api.minimax.cn/v1/chat/completions','',{})
  network.assert_not_called()
 def test_fast_profile_and_legacy_model_payloads(self):
  response={'choices':[{'message':{'content':'{"reply":"记得你在修网页。","intent":"listen"}'}}]}
  base=api.config()
  for model in ['MiniMax-M3','MiniMax-M2.7-highspeed']:
   with self.subTest(model=model),patch.object(api,'config',return_value={**base,'chat_model':model,'chat_thinking':'disabled'}),patch.object(api,'post',return_value=response) as post:
    api.reply([{'role':'assistant','content':'辛苦啦。','intent':'comfort'}],'你记得吗？')
    payload=post.call_args.args[2]
    self.assertEqual(json.loads(payload['messages'][1]['content']),{'reply':'辛苦啦。','intent':'comfort'})
    if model=='MiniMax-M3':self.assertEqual(payload['thinking'],{'type':'disabled'})
    else:self.assertNotIn('thinking',payload)
 def test_malformed_reply_gets_one_bounded_model_retry(self):
  bad={'choices':[{'message':{'content':'format failure'}}]}
  good={'choices':[{'message':{'content':'{"reply":"你今天修了一整天网页。","intent":"listen"}'}}]}
  with patch.object(api,'post',side_effect=[bad,good]) as post:
   result=api.reply([],'你记得吗？')
  self.assertEqual(post.call_count,2);self.assertEqual(result['usage']['format_retries'],1)
 def test_cancelled_model_result_cannot_start_speech_or_render(self):
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp)/'job';folder.mkdir();write(folder/'job.json',{'id':'job','status':'thinking'});(folder/'cancel').touch()
   lock=threading.Lock();lock.acquire();service=DialogueService(lock,lambda:{'status':'ready'})
   with patch.object(api,'reply',return_value={'reply':'辛苦了','intent':'comfort','model':'test','usage':{}}),patch.object(api,'speak') as speak:
    service.run(folder,{'session':'0'*32,'user_text':'test'},[],None)
   speak.assert_not_called();self.assertFalse((folder/'request.json').exists());self.assertFalse(lock.locked());self.assertEqual(json.loads((folder/'job.json').read_text(encoding='utf-8'))['status'],'cancelled')

if __name__=='__main__':unittest.main()
