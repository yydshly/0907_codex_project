"""Same audio/frame inputs: measured batching/layout speed and pixel differences."""
import json,time,gc
import numpy as np
import torch
from musetalk_complete import WEIGHTS,ROOT
from performance_jobs import ASSETS,JOBS,write

@torch.inference_mode()
def main():
 from accelerate import init_empty_weights
 from diffusers import UNet2DConditionModel
 from musetalk.models.vae import VAE
 from musetalk.models.unet import PositionalEncoding
 from musetalk.utils.audio_processor import AudioProcessor
 from transformers import WhisperModel
 with init_empty_weights():unet=UNet2DConditionModel.from_config(json.loads((WEIGHTS/'unet/config.json').read_text()))
 unet.load_state_dict(torch.load(str(WEIGHTS/'unet/unet.pth'),map_location='cpu',mmap=True,weights_only=True),assign=True)
 unet.to(device='cuda',dtype=torch.float16).eval();vae=VAE(str(WEIGHTS/'vae'),use_float16=True);pe=PositionalEncoding().cuda().half()
 processor=AudioProcessor(str(WEIGHTS/'whisper'));whisper=WhisperModel.from_pretrained(str(WEIGHTS/'whisper')).cpu().eval()
 features,length=processor.get_audio_feature(str(JOBS/'ec6bfbcc5edc445da2f2157103b21781/audio.wav'))
 chunks=pe(processor.get_whisper_chunk(features,'cpu',torch.float32,whisper,length,fps=25).cuda().half())[8:40]
 latents=torch.load(str(ASSETS/'comfort/latents.pt'),weights_only=True).cuda()[8:40]
 dest=ROOT/'.cache/inference-benchmark';dest.mkdir(exist_ok=True)
 baseline=None;report=[];zero=torch.tensor([0],device='cuda')
 for name,batch,layout in [('original',4,False),('batch8',8,False),('channels_last4',4,True),('channels_last8',8,True),('channels_last16',16,True)]:
  try:
   memory_format=torch.channels_last if layout else torch.contiguous_format
   unet.to(memory_format=memory_format);vae.vae.to(memory_format=memory_format);inputs=latents.contiguous(memory_format=memory_format)
   torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats()
   # Warm the specific shape; do not include startup in steady-state measurements.
   pred=unet(inputs[:batch],zero,encoder_hidden_states=chunks[:batch]).sample;vae.decode_latents(pred);torch.cuda.synchronize()
   runs=[];result=None
   for repeat in range(2):
    unet_s=0;decode_s=0;out=[];start=time.monotonic()
    for i in range(0,len(inputs),batch):
     tick=time.monotonic();pred=unet(inputs[i:i+batch],zero,encoder_hidden_states=chunks[i:i+batch]).sample;torch.cuda.synchronize();unet_s+=time.monotonic()-tick
     tick=time.monotonic();out.extend(vae.decode_latents(pred));torch.cuda.synchronize();decode_s+=time.monotonic()-tick
    result=np.array(out);runs.append({'total_s':round(time.monotonic()-start,4),'unet_s':round(unet_s,4),'decode_s':round(decode_s,4)})
   if baseline is None:baseline=result
   difference=np.abs(result.astype(np.int16)-baseline.astype(np.int16))
   item={'name':name,'batch':batch,'channels_last':layout,'frames':len(inputs),'runs':runs,'pixel_mae':float(difference.mean()),'pixel_p99':float(np.percentile(difference,99)),'pixel_max':int(difference.max()),'peak_mb':round(torch.cuda.max_memory_allocated()/1024**2,1)}
   np.save(dest/(name+'.npy'),result);report.append(item);print(json.dumps(item),flush=True)
  except torch.cuda.OutOfMemoryError:
   report.append({'name':name,'error':'CUDA OOM'});gc.collect();torch.cuda.empty_cache();print(name+' OOM',flush=True)
 write(ROOT/'notes/avatar-inference-benchmark.json',{'source_job':'ec6bfbcc5edc445da2f2157103b21781','results':report})

if __name__=='__main__':main()
