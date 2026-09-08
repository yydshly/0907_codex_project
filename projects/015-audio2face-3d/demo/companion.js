const $=s=>document.querySelector(s), video=$('#character'), stage=$('.stage');
const scenarios={neutral:['☀','我回来了','温柔欢迎 · 放慢一点'],playful:['✧','我昨晚又熬夜了','调皮一下 · 被她发现了'],angry:['☁','你是不是生气了？','假装生气 · 带一点小脾气'],comfort:['♡','今天真的好累','安慰陪伴 · 听你慢慢说']};
let current=null, clips=[], playToken=0, jobTimer=null;
function selectTab(create){$('#scenes').hidden=create;$('#create').hidden=!create;$('#scenes-tab').setAttribute('aria-selected',!create);$('#create-tab').setAttribute('aria-selected',create);}
$('#scenes-tab').onclick=()=>selectTab(false);$('#create-tab').onclick=()=>selectTab(true);
function stop(){playToken++;video.pause();$('#preview-audio').pause();stage.classList.remove('playing');$('#state-label').textContent='在听你说';$('#time').textContent='已停止';}
async function play(clip){
 const token=++playToken;video.pause();$('#preview-audio').pause();current=clip;
 $('#portrait').src=clip.poster;$('#reply').textContent=clip.text;$('#subtitle').textContent=clip.text;
 $('#state-label').textContent=clip.name||'新台词';$('#replay').disabled=false;
 $('#download').href=clip.video;$('#download').hidden=false;
 document.querySelectorAll('.scene').forEach(b=>{const active=b.dataset.id===clip.id;b.classList.toggle('active',active);b.setAttribute('aria-pressed',active);});
 video.src=clip.video;video.load();
 try{await video.play();if(token!==playToken)return;stage.classList.add('playing');}
 catch(e){if(token===playToken){stage.classList.remove('playing');$('#time').textContent=e.name==='NotAllowedError'?'请点重播开启声音':'播放失败，请重试';}}
}
$('#stop').onclick=stop;$('#replay').onclick=()=>current&&play(current);$('#focus').onclick=()=>{document.body.classList.toggle('focus');$('#focus').textContent=document.body.classList.contains('focus')?'返回完整视图 ↙':'陪伴视图 ↗';};
video.ontimeupdate=()=>{if(!video.paused)$('#time').textContent=`${video.currentTime.toFixed(1)} / ${video.duration.toFixed(1)} s`;};
video.onended=()=>{stage.classList.remove('playing');$('#state-label').textContent='等你回应';$('#time').textContent='播放完毕';};
async function refresh(){
 const response=await fetch('/api/status');if(!response.ok)throw Error('服务暂时不可用');const data=await response.json();clips=data.clips;
 const list=$('#scene-list');list.replaceChildren();
 for(const id of Object.keys(scenarios)){
  const clip=clips.find(c=>c.id===id),[emoji,prompt,label]=scenarios[id];const button=document.createElement('button');button.className='scene';button.dataset.id=id;button.disabled=!clip;button.setAttribute('aria-pressed','false');
  const icon=document.createElement('span');icon.className='emoji';icon.textContent=emoji;
  const copy=document.createElement('span'),title=document.createElement('strong'),small=document.createElement('small');title.textContent=prompt;small.textContent=clip?label:'片段生成中…';copy.append(title,small);
  const arrow=document.createElement('span');arrow.className='arrow';arrow.textContent='↗';button.append(icon,copy,arrow);button.onclick=()=>play(clip);list.append(button);
 }
 const mm=$('#provider option[value=minimax]');mm.disabled=!data.minimax_ready;mm.textContent=data.minimax_ready?'MiniMax · 已配置':'MiniMax · 未配置';
 $('#technical').textContent=clips.length?`${clips.length} 段已就绪 · 512 × 768 · 25 fps。单段离线渲染 ${Math.min(...clips.map(c=>c.render_seconds)).toFixed(0)}–${Math.max(...clips.map(c=>c.render_seconds)).toFixed(0)} 秒。`:'正在生成示例片段。';
 if(clips.length<4)setTimeout(()=>refresh().catch(()=>{}),5000);
}
$('#generate').onclick=async()=>{
 const text=$('#script').value.trim();if(!text){$('#job-status').textContent='请先输入台词';return;}
 const button=$('#generate');button.disabled=true;$('#audio-ready').hidden=true;const start=Date.now();let audioShown=false;
 try{
  const r=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,state:$('#emotion').value,provider:$('#provider').value})});const job=await r.json();if(!r.ok)throw Error(job.error);
  $('#job-status').textContent='正在准备新台词…';
  const poll=async()=>{
   try{const response=await fetch(`/api/jobs/${job.id}`);const item=await response.json();if(!response.ok)throw Error(item.error);
    $('#job-status').textContent=`${item.message} · ${Math.round((Date.now()-start)/1000)} 秒`;
    if(item.audio&&!audioShown){audioShown=true;$('#preview-audio').src=item.audio;$('#audio-ready').hidden=false;}
    if(item.status==='done'){button.disabled=false;current={...item,name:'自定义台词'};$('#reply').textContent=item.text;$('#replay').disabled=false;$('#download').href=item.video;$('#download').hidden=false;$('#job-status').textContent=`完成，用时 ${item.seconds} 秒。点击人物下方「重播」查看。`;return;}
    if(item.status==='failed')throw Error(item.message);jobTimer=setTimeout(poll,1800);
   }catch(e){button.disabled=false;$('#job-status').textContent=e.message;}
  };await poll();
 }catch(e){button.disabled=false;$('#job-status').textContent=e.message;}
};
refresh().catch(e=>{$('#scene-list').textContent=e.message;});
