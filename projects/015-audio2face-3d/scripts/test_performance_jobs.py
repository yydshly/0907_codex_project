import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from performance_jobs import write,read

class AtomicJobTests(unittest.TestCase):
 def test_read_retries_transient_rename_contention(self):
  with patch.object(Path,'read_text',side_effect=[PermissionError('renaming'),PermissionError('renaming'),'{"status":"done"}']) as reader:
   self.assertEqual(read(Path('job.json')),{'status':'done'});self.assertEqual(reader.call_count,3)
 def test_invalid_json_is_not_hidden_by_retries(self):
  with patch.object(Path,'read_text',return_value='broken') as reader,self.assertRaises(json.JSONDecodeError):read(Path('job.json'))
  self.assertEqual(reader.call_count,1)
 def test_transient_reader_contention_keeps_old_json_until_replace(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'job.json';write(path,{'status':'old'});replace=Path.replace;calls=[]
   def busy(source,target):
    calls.append(1)
    if len(calls)<3:
     self.assertEqual(json.loads(path.read_text())['status'],'old');raise PermissionError('reader handle')
    return replace(source,target)
   with patch.object(Path,'replace',busy):write(path,{'status':'new'})
   self.assertEqual(json.loads(path.read_text())['status'],'new');self.assertEqual(list(Path(temp).glob('*.tmp')),[])
 def test_permanent_failure_does_not_corrupt_previous_state(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'job.json';write(path,{'status':'old'})
   with patch.object(Path,'replace',side_effect=PermissionError('blocked')),patch('performance_jobs.time.sleep'),self.assertRaises(PermissionError):write(path,{'status':'new'})
   self.assertEqual(json.loads(path.read_text())['status'],'old');self.assertEqual(list(Path(temp).glob('*.tmp')),[])
if __name__=='__main__':unittest.main()
