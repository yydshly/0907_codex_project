"""Read and selectively extract the official Reallusion sample ZIP via HTTP ranges."""
import io
import urllib.request
import zipfile
from pathlib import Path

URL='https://file.reallusion.com/nvidia/Reallusion_Character_Camila.zip'
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'vendor/Camila'

class RemoteZip(io.RawIOBase):
    def __init__(self):
        response=urllib.request.urlopen(urllib.request.Request(URL,method='HEAD'),timeout=60)
        self.size=int(response.headers['Content-Length'])
        self.pos=0
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        return self.pos
    def read(self,n=-1):
        if n<0:n=self.size-self.pos
        if n==0:return b''
        end=min(self.size-1,self.pos+n-1)
        request=urllib.request.Request(URL,headers={'Range':f'bytes={self.pos}-{end}'})
        with urllib.request.urlopen(request,timeout=180) as response:
            if response.status!=206:raise RuntimeError('Server must support byte ranges')
            data=response.read()
        self.pos+=len(data)
        return data

def extract(names):
    TARGET.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(RemoteZip()) as archive:
        for name in names:
            path=(TARGET/name).resolve()
            if not path.is_relative_to(TARGET.resolve()):raise ValueError('Invalid path')
            if path.is_file():continue
            path.parent.mkdir(parents=True,exist_ok=True)
            print('Downloading',name,flush=True)
            path.write_bytes(archive.read(name))
            print('Saved',path.stat().st_size,flush=True)

if __name__=='__main__':
    import sys,json
    if len(sys.argv)>1:
        extract(sys.argv[1:])
    else:
        with zipfile.ZipFile(RemoteZip()) as archive:
            files=[{'name':i.filename,'bytes':i.file_size,'compressed':i.compress_size} for i in archive.infolist()]
        TARGET.mkdir(parents=True,exist_ok=True)
        (TARGET/'zip-index.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
        print(json.dumps(files,indent=2))
