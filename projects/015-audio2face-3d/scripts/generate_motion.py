"""Generate actual half-body motion with the public official LTX-Video Space.

Sends the project's fictional AI portrait to Hugging Face. No credentials or
private personal photos are used. Outputs are model-generated silent videos.
"""
import argparse
import json
import shutil
import time
from pathlib import Path
from gradio_client import Client, handle_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/motion'
SOURCE=ROOT/'.cache/companion/neutral.png'
SPACE='https://lightricks-ltx-video-distilled.hf.space'
COMMON='A continuous photorealistic waist-up shot of the same adult woman from the input image, wearing a cream cardigan over a dusty rose top, seated in the same cozy room. Locked-off camera, constant framing and lighting. '
PROMPTS={
 'listen':COMMON+'She listens attentively to someone beside the camera, gently tilts her head, slowly nods once with a small forward movement of her shoulders and upper torso, then returns to a relaxed upright pose. Natural blinking, calm closed lips. Her body movement is visible but gentle. The lamp and background remain stationary.',
 'playful':COMMON+'She raises one eyebrow with a mischievous smile, gives a small visible shrug of both shoulders, tilts her head slightly to one side, then relaxes her shoulders and returns to center. Lips stay closed. Natural coordinated movement of head and shoulders, subtle breathing. The lamp and background remain stationary.',
 'annoyed':COMMON+'She briefly furrows her eyebrows and presses her lips in mild teasing annoyance, turns her head slightly away while shifting her shoulders, then looks back at the camera and relaxes into a small smile. Gentle upper-body movement, no speech. The lamp and background remain stationary.',
}
NEGATIVE='camera movement, zoom, pan, cuts, changing identity, distorted face, deformed body, extra limbs, waving hands, exaggerated motion, talking, open mouth, flicker, changing clothes, moving background, blurry'
REFINED={
 'listen':'Static camera. The woman gently tilts her head and nods once while listening attentively. Her shoulders move slightly with the nod. She then returns to her starting posture. Her hands stay resting in her lap throughout. Her lips remain closed. The background stays fixed.',
 'playful':'Static camera. The woman gives a small playful smile and a brief gentle shrug of her shoulders, then relaxes. Her hands stay resting in her lap throughout the video. Small natural movements, lips closed, same face and clothing. The background stays fixed.',
 'annoyed':'Static camera. The woman stops smiling, frowns with knitted eyebrows and pursed lips, and slowly turns her head a little to her left in mild annoyance. Her hands stay resting in her lap throughout. Her upper body remains seated. The background stays fixed.',
}

def generate(states,refine=False):
 OUT.mkdir(parents=True,exist_ok=True)
 client=Client(SPACE,download_files=str(OUT/'downloads'),verbose=False)
 for index,state in enumerate(states):
  folder=OUT/(state+'-v2' if refine else state);folder.mkdir(exist_ok=True)
  if (folder/'result.mp4').exists():print(state+' already generated',flush=True);continue
  info={'id':state,'source':'neutral.png','provider':SPACE,'space_revision':'8a42e93469c66b62d794b83a4233f5fc8439e2b5',
    'model':'LTX-Video 13B 0.9.8 distilled','prompt':REFINED[state] if refine else PROMPTS[state],'negative_prompt':NEGATIVE,
    'requested_width':512,'requested_height':768,'requested_duration':4,'seed':42+list(PROMPTS).index(state),'status':'submitted'}
  def save(): (folder/'generation.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
  save();start=time.monotonic();print('Submitting '+state,flush=True)
  try:
   info.update(guidance_scale=3 if refine else 1,multiscale=not refine);save()
   job=client.submit(prompt=info['prompt'],negative_prompt=NEGATIVE,input_image_filepath=handle_file(str(SOURCE)),
    input_video_filepath=None,height_ui=768,width_ui=512,mode='image-to-video',duration_ui=4,
    ui_frames_to_use=9,seed_ui=info['seed'],randomize_seed=False,ui_guidance_scale=info['guidance_scale'],improve_texture_flag=info['multiscale'],api_name='/image_to_video')
   last=''
   while not job.done():
    status=str(job.status().code)
    if status!=last:print(state+' '+status,flush=True);last=status
    if time.monotonic()-start>900:job.cancel();raise TimeoutError('Remote generation exceeded 15 minutes')
    time.sleep(3)
   result,seed=job.result()
   path=result['video'] if isinstance(result,dict) else result
   shutil.copyfile(path,folder/'result.mp4')
   info.update(status='done',elapsed_seconds=round(time.monotonic()-start,1),seed=seed)
   print(state+' completed in '+str(info['elapsed_seconds'])+' s',flush=True)
  except Exception as e:
   info.update(status='failed',error=str(e));save();print(state+' FAILED: '+str(e),flush=True);raise
  save()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('states',nargs='*',default=list(PROMPTS));parser.add_argument('--refine',action='store_true');args=parser.parse_args()
 if any(s not in PROMPTS for s in args.states):parser.error('states must be listen, playful, annoyed')
 generate(args.states,args.refine)
