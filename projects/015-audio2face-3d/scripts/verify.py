"""Numerical and local HTTP checks for actual generated animation artifacts."""
import json
import urllib.request
import urllib.error
from pathlib import Path
import numpy as np
from inference import ROOT, MODEL

assets = ROOT / 'demo/assets'
reports = []
data = np.load(MODEL / 'model_data.npz')
shapes = data['shapes_matrix_skin'].reshape(272, -1)
base_mean = data['shapes_mean_skin'].reshape(-1)
for name in ['hello-neutral','hello-joy','hello-anger','phonemes-neutral','phonemes-joy','phonemes-anger']:
    meta = json.loads((assets / f'{name}.json').read_text(encoding='utf-8'))
    buf = (assets / f'{name}.bin').read_bytes()
    n, k, f = meta['vertices'] * 3, meta['rank'], meta['frames']
    mean = np.frombuffer(buf, '<f4', n)
    scales = np.frombuffer(buf, '<f4', k, n*4)
    basis = np.frombuffer(buf, '<i2', k*n, n*4+k*4).reshape(k,n)
    weights = np.frombuffer(buf, '<f4', f*k, n*4+k*4+2*k*n).reshape(f,k)
    original = np.load(assets / f'{name}.coeffs.npy')
    errors = []
    for frame in [0,f//3,f//2,f-1]:
        rebuilt = mean+(weights[frame]*scales)@basis.astype(np.float32)
        exact = base_mean + original[frame,:272]@shapes
        errors.append(float(np.sqrt(np.mean((rebuilt-exact)**2))))
    assert np.isfinite(mean).all() and np.isfinite(weights).all()
    assert max(errors)<.03, (name, errors)  # Scene is in centimeters: <0.3 mm RMS.
    assert meta['coefficient_motion_max']>1
    reports.append({'sample':name,'max_sampled_vertex_rms_cm':max(errors),'frames':f,'providers':meta['providers']})
idx = np.fromfile(assets / 'skin.indices.bin', '<u4')
assert idx.max()==61519 and len(np.unique(idx))==61520
a=np.load(assets/'hello-neutral.coeffs.npy')
b=np.load(assets/'hello-joy.coeffs.npy')
assert float(np.max(np.abs(a-b)))>1
status=json.load(urllib.request.urlopen('http://127.0.0.1:8015/api/status'))
assert status['ready']
for body, expected in [(b'abc',400),(np.full(4000,np.nan,dtype='<f4').tobytes(),400)]:
    try:
        urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8015/api/generate',data=body,headers={'Content-Type':'application/octet-stream'}))
        raise AssertionError('Invalid input was accepted')
    except urllib.error.HTTPError as e:
        assert e.code==expected
result={'passed':True,'topology':{'vertices':61520,'triangles':len(idx)//3,'all_vertices_referenced':True},'samples':reports,'api_status':status,'invalid_input_checks':'short payload and NaN rejected'}
(ROOT/'notes/verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
