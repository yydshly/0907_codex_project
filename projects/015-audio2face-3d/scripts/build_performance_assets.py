"""Six real LivePortrait animations of the same fictional character.

Uses official portrait-editing delta functions without importing the Gradio UI.
This controls the face/head; it does not synthesize new arm gestures.
"""
import ast,gc,json,subprocess,sys,time,hashlib
from pathlib import Path
import cv2,numpy as np,torch
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT/'vendor/LivePortrait';OUT=ROOT/'.cache/performance'
sys.path.insert(0,str(REPO));torch.set_num_threads(4)
STATES={
 'listen':{'name':'倾听','description':'轻点头、自然眨眼','pitch':3,'yaw':0,'roll':1.5,'smile':.08,'brow':0},
 'think':{'name':'思考','description':'偏头、移开视线、轻挑眉','pitch':-2,'yaw':-7,'roll':4,'smile':-.08,'brow':3},
 'comfort':{'name':'安慰','description':'柔和微笑、轻微侧头','pitch':2,'yaw':2,'roll':-4,'smile':.3,'brow':1},
 'playful':{'name':'调皮','description':'歪头、短暂眨单眼、微笑','pitch':0,'yaw':3,'roll':5,'smile':.55,'brow':3},
 'annoyed':{'name':'轻微不满','description':'皱眉、收起笑容、轻摇头 · 使用同角色表情参考图','pitch':-1,'yaw':-6,'roll':-2,'smile':0,'brow':0},
 'affirm':{'name':'肯定','description':'微笑、两次轻点头','pitch':5,'yaw':0,'roll':0,'smile':.6,'brow':1}
}

