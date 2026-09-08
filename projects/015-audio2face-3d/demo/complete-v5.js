const $ = s => document.querySelector(s);
const actor=$('#actor'), idle=$('#idle'), stage=$('.stage');
const cover=document.createElement('canvas');cover.id='transition';cover.setAttribute('aria-hidden','true');stage.append(cover);
let clips=[],selected=null,mode='complete',queue=[],token=0,muted=false,operation=null;
const descriptions={complete:'播放优化版：开口前自然过渡，支持长停顿放松和同姿态打断。',before:'已保存基线：你认可的收尾修正版，原成片保留不变。',motion:'生成嘴型前的原始动作视频，没有音轨。',photo:'生成动作前的原始照片。'};
function state(value,label){stage.dataset.state=value;$('#state').textContent=label;}
function modes(){document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.mode===mode));$('#mode-description').textContent=descriptions[mode];}
function begin(){operation?.abort();operation=new AbortController();return {id:++token,signal:operation.signal};}
function current(op){return op.id===token&&!op.signal.aborted;}
function capture(){
 const source=stage.classList.contains('photo')?$('#still'):stage.classList.contains('active')?actor:idle;
 if(cover.classList.contains('visible'))return;
 const w=source.videoWidth||source.naturalWidth,h=source.videoHeight||source.naturalHeight;
 if(!w||!h)return;
 cover.width=w;cover.height=h;cover.getContext('2d').drawImage(source,0,0,w,h);cover.classList.add('visible');
}
function reveal(op){if(current(op))cover.classList.remove('visible');}
function event(element,name,op){
 return new Promise((resolve,reject)=>{
  let timer;
  const cleanup=()=>{clearTimeout(timer);element.removeEventListener(name,done);element.removeEventListener('error',failed);op.signal.removeEventListener('abort',abort);};
  const done=()=>{cleanup();resolve();};
  const failed=()=>{cleanup();reject(Error('媒体加载失败'));};
  const abort=()=>{cleanup();reject(new DOMException('Cancelled','AbortError'));};
  element.addEventListener(name,done,{once:true});element.addEventListener('error',failed,{once:true});op.signal.addEventListener('abort',abort,{once:true});
  timer=setTimeout(()=>{cleanup();reject(Error('媒体加载超时'));},12000);
  if(op.signal.aborted)abort();
 });
}
async function prepare(video,url,seek,op){
 video.pause();video.onended=null;
 const ready=event(video,'loadeddata',op);video.src=url;video.load();await ready;
 if(!current(op))return false;
 const time=Math.max(0,Math.min(seek,Math.max(0,video.duration-.04)));
 if(time>0){const positioned=event(video,'seeked',op);video.currentTime=time;await positioned;}
 return current(op);
}
function failure(e,op){if(!current(op)||e.name==='AbortError')return;state('error','暂时无法播放');$('#time').textContent=e.message;}
async function matchedIdle(clip,op){
 idle.loop=true;idle.muted=true;
 if(!await prepare(idle,clip.idle_video,0,op))return;
 await idle.play();if(!current(op))return;
 stage.classList.remove('active','photo');reveal(op);state('idle','等你回应');$('#time').textContent='播放完毕';
}
async function rest(){
 const wasPlaying=stage.classList.contains('active'),position=actor.currentTime;
 capture();const op=begin();actor.pause();idle.pause();queue=[];
 const clip=selected;mode='complete';modes();state('releasing','休息一下');$('#subtitle').textContent='播放已停止，随时可以再听一段。';$('#time').textContent='已停止';
 try{
  if(clip&&wasPlaying&&position<actor.duration-.08){
   // Resume the same source time instead of jumping to another head/hand pose.
   idle.loop=false;idle.muted=true;
   if(!await prepare(idle,clip.source_video,position,op))return;
   idle.onended=()=>{if(current(op))matchedIdle(clip,op).catch(e=>failure(e,op));};
   await idle.play();if(!current(op))return;
   stage.classList.remove('active','photo');reveal(op);state('idle','休息一下');
  }else if(clip){await matchedIdle(clip,op);}
  else{idle.loop=true;await idle.play();if(current(op)){stage.classList.remove('active','photo');reveal(op);state('idle','休息一下');}}
 }catch(e){failure(e,op);}
}
async function show(clip,seek=0){
 capture();const op=begin();selected=clip;actor.pause();idle.pause();
 $('#reply').textContent=clip.text;$('#subtitle').textContent=mode==='motion'?'原始动作 · 未添加语音与新嘴型':mode==='photo'?'原始照片 · 静态参考':clip.text;
 $('#replay').disabled=false;$('#download').href=clip.video;$('#download').hidden=false;
 document.querySelectorAll('.scene').forEach(b=>b.setAttribute('aria-pressed',b.dataset.id===clip.id));
 if(mode==='photo'){stage.classList.add('photo');reveal(op);state('photo','原始照片');return;}
 state('preparing','准备回应');actor.muted=mode==='motion'||muted;
 try{
  const url=mode==='complete'?clip.video:mode==='before'?clip.before_video:clip.source_video;
  if(!await prepare(actor,url,seek,op))return;
  actor.onended=async()=>{
   if(!current(op))return;
   if(queue.length){show(queue.shift());return;}
   capture();try{await matchedIdle(clip,op);}catch(e){failure(e,op);}
  };
  await actor.play();if(!current(op))return;
  stage.classList.remove('photo');stage.classList.add('active');reveal(op);state('speaking',clip.name);
 }catch(e){failure(e,op);}
}
$('#interrupt').onclick=rest;
$('#replay').onclick=()=>{queue=[];if(selected)show(selected);};
$('#play-all').onclick=()=>{if(!clips.length)return;mode='complete';modes();queue=clips.slice(1);show(clips[0]);};
$('#mute').onclick=()=>{muted=!muted;actor.muted=mode==='motion'||muted;$('#mute').textContent=muted?'声音关':'声音开';};
$('#focus').onclick=()=>{document.body.classList.toggle('focus');$('#focus').textContent=document.body.classList.contains('focus')?'返回完整视图 ↙':'陪伴视图 ↗';};
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{
 const seek=actor.ended?0:actor.currentTime;queue=[];mode=b.dataset.mode;modes();
 if(selected)show(selected,seek);
 else if(mode==='photo'){capture();const op=begin();idle.pause();stage.classList.add('photo');reveal(op);}
 else{stage.classList.remove('photo');idle.play().catch(()=>{});}
});
actor.ontimeupdate=()=>{if(!actor.paused)$('#time').textContent=`${actor.currentTime.toFixed(1)} / ${actor.duration.toFixed(1)} s`;};
async function init(){
 const r=await fetch('/api/complete');if(!r.ok)throw Error('完整效果服务连接失败');const data=await r.json();clips=data.clips;
 const list=$('#scenes');list.replaceChildren();
 for(const [i,clip] of clips.entries()){
  const b=document.createElement('button');b.className='scene';b.dataset.id=clip.id;b.setAttribute('aria-pressed','false');
  const icon=document.createElement('span');icon.className='icon';icon.textContent=['☀','✧','♡'][i]||'✧';
  const words=document.createElement('span'),title=document.createElement('strong'),line=document.createElement('small');title.textContent=clip.name;line.textContent=clip.text;words.append(title,line);
  const arrow=document.createElement('span');arrow.className='arrow';arrow.textContent='↗';b.append(icon,words,arrow);b.onclick=()=>{queue=[];show(clip);};list.append(b);
 }
 $('#play-all').disabled=!clips.length;
 $('#metrics').textContent=`${clips.length} 段预生成输出 · 长停顿策略阈值 0.6 秒，当前短停顿保留。`;
 if(data.montage){$('#montage').href=data.montage;$('#montage').hidden=false;}
}
init().catch(e=>$('#status').textContent=e.message);
