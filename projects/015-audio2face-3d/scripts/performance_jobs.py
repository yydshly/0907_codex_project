"""Shared on-disk job protocol; no credentials are stored in job metadata."""
import json,uuid,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'.cache/performance';JOBS=ROOT/'.cache/performance-jobs'

def read(path):
 for attempt in range(12):
  try:return json.loads(path.read_text(encoding='utf-8'))
  except PermissionError:
   if attempt==11:raise
   time.sleep(min(.01*(attempt+1),.1))
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  # Windows can briefly reject replacement while another process reads the file.
  # Keep the previous complete JSON visible and retry only the atomic rename.
  for attempt in range(12):
   try:temp.replace(path);break
   except PermissionError:
    if attempt==11:raise
    time.sleep(min(.01*(attempt+1),.1))
 finally:temp.unlink(missing_ok=True)
def update(folder,**values):
 path=folder/'job.json';data=read(path) if path.exists() else {}
 data.update(values);write(path,data);return data
def cancelled(folder):return (folder/'cancel').exists()
