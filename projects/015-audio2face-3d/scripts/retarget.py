"""Constrained Mark surface -> ARKit fit for the local Camila preview.

Independent adapter, not NVIDIA's production blendshape solver. The motion
comes from real model output; no waveform-amplitude mouth animation is used.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

class Retarget:
    def __init__(self):
        cache=ROOT/'.cache/retarget-fit-v2.npz'
        if not cache.exists():
            data=np.load(ROOT/'vendor/models/mark-v2.3/model_data.npz')
            bs=np.load(ROOT/'vendor/models/mark-v2.3/bs_skin.npz')
            names=[x.decode() for x in bs['poseNames'][1:]]
            ids=bs['frontalMask'].astype(int).ravel()[::3]
            neutral=bs['neutral'][ids]
            # Named poses are DELTAS; only the neutral array is absolute geometry.
            a=np.stack([bs[n][ids].ravel() for n in names],axis=1).astype('f8')
            shapes=data['shapes_matrix_skin'][:,ids].reshape(272,-1)
            offset=(data['shapes_mean_skin'][ids]-neutral).ravel()
            gram=a.T@a
            gram+=np.eye(len(names))*np.trace(gram)/len(names)*.002
            np.savez(cache,gram=gram,projection=a.T@shapes.T,offset=a.T@offset,names=names)
        fit=np.load(cache)
        self.gram=fit['gram'];self.projection=fit['projection'];self.offset=fit['offset']
        self.names=fit['names'].tolist();self.lipschitz=np.linalg.eigvalsh(self.gram)[-1]

    def solve(self,coeffs):
        rhs=coeffs[:,:272]@self.projection.T+self.offset
        x=np.zeros_like(rhs);y=x.copy();t=1
        for _ in range(220):
            nxt=np.clip(y+(rhs-y@self.gram)/self.lipschitz,0,1)
            tn=(1+np.sqrt(1+4*t*t))/2
            y=nxt+(t-1)/tn*(nxt-x);x=nxt;t=tn
        return x.astype('f4')

    def export(self,coefficients,report,path):
        weights=self.solve(coefficients)
        output=dict(report)
        output.update({'expressions':self.names,'weights':np.round(weights,5).tolist(),
                       'adapter':'Independent constrained ARKit surface fit + Reallusion expression mapping; approximate joint preview'})
        Path(path).write_text(json.dumps(output,ensure_ascii=False),encoding='utf-8')
        return output

if __name__=='__main__':
    adapter=Retarget()
    out=ROOT/'.cache/camila'
    for source in (ROOT/'demo/assets').glob('*.coeffs.npy'):
        name=source.name.removesuffix('.coeffs.npy')
        meta=json.loads(source.with_name(name+'.json').read_text(encoding='utf-8'))
        adapter.export(np.load(source),meta,out/(name+'.json'))
        print(name,flush=True)
