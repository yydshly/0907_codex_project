"""Fetch and prepare the official sample for personal local evaluation only."""
import sys
import zipfile
import subprocess
from fetch_camila import RemoteZip, extract, ROOT

if __name__=='__main__':
    names=['Camila/ReadMe.txt','Camila/scenes/Camila.ma','Camila/scripts/MappingProfile.json','Camila/scripts/mace_RL_load_json.py']
    with zipfile.ZipFile(RemoteZip()) as archive:
        names += [n for n in archive.namelist() if n.startswith('Camila/data/camila.fbm/')
                  and n.endswith(('.jpg','.png')) and any(t in n for t in ['Diffuse','Opacity','Normal'])
                  and not any(t in n for t in ['Denim','Canvas'])]
    extract(names)
    print('Camila is licensed for personal non-commercial evaluation, without redistribution. See vendor/Camila/Camila/ReadMe.txt.',flush=True)
    if not (ROOT/'vendor/models/mark-v2.3/bs_skin.npz').exists():
        from download_model import download
        download('bs_skin.npz')
    for script in ['build_camila.py','retarget.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)],check=True,cwd=ROOT)
