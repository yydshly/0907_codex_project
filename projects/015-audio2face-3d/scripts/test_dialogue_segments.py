import threading,time,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import minimax_dialogue as provider
from dialogue_segments import split_reply
from dialogue_service import DialogueCancelled

class SegmentTests(unittest.TestCase):
 def test_natural_boundaries_preserve_every_character(self):
  text='修了一整天网页很辛苦呢，你现在可以好好休息一下了。'
  parts=split_reply(text)
  self.assertEqual(len(parts),2);self.assertEqual(''.join(parts),text)
  self.assertTrue(parts[0].endswith('，'));self.assertGreaterEqual(min(map(len,parts)),6)
  self.assertEqual(split_reply('辛苦啦。'),['辛苦啦。'])
  self.assertEqual(split_reply('这是一段没有合适标点所以不应该从词语中间切开的回复'),['这是一段没有合适标点所以不应该从词语中间切开的回复'])
 def test_cancel_detaches_http_but_keeps_remote_concurrency_bounded(self):
  release=threading.Event();entered=threading.Event();cancel=threading.Event();errors=[]
  def network(*args):entered.set();release.wait(3);return {'ok':True}
  def check():
   if cancel.is_set():raise DialogueCancelled()
  def caller():
   try:provider.cancellable_post('url','key',{},check)
   except DialogueCancelled:errors.append('cancelled')
  slots=threading.BoundedSemaphore(1)
  with patch.object(provider,'post',side_effect=network),patch.object(provider,'HTTP_SLOTS',slots):
   thread=threading.Thread(target=caller);thread.start();self.assertTrue(entered.wait(1));start=time.monotonic();cancel.set();thread.join(1)
   self.assertEqual(errors,['cancelled']);self.assertLess(time.monotonic()-start,.5)
   self.assertFalse(slots.acquire(False));release.set()
   self.assertTrue(slots.acquire(timeout=1));slots.release()
 def test_cancelled_speech_never_writes_late_audio(self):
  cancel=threading.Event()
  def network(*args):cancel.set();return {'data':{'audio':'1234'}}
  def check():
   if cancel.is_set():raise DialogueCancelled()
  with tempfile.TemporaryDirectory() as temp,patch.object(provider,'post',side_effect=network):
   target=Path(temp)/'speech.mp3'
   with self.assertRaises(DialogueCancelled):provider.speak('你好','listen',target,check=check)
   self.assertFalse(target.exists())

if __name__=='__main__':unittest.main()
