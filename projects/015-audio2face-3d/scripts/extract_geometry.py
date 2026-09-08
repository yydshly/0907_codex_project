"""Read vertices/edge topology from the official Maya ASCII asset without Maya.
Only parses numeric mesh attributes; never executes scene commands.
"""
import json
import re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'vendor/Maya-ACE/sample_project/maya_geom/mark_geom_v2_topo1.ma'
OUT = ROOT / 'demo/assets'

def attribute(block, key, dtype, width):
    chunks = []
    pattern = r'setAttr[^;]*?"\.' + key + r'\[(\d+)(?::(\d+))?\]"\s+([^;]+);'
    for match in re.finditer(pattern, block):
        raw = re.sub(r'-type\s+"[^"]+"', '', match[3])
        values = np.fromstring(raw, sep=' ', dtype=dtype).reshape(-1, width)
        chunks.append((int(match[1]), values))
    size = max(start + len(a) for start, a in chunks)
    result = np.empty((size, width), dtype=dtype)
    for start, a in chunks:
        result[start:start+len(a)] = a
    return result

def parse():
    source = SOURCE.read_text(encoding='utf-8')
    blocks = re.split(r'(?=createNode )', source)
    report = []
    for block in blocks:
        m = re.match(r'createNode mesh -n "([^"]+)"', block)
        if not m:
            continue
        name = m[1]
        if name not in ['c_headWatertight_hiShape', 'r_choroid_hiShape', 'l_choroid_hiShape', 'r_lens_hiShape', 'l_lens_hiShape']:
            continue
        vertices = attribute(block, 'vt', '<f4', 3)
        edges = attribute(block, 'ed', np.int32, 3)
        triangles = []
        for fc in re.finditer(r'"\.fc\[[^\]]+\]"\s+(?:-type "polyFaces"\s+)?([^;]+);', block):
            for face in re.finditer(r'(?:^|\n)\s*f\s+(\d+)\s+([^\n]+)', fc[1]):
                ids = [int(n) for n in face[2].split()[:int(face[1])]]
                polygon = [int(edges[e, 0]) if e >= 0 else int(edges[-e-1, 1]) for e in ids]
                for k in range(1, len(polygon)-1):
                    triangles.extend((polygon[0], polygon[k], polygon[k+1]))
        index = np.array(triangles, dtype='<u4')
        assert len(index) and index.max() < len(vertices)
        if name.startswith('c_head'):
            assert len(vertices) == 61520, 'Topology must match the Mark v2.3 model'
            tag = 'skin'
        else:
            tag = name.replace('_hiShape', '')
        (OUT / f'{tag}.indices.bin').write_bytes(index.tobytes())
        (OUT / f'{tag}.vertices.bin').write_bytes(vertices.tobytes())
        report.append({'name': tag, 'vertices': len(vertices), 'triangles': len(index)//3})
    (OUT / 'geometry.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    parse()
