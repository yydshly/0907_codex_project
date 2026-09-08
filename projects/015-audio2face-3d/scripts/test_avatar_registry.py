import io,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import avatar_registry as a
from dialogue_service import DialogueService

def photo(size=(400,300)):
 stream=io.BytesIO();Image.new('RGB',size,(100,80,60)).save(stream,'PNG');return stream.getvalue()

class RegistryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.patch=patch.object(a,'AVATARS',Path(self.tmp.name));self.patch.start()
 def tearDown(self):self.patch.stop();self.tmp.cleanup()
 def test_normalize_preserves_aspect_and_strips_metadata(self):
  im=Image.open(io.BytesIO(a.normalize(photo())));self.assertEqual(im.size,(512,768))
  self.assertEqual(im.getpixel((256,384)),(100,80,60));self.assertNotEqual(im.getpixel((256,0)),(100,80,60));self.assertNotIn('exif',im.info)
 def test_invalid_uploads(self):
  for raw in (b'not an image',photo((100,100)),b'x'*(12*1024*1024+1)):
   with self.subTest(length=len(raw)),self.assertRaises(ValueError):a.normalize(raw)
 def test_ids_are_contained(self):
  for key in ('../performance','a'*31,'A'*32,None,[], 'a'*32+'/../../'):
   with self.subTest(key=key),self.assertRaises(ValueError):a.get(key)
 def test_distinct_uploads_never_share_mutable_assets(self):
  one=a.create(photo(),'One');two=a.create(photo(),'Two')
  self.assertNotEqual(one['id'],two['id'])
  with self.assertRaises(ValueError):a.asset_root(one['id'])
  a.change(one['id'],status='ready');a.change(two['id'],status='ready')
  self.assertNotEqual(a.asset_root(one['id']),a.asset_root(two['id']))
  self.assertEqual(a.asset_for({'state':'listen','avatar_id':one['id']}),a.AVATARS/one['id']/'assets/listen')
 def test_unknown_state_does_not_escape(self):
  with self.assertRaises(ValueError):a.asset_for({'state':'../../secret'})
 def test_existing_jobs_keep_default(self):self.assertEqual(a.asset_for({'state':'listen'}),a.ASSETS/'listen')
 def test_session_binding_and_mismatch_rejected(self):
  avatar=a.create(photo(),'New');a.change(avatar['id'],status='ready')
  svc=DialogueService(threading.Lock(),lambda:{'status':'ready'});svc.storage=Path(self.tmp.name)/'sessions'
  session=svc.create(avatar['id']);self.assertEqual(svc.session(session['id'])['avatar_id'],avatar['id'])
  with self.assertRaisesRegex(ValueError,'人物不一致'):svc.submit({'session':session['id'],'avatar_id':'xiaoqing','text':'hello'})
 def test_unready_cannot_start_session(self):
  avatar=a.create(photo(),'New');svc=DialogueService(threading.Lock(),lambda:{'status':'ready'})
  with self.assertRaises(ValueError):svc.create(avatar['id'])

if __name__=='__main__':unittest.main()
