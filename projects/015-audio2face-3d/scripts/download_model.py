"""Download the official open-weight Mark model into ignored local storage."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'vendor' / 'models' / 'mark-v2.3'
REPO = 'nvidia/Audio2Face-3D-v2.3-Mark'
REVISION = '5451728e07378df93b04523279e134a9993ae71b'
FILES = ['README.md', 'model.json', 'model_config.json', 'network_info.json',
         'network.onnx', 'model_data.npz', 'implicit_emo_db.npz']

def download(name):
    path = TARGET / name
    if not path.exists():
        url = f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}'
        with urllib.request.urlopen(url, timeout=120) as response, path.with_suffix(path.suffix + '.part').open('wb') as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        path.with_suffix(path.suffix + '.part').replace(path)
    result = {'file': name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    print(json.dumps(result), flush=True)
    return result

if __name__ == '__main__':
    TARGET.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(download, FILES))
    (TARGET / 'download-manifest.json').write_text(json.dumps({'repository': REPO, 'revision': REVISION, 'files': records}, indent=2), encoding='utf-8')