@torch.inference_mode()
def main(source_path=None, output=None, progress=lambda *args:None):
 global OUT
 generic=source_path is not None
 if output is not None:OUT=Path(output)
 source_path=Path(source_path) if generic else ROOT/'.cache/companion/neutral.png'
 from facexlib.detection import init_detection_model
 from facexlib.alignment import init_alignment_model,landmark_98_to_68
 from src.utils.crop import crop_image,prepare_paste_back,paste_back
 from src.config.inference_config import InferenceConfig
 from src.live_portrait_wrapper import LivePortraitWrapper
 from src.utils.camera import get_rotation_matrix
 OUT.mkdir(parents=True,exist_ok=True);source=cv2.resize(cv2.imread(str(source_path)),(512,768))
 progress('检查人脸和姿态',.01)
 detector=init_detection_model('retinaface_resnet50',device='cuda',model_rootpath=str(ROOT/'vendor/photo-models'))
 align=init_alignment_model('awing_fan',device='cuda',model_rootpath=str(ROOT/'vendor/photo-models'))
 detections=detector.detect_faces(source,.9)
 if len(detections)!=1:raise ValueError('请使用仅有一张清晰人脸的照片；当前未检出人脸或存在多人')
 d=detections[0];x,y,x2,y2=d[:4];w=x2-x;h=y2-y
 if generic and (w<90 or h<100):raise ValueError('人脸过小，请使用正面近景或半身照片')
 l=max(0,int(x-.15*w));r=min(512,int(x2+.15*w));t=max(0,int(y-.18*h));b=min(768,int(y2+.1*h))
 points=landmark_98_to_68(align.get_landmarks(source[t:b,l:r]))+np.array([l,t])
 angry=source;angry_crop=None
 if not generic:
  angry=cv2.resize(cv2.imread(str(ROOT/'.cache/companion/angry.png')),(512,768))
  ad=max(detector.detect_faces(angry,.9),key=lambda a:(a[2]-a[0])*(a[3]-a[1]));ax,ay,ax2,ay2=ad[:4];aw=ax2-ax;ah=ay2-ay
  al=max(0,int(ax-.15*aw));ar=min(512,int(ax2+.15*aw));at=max(0,int(ay-.18*ah));ab=min(768,int(ay2+.1*ah))
  angry_points=landmark_98_to_68(align.get_landmarks(angry[at:ab,al:ar]))+np.array([al,at])
  angry_crop=crop_image(angry[:,:,::-1],angry_points,dsize=512,scale=2.3,vy_ratio=-.125)
 del detector,align;gc.collect();torch.cuda.empty_cache()
 crop=crop_image(source[:,:,::-1],points,dsize=512,scale=2.3,vy_ratio=-.125)
 cfg=InferenceConfig();model=LivePortraitWrapper(cfg)
 image=model.prepare_source(crop['img_crop']);info=model.get_kp_info(image);features=model.extract_feature_3d(image);kp=model.transform_keypoint(info)
 if generic and (abs(float(info['yaw'].item()))>30 or abs(float(info['pitch'].item()))>25):raise ValueError('侧脸或俯仰角度过大，请换接近正面的照片')
 mask=prepare_paste_back(cfg.mask_crop,crop['M_c2o'],(512,768))
 neutral_source=source.copy();neutral_crop=crop
 # Extract unchanged official editing functions; avoid UI/InsightFace dependencies.
 tree=ast.parse((REPO/'src/gradio_pipeline.py').read_text(encoding='utf-8'))
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GradioPipeline')
 methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name.startswith('update_delta_new_')]
 module=ast.Module(body=[ast.ClassDef(name='Edits',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[])
 namespace={'torch':torch};exec(compile(ast.fix_missing_locations(module),str(REPO/'src/gradio_pipeline.py'),'exec'),namespace);edits=namespace['Edits']()
 manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))['assets'] if (OUT/'manifest.json').exists() else []
 for name,spec in STATES.items():
  if not generic and len(sys.argv)>1 and name not in sys.argv[1:]:continue
  spec=dict(spec)
  if generic and name=='annoyed':spec.update(smile=-.12,brow=-3,description='收起笑容、轻皱眉和小幅摇头')
  source,crop=(angry,angry_crop) if name=='annoyed' and not generic else (neutral_source,neutral_crop)
  image=model.prepare_source(crop['img_crop']);info=model.get_kp_info(image);features=model.extract_feature_3d(image);kp=model.transform_keypoint(info)
  mask=prepare_paste_back(cfg.mask_crop,crop['M_c2o'],(512,768))
  folder=OUT/name;frames=folder/'frames';frames.mkdir(parents=True,exist_ok=True);start=time.monotonic();poses=[]
  for i in range(100):
   progress('生成'+spec['name']+'动作',.05+.60*(list(STATES).index(name)+i/100)/6)
   phase=i/99;envelope=np.sin(np.pi*phase)**2
   pitch=spec['pitch']*envelope*(np.sin(4*np.pi*phase) if name=='affirm' else np.sin(2*np.pi*phase))
   yaw=spec['yaw']*envelope*(np.sin(3*np.pi*phase) if name=='annoyed' else 1)
   delta=info['exp'].clone()
   edits.update_delta_new_smile(spec['smile']*envelope,delta)
   edits.update_delta_new_eyebrow(spec['brow']*envelope,delta)
   if name=='think':edits.update_delta_new_eyeball_direction(5*envelope,1.5*envelope,delta)
   blink=7*np.exp(-((phase-.33)/.028)**2)
   delta[0,11,1]+=blink*.001;delta[0,13,1]-=blink*.0003
   delta[0,15,1]+=blink*.001;delta[0,16,1]-=blink*.0003
   if name=='playful':edits.update_delta_new_wink(10*np.exp(-((phase-.58)/.07)**2),delta)
   rotation=get_rotation_matrix(info['pitch']+pitch,info['yaw']+yaw,info['roll']+spec['roll']*envelope)
   driven=info['scale'][...,None]*(info['kp']@rotation+delta)
   driven[:,:,:2]+=info['t'][:,None,:2]
   driven=model.stitching(kp,driven)
   face=model.parse_output(model.warp_decode(features,kp,driven)['out'])[0]
   full=paste_back(face,crop['M_c2o'],source[:,:,::-1],mask)[:,:,::-1]
   cv2.imwrite(str(frames/f'{i:05d}.png'),full)
   poses.append([pitch,yaw,spec['roll']*envelope])
  subprocess.run(['ffmpeg','-v','error','-y','-framerate','25','-i',str(frames/'%05d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(folder/'motion.mp4')],check=True)
  cv2.imwrite(str(folder/'poster.jpg'),cv2.imread(str(frames/'00050.png')))
  data={'id':name,**spec,'video':f'/assets/{name}/motion.mp4','poster':f'/assets/{name}/poster.jpg','fps':25,'frames':100,'duration':4,'render_s':round(time.monotonic()-start,2),'backend':'LivePortrait','scope':'facial expression and head motion, no new arm gestures','review':'generated; subjective evaluation required','pose_curves':poses}
  data['source_reference']='source.png' if generic else ('angry.png' if name=='annoyed' else 'neutral.png')
  data['source_sha256']=hashlib.sha256((source_path if generic else ROOT/'.cache/companion'/data['source_reference']).read_bytes()).hexdigest()
  (folder/'asset.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  (folder/'scene.json').write_text(json.dumps({'id':name,'motion_source':str(folder/'motion.mp4')},indent=2),encoding='utf-8')
  manifest=[a for a in manifest if a['id']!=name];manifest.append(data);print(name+' generated '+str(data['render_s'])+'s',flush=True)
 manifest.sort(key=lambda a:list(STATES).index(a['id']))
 (OUT/'manifest.json').write_text(json.dumps({'character':'uploaded' if generic else '小晴','source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),'repo_revision':'9b294b3d0536135442ea73cb01e6cb3ca7029dd3','assets':manifest},ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
