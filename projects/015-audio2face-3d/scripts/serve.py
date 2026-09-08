"""Loopback-only demo server. Uploads are processed locally by the official model."""
import argparse
import json
import threading
import uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import numpy as np
from inference import Engine, ROOT
from retarget import Retarget

OUTPUT = ROOT / '.cache/generated'
lock = threading.Lock()
engine = None
retarget = None

class Handler(SimpleHTTPRequestHandler):
    def json_response(self, code, data):
        raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def translate_path(self, path):
        clean = unquote(urlparse(path).path)
        if clean.startswith('/character/'):
            root = ROOT / '.cache/camila'
            destination = (root / clean.removeprefix('/character/')).resolve()
            return str(destination if destination.is_relative_to(root.resolve()) else root/'invalid')
        if clean in ['/', '/index.html'] and (ROOT/'.cache/camila/character.json').exists():
            return str(ROOT/'demo/realistic.html')
        if clean.startswith('/generated/'):
            destination = (OUTPUT / clean.removeprefix('/generated/')).resolve()
            if not destination.is_relative_to(OUTPUT.resolve()):
                return str(OUTPUT / 'invalid')
            return str(destination)
        return super().translate_path(path)

    def do_GET(self):
        if urlparse(self.path).path == '/api/status':
            return self.json_response(200, {'ready': engine is not None, 'model': 'Mark v2.3', 'providers': engine.session.get_providers() if engine else []})
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/api/generate':
            return self.json_response(404, {'error': '接口不存在'})
        # Reject cross-origin browser requests; no external service receives audio.
        origin = self.headers.get('Origin')
        if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}']:
            return self.json_response(403, {'error': '只接受本机页面请求'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.json_response(400, {'error': '无效长度'})
        if length < 16000 or length > 16000 * 20 * 4 or length % 4:
            return self.json_response(400, {'error': '请使用 0.25–20 秒音频'})
        emotion = parse_qs(parsed.query).get('emotion', ['neutral'])[0]
        if emotion not in ['neutral', 'joy', 'anger']:
            return self.json_response(400, {'error': '不支持的表情'})
        if not lock.acquire(blocking=False):
            return self.json_response(409, {'error': '已有任务生成中，请稍候'})
        try:
            body = self.rfile.read(length)
            if len(body) != length:
                return self.json_response(400, {'error': '音频上传不完整'})
            pcm = np.frombuffer(body, dtype='<f4')
            if not np.isfinite(pcm).all():
                return self.json_response(400, {'error': '音频数据无效'})
            name = uuid.uuid4().hex
            report = engine.export(pcm, 16000, emotion, OUTPUT, name)
            if retarget:
                retarget.export(np.load(OUTPUT/f'{name}.coeffs.npy'), report, OUTPUT/f'{name}.camila.json')
            self.json_response(200, {'url': f'/generated/{name}.json', 'camila_url': f'/generated/{name}.camila.json' if retarget else None, 'base': '/generated/', 'report': report})
        except Exception as error:
            self.json_response(500, {'error': str(error)})
        finally:
            lock.release()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8015)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    print('Loading official Mark model...', flush=True)
    engine = Engine()
    if (ROOT/'.cache/camila/character.json').exists():
        retarget = Retarget()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT / 'demo')))
    print(f'Ready: http://127.0.0.1:{args.port} / {engine.session.get_providers()}', flush=True)
    server.serve_forever()
