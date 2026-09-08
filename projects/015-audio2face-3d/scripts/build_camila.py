"""Convert licensed Camila sample for local preview only; never publish the output.

Reads numeric Maya mesh/morph attributes, without executing Maya scene commands.
Uses Reallusion's own expression mapping. Outputs stay in ignored .cache/camila.
"""
import json
import re
import shutil
from pathlib import Path
import numpy as np
from extract_geometry import attribute

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'vendor/Camila/Camila'
OUT = ROOT / '.cache/camila'

def ranges(raw, kind):
    result = []
    for a, b in re.findall(r'"'+kind+r'\[(\d+)(?::(\d+))?\]"', raw):
        result.extend(range(int(a), int(b or a)+1))
    return result

def convert_axes(v):
    return np.stack([v[...,0], v[...,2], -v[...,1]], axis=-1)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = (SOURCE/'scenes/Camila.ma').read_text(encoding='utf-8')
    blocks = {}
    for block in re.split(r'(?=createNode )', source):
        match = re.match(r'createNode (\S+) -n "([^"]+)"', block)
        if match: blocks[match[2]] = block
    mapping = json.loads((SOURCE/'scripts/MappingProfile.json').read_text())
    names = [x.decode() for x in np.load(ROOT/'vendor/models/mark-v2.3/bs_skin.npz')['poseNames'][1:]]
    all_meshes = []
    configurations = {
        'CC_Base_Body': [(1,'Std_Skin_Head'),(2,'Std_Skin_Body'),(3,'Std_Skin_Arm'),(4,'Std_Skin_Leg'),(5,'Std_Nails'),(6,'Std_Eyelash')],
        'CC_Base_Tongue': [(None,'Std_Tongue')],
        'CC_Base_Teeth': [(19,'Std_Upper_Teeth'),(20,'Std_Lower_Teeth')],
        'CC_Base_Eye': [(11,'Std_Eye_R'),(12,'Std_Cornea_R'),(13,'Std_Eye_L'),(14,'Std_Cornea_L')],
        'Camila_Brow': [(15,'Female_Brow_Transparency'),(16,'Female_Brow_Base_Transparency')],
        'Crop_T_shirts': [(None,'Crop_T_shirts')],
        'Side_part_wavy': [(17,'Scalp_Transparency'),(18,'Hair_Transparency')],
    }
    textures = {}
    for file in (SOURCE/'data/camila.fbm').glob('*'):
        if file.suffix.lower() in ['.jpg','.png']:
            textures[file.stem] = file.name
            shutil.copyfile(file, OUT/file.name)
    for mesh_name, groups in configurations.items():
        print('Converting',mesh_name,flush=True)
        block = blocks['camila02:'+mesh_name+'ShapeOrig']
        vertices = attribute(block,'vt','<f4',3)
        edges = attribute(block,'ed',np.int32,3)
        uvs = attribute(block,r'uvst\[0\]\.uvsp','<f4',2)
        polygons = []
        for chunk in re.finditer(r'"\.fc\[[^\]]+\]"\s+(?:-type "polyFaces"\s+)?([^;]+);',block):
            for face in re.finditer(r'\bf (\d+) ([^\n]+)\s+mu 0 \d+ ([^\n]+)',chunk[1]):
                e = [int(x) for x in face[2].split()]
                v = [int(edges[x,0]) if x>=0 else int(edges[-x-1,1]) for x in e]
                uv = [int(x) for x in face[3].split()]
                assert len(v)==len(uv)==int(face[1])
                polygons.append(list(zip(v,uv)))
        morph_block = blocks.get('camila02:Morpher_'+mesh_name,'')
        aliases = {int(i):name for name,i in re.findall(r'"([^"\n]+)"\s*,\s*"weight\[(\d+)\]"',morph_block)}
        targets = {}
        for m in re.finditer(r'"\.it\[0\]\.itg\[(\d+)\]\.iti\[6000\]\.ipt" -type "pointArray" ([^;]+);',morph_block):
            idx = int(m[1]); name = aliases.get(idx)
            if name not in mapping['expression']: continue
            points = np.fromstring(m[2],sep=' ',dtype='<f4')
            count = int(points[0]); points=points[1:].reshape(-1,4)[:,:3]
            ic = re.search(r'"\.it\[0\]\.itg\['+str(idx)+r'\]\.iti\[6000\]\.ict" -type "componentList" ([^;]+);',morph_block)
            ids = ranges(ic[1],'vtx')
            assert len(ids)==count==len(points)
            delta = np.zeros_like(vertices);delta[ids]=points
            targets[name]=delta
        basis = np.zeros((len(names),len(vertices),3),dtype='<f4')
        for i,name in enumerate(names):
            key = name if name in mapping['mapping'] else name.replace('Left','_L').replace('Right','_R')
            for expr,weight in zip(mapping['expression'],mapping['mapping'][key]):
                if weight and expr in targets:basis[i]+=targets[expr]*weight
        vertices=convert_axes(vertices);basis=convert_axes(basis)
        jaw_weights=np.zeros(len(vertices),dtype='<f4')
        cluster_name,jaw_id={'CC_Base_Body':('skinCluster11',77),'Side_part_wavy':('skinCluster5',2)}.get(mesh_name,(None,None))
        if cluster_name:
            for m in re.finditer(r'"\.wl\[(\d+)(?::(\d+))?\]\.w"\s+([^;]+);',blocks['camila02:'+cluster_name]):
                values=np.fromstring(m[3],sep=' ');cursor=0
                for vertex in range(int(m[1]),int(m[2] or m[1])+1):
                    count=int(values[cursor]);cursor+=1
                    for _ in range(count):
                        joint=int(values[cursor]);weight=values[cursor+1];cursor+=2
                        if joint==jaw_id:jaw_weights[vertex]=weight
                assert cursor==len(values)
        if mesh_name=='CC_Base_Tongue':jaw_weights[:]=1
        for gp,material in groups:
            face_ids = range(len(polygons)) if gp is None else ranges(re.search(r'"\.ic"[^;]+;',blocks['camila02:groupParts'+str(gp)])[0],'f')
            # Reinsert the small head polygons split into a separate Maya selection set.
            if mesh_name=='CC_Base_Body' and gp==1:face_ids=list(face_ids)+list(range(1638,1668))+list(range(3691,3721))
            if mesh_name=='CC_Base_Body':
                hidden=set(ranges(re.search(r'"\.ic"[^;]+;',blocks['groupParts26'])[0],'f'))
                face_ids=[f for f in face_ids if f not in hidden]
            lookup={};pairs=[];indices=[]
            for f in face_ids:
                polygon=polygons[f];p=[]
                for pair in polygon:
                    if pair not in lookup:lookup[pair]=len(pairs);pairs.append(pair)
                    p.append(lookup[pair])
                for k in range(1,len(p)-1):indices.extend([p[0],p[k],p[k+1]])
            pairs=np.array(pairs);vi=pairs[:,0]
            pos=vertices[vi];uv=uvs[pairs[:,1]].copy();uv[:,0]%=1
            local_basis=basis[:,vi].copy()
            if material=='Std_Lower_Teeth':
                jaw_weights[:]=0;jaw_weights[vi]=1
                local_basis[names.index('jawForward'),:,2]=1
                local_basis[names.index('jawLeft'),:,0]=1
                local_basis[names.index('jawRight'),:,0]=-1
            active=np.where(np.max(np.abs(local_basis),axis=(1,2))>1e-5)[0]
            tag=material
            for suffix,data in [('position',pos.astype('<f4')),('uv',uv.astype('<f4')),('index',np.array(indices,dtype='<u4')),('morph',local_basis[active].astype('<f4')),('jaw',jaw_weights[vi])]:
                (OUT/f'{tag}.{suffix}.bin').write_bytes(data.tobytes())
            tex={role:textures.get(material+'_'+role) for role in ['Diffuse','Normal','Opacity']}
            all_meshes.append({'name':tag,'vertices':len(pos),'indices':len(indices),'morphs':active.tolist(),'textures':tex,'jaw':bool(jaw_weights[vi].max()>0)})
    shutil.copyfile(SOURCE/'ReadMe.txt',OUT/'LICENSE.txt')
    (OUT/'character.json').write_text(json.dumps({'name':'Camila','expressions':names,'meshes':all_meshes,'license':'Local non-commercial evaluation only. Reallusion 2024. See LICENSE.txt.'},indent=2))
    print('Ready',OUT,flush=True)

if __name__=='__main__':main()
