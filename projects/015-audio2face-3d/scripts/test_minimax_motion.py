import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from minimax_motion import generate
from performance_jobs import write
from minimax_dialogue import ProviderError
import hashlib

class DurableVideoTests(unittest.TestCase):
 def test_unknown_submission_never_reissues_paid_request(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source.png';source.write_bytes(b'image');out=root/'state';out.mkdir()
   write(out/'generation.json',{'source_sha256':hashlib.sha256(b'image').hexdigest(),'status':'submitting'})
   with patch('minimax_motion.post') as post,self.assertRaises(ProviderError):generate(source,out,'listen')
   post.assert_not_called()
 def test_completed_download_is_reused_without_network(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source.png';source.write_bytes(b'image');out=root/'state';out.mkdir();(out/'generated.mp4').write_bytes(b'video')
   write(out/'generation.json',{'source_sha256':hashlib.sha256(b'image').hexdigest(),'status':'downloaded'})
   with patch('minimax_motion.post') as post,patch('minimax_motion.get') as get:
    self.assertEqual(generate(source,out,'listen'),out/'generated.mp4');post.assert_not_called();get.assert_not_called()
 def test_changed_photo_cannot_reuse_other_persons_video(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source.png';source.write_bytes(b'new-image');out=root/'state';out.mkdir();write(out/'generation.json',{'source_sha256':'wrong','task_id':'123'})
   with self.assertRaises(ValueError):generate(source,out,'listen')

if __name__=='__main__':unittest.main()
