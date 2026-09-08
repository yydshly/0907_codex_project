const $=s=>document.querySelector(s),idle=$('#idle'),actor=$('#actor'),audio=$('#audio');
let session=null,active=null,epoch=0,poll=null,lastResult=null,configured=false,muted=false,mode='listen',replySeen=new Set(),submitting=false,playback=null,sessionLoading=true;
let selectedAvatar={id:'xiaoqing',name:'小晴',asset_base:'/assets'};
const names={listen:'倾听',think:'思考',comfort:'安慰',playful:'调皮',annoyed:'轻微不满',affirm:'肯定'};
async function api(path,data){const r=await fetch(path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const value=await r.json();if(!r.ok)throw Error(value.error||'请求失败');return value;}
function stage(state,phaseSeconds){actor.pause();actor.hidden=true;idle.hidden=false;if(mode!==state){mode=state;idle.src=selectedAvatar.asset_base+'/'+state+'/motion.mp4';}if(Number.isFinite(phaseSeconds)){const token=epoch;const seek=()=>{if(token!==epoch||mode!==state)return;idle.currentTime=phaseSeconds%(idle.duration||6);idle.play().catch(()=>{});};if(idle.readyState>=1)seek();else idle.addEventListener('loadedmetadata',seek,{once:true});}idle.play().catch(()=>{});$('#state').textContent=state==='think'?'正在准备回应':'我在听';}
function message(role,text,key){if(key&&replySeen.has(key))return;if(key)replySeen.add(key);$('#messages .empty')?.remove();const p=document.createElement('p');p.className='message '+role;const label=document.createElement('small');label.textContent=role==='user'?'你':'AI 伙伴';p.append(label,document.createTextNode(text));$('#messages').append(p);$('#messages').scrollTop=$('#messages').scrollHeight;}
function controls(){const busy=Boolean(active)||submitting||sessionLoading;$('#send').disabled=!configured||busy;$('#new-session').disabled=busy;document.querySelectorAll('.suggestions button').forEach(b=>b.disabled=!configured||busy);}
async function refresh(){const s=await api('/api/dialogue/status');configured=s.provider.configured&&s.worker.status==='ready';$('#setup').hidden=s.provider.configured;$('#connection').textContent=s.provider.configured?'MiniMax · 分段对话':'MiniMax · 待配置';$('#models').textContent='对话：'+s.provider.chat_model+'；语音：'+s.provider.speech_model+'。';if(!configured)$('#status').textContent=s.provider.configured?'人物模型正在准备…':'请先配置 MiniMax，再开始对话。';controls();return s;}
async function loadSession(key){session=key?await api('/api/dialogue/session/'+key):await api('/api/dialogue/session',{avatar_id:selectedAvatar.id});selectedAvatar=await api('/api/avatars/'+(session.avatar_id||'xiaoqing'));$('#avatar-label').textContent=selectedAvatar.name;$('#workbench-link').href='/?avatar='+selectedAvatar.id;$('#classic-link').hidden=selectedAvatar.id!=='xiaoqing';mode=null;stage('listen');sessionStorage.setItem('xiaoqing-dialogue',session.id);history.replaceState(null,'','/chat?session='+session.id);$('#messages').replaceChildren();replySeen=new Set();for(const m of session.messages)message(m.role,m.content,m.role==='assistant'?m.job:null);if(!session.messages.length){const p=document.createElement('p');p.className='empty';p.textContent='说一句，我会认真听。也可以在回应时打断我。';$('#messages').append(p);}}
function segments(item){return item.mode==='segmented'?(item.segments||[]):item.video?[item]:[];}
function timing(p){const item=p.item,first=p.firstPlay==null?'准备中':p.firstPlay.toFixed(1)+' 秒';$('#timing').textContent=(p.replay?'重播；':'本轮首句实际开播 '+first+'；')+'已播放 '+p.next+'/'+(item.segment_count||1)+' 句；句间等待 '+p.gaps.map(g=>g.toFixed(1)+' 秒').join('、')+(p.gaps.length?'':'暂无')+'。'+(item.metrics?'全部画面准备 '+item.metrics.total_s.toFixed(1)+' 秒。':'');$('#timing').dataset.measurement=JSON.stringify({job:item.id,replay:p.replay,first_play_s:p.firstPlay,gaps_s:p.gaps,played:p.next,complete:Boolean(p.finished)&&item.status==='done',status:item.status});}
function finishPlayback(p){if(playback!==p)return;p.finished=true;const tail=selectedAvatar.motion_backend==='minimax-body'?segments(p.item).at(-1):null;stage(tail?.state||'listen',tail?.motion_phase_end/25);$('#subtitle').textContent='我在听，你继续说。';$('#status').textContent=p.item.status==='failed'?p.item.message:'可以继续聊，或分享下一件小事。';timing(p);}
async function advance(p){
 if(playback!==p||p.token!==epoch||p.playing)return;
 const part=segments(p.item)[p.next];
 if(!part){if(p.terminal)finishPlayback(p);else{if(selectedAvatar.motion_backend==='minimax-body')stage('listen');$('#state').textContent='下一句正在准备';$('#status').textContent='后一句画面还在生成，你可以随时打断。';}return;}
 p.playing=true;audio.pause();idle.pause();idle.hidden=true;actor.hidden=false;actor.src=part.video;actor.muted=muted;
 $('#state').textContent=names[part.state]+' · 第 '+(p.next+1)+' 句';$('#subtitle').textContent=part.text;$('#result-controls').hidden=false;$('#download').hidden=false;$('#download').href=part.video;$('#download').textContent='下载当前片段';$('#play-ready').hidden=true;
 try{
  await actor.play();if(playback!==p||p.token!==epoch)return;
  const now=Date.now();if(p.firstPlay==null)p.firstPlay=(now/1000-p.item.submitted_at);
  if(p.endedAt!=null)p.gaps.push((now-p.endedAt)/1000);
  p.next++;timing(p);$('#status').textContent='她正在回应你，可以随时打断。';
 }catch{if(playback!==p)return;p.playing=false;$('#play-ready').hidden=false;$('#status').textContent='回应已准备好，点击播放。';}
}
actor.onended=()=>{const p=playback;if(!p||p.token!==epoch)return;p.playing=false;p.endedAt=Date.now();advance(p);};
function receive(item,token,replay=false){lastResult=item;$('#replay').disabled=segments(item).length===0;if(!playback||playback.item.id!==item.id||playback.token!==token)playback={item,token,next:0,playing:false,terminal:false,firstPlay:null,endedAt:null,gaps:[],replay};playback.item=item;playback.terminal=['done','failed','cancelled'].includes(item.status);advance(playback);}
async function watch(token){
 if(token!==epoch||!active)return;
 try{
  const item=await api('/api/jobs/'+active.id);if(token!==epoch)return;active=item;
  if(!playback?.playing)$('#status').textContent=item.message;$('#progress').value=item.progress||0;
  if(item.text)message('assistant',item.text,item.id);
  if(item.audio){if(audio.getAttribute('src')!==item.audio)audio.src=item.audio;$('#result-controls').hidden=false;$('#audio-only').hidden=false;}
  if(item.status==='cancelled'){playback=null;audio.pause();stage('listen');$('#subtitle').textContent='已打断，你继续说。';}else if(segments(item).length)receive(item,token);
  if(['done','failed','cancelled'].includes(item.status)){active=null;controls();if(!segments(item).length){stage('listen');$('#subtitle').textContent=item.message;$('#timing').textContent='本次没有完成声画回应。';$('#timing').dataset.measurement=JSON.stringify({job:item.id,status:item.status,complete:false,replay:false,first_play_s:null,gaps_s:[],played:0});}return;}
  poll=setTimeout(()=>watch(token),200);
 }catch(e){if(token!==epoch)return;$('#status').textContent='连接暂时中断，正在重试：'+e.message;poll=setTimeout(()=>watch(token),1000);}
}
async function send(text,event){
 if(!configured||active||submitting||sessionLoading||!text.trim())return;
 const token=++epoch;submitting=true;playback=null;controls();audio.pause();stage('think');$('#subtitle').textContent='听到了，给我一点时间。';$('#progress').value=0;$('#status').textContent='正在把这句话交给 MiniMax…';
 try{const item=await api('/api/dialogue/turn',{session:session.id,text,event,mode:'segmented'});if(token!==epoch){await api('/api/cancel/'+item.id,{});return;}message('user',text);$('#message').value='';active=item;$('#result-controls').hidden=true;$('#download').hidden=true;$('#audio-only').hidden=true;$('#replay').disabled=true;watch(token);}
 catch(e){if(token===epoch){stage('listen');$('#status').textContent=e.message;}}finally{submitting=false;controls();}
}
async function interrupt(){
 const item=active;++epoch;clearTimeout(poll);playback=null;audio.pause();stage('listen');$('#play-ready').hidden=true;$('#subtitle').textContent='好，我在听。';
 $('#replay').disabled=!lastResult||!segments(lastResult).length;if(!item){$('#status').textContent='已停声，可以继续说。';return;}
 active=null;submitting=true;controls();const start=performance.now();
 try{await api('/api/cancel/'+item.id,{});$('#status').textContent='已停声，正在让出生成资源…';const end=Date.now()+70000;let released=false;while(Date.now()<end){const s=await api('/api/dialogue/status');if(!s.busy){released=true;break;}await new Promise(r=>setTimeout(r,100));}$('#status').textContent=released?'已打断，可以继续说。':'后台仍在停止，请稍后重试。';$('#timing').textContent='本次打断至可继续提交：'+((performance.now()-start)/1000).toFixed(2)+' 秒。';}
 catch(e){$('#status').textContent=e.message;}finally{submitting=false;controls();}
}
$('#composer').onsubmit=e=>{e.preventDefault();send($('#message').value);};$('#message').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();send($('#message').value);}};
document.querySelectorAll('[data-text]').forEach(b=>b.onclick=()=>send(b.dataset.text));$('#task-done').onclick=()=>send('我刚完成了一个任务，想听你鼓励一下。','task_done');
$('#interrupt').onclick=interrupt;$('#new-session').onclick=async()=>{sessionLoading=true;controls();try{await interrupt();await loadSession(null);lastResult=null;$('#replay').disabled=true;$('#result-controls').hidden=true;$('#status').textContent='新对话已开始。';}catch(e){$('#status').textContent=e.message;}finally{sessionLoading=false;controls();}};$('#refresh-config').onclick=async()=>{await refresh();if(configured)$('#status').textContent='MiniMax 配置已就绪，可以开始聊。';};
$('#replay').onclick=async()=>{const item=lastResult;if(!item)return;await interrupt();receive({...item,status:'done',segment_count:segments(item).length},epoch,true);};$('#play-ready').onclick=()=>playback&&advance(playback);$('#audio-only').onclick=()=>{playback=null;stage('listen');$('#state').textContent='语音模式 · 画面为待机';audio.muted=muted;audio.play().catch(()=>{});};$('#mute').onclick=()=>{muted=!muted;actor.muted=muted;audio.muted=muted;$('#mute').textContent=muted?'声音关':'声音开';};
async function init(){await refresh();const params=new URLSearchParams(location.search);const avatarKey=params.get('avatar');if(avatarKey){selectedAvatar=await api('/api/avatars/'+avatarKey);if(selectedAvatar.status!=='ready')throw Error('这个人物尚未准备好，请到人物库查看进度。');}const key=avatarKey?null:(params.get('session')||sessionStorage.getItem('xiaoqing-dialogue'));try{await loadSession(key);}catch{await loadSession(null);}if(configured)$('#status').textContent='可以开始聊。第一句画面准备好就播放，后一句继续生成。';const keys=[...new Set(session.messages.slice().reverse().map(m=>m.job))].slice(0,12);for(const key of keys){try{const item=await api('/api/jobs/'+key);if(['done','failed'].includes(item.status)&&segments(item).length){lastResult=item;$('#replay').disabled=false;break;}if(['thinking','tts','queued','rendering'].includes(item.status)){active=item;stage('think');controls();watch(++epoch);break;}}catch{}}}

init().catch(e=>{configured=false;$('#status').textContent='连接失败：'+e.message;}).finally(()=>{sessionLoading=false;controls();});
