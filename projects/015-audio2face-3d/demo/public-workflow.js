const $=s=>document.querySelector(s);
fetch('experience-data.json').then(r=>{if(!r.ok)throw Error('素材清单无法加载');return r.json();}).then(people=>{
 if(document.body.dataset.preview==='characters'){
  $('#library-status').textContent='预设人物 · 可预览并进入对应对话页面';
  for(const p of people){const card=document.createElement('article');card.className='avatar-card';const video=document.createElement('video');video.src=p.motions[0].video;video.controls=true;video.muted=true;video.loop=true;video.playsInline=true;video.preload='metadata';const body=document.createElement('div');body.className='avatar-body';const name=document.createElement('h3');name.textContent=p.name;const link=document.createElement('a');link.className='use-avatar';link.href='chat.html?avatar='+encodeURIComponent(p.id);link.textContent='使用此人物查看对话页 →';body.append(name,link);card.append(video,body);$('#avatars').append(card);}
  $('#upload-form').onsubmit=e=>e.preventDefault();$('#incomplete').textContent='公开站不展示私人上传与准备记录。';
 }else{
  const p=people.find(x=>x.id===new URLSearchParams(location.search).get('avatar'))||people[0];$('#avatar-label').textContent=p.name;$('#idle').src=p.motions[0].video;$('#subtitle').textContent='界面留档 · 可播放已保存片段';$('#state').textContent='静态预览';
  const stop=()=>{$('#actor').pause();$('#actor').hidden=true;$('#idle').hidden=false;$('#state').textContent='静态预览';};
  const play=()=>{$('#idle').hidden=true;$('#actor').hidden=false;$('#actor').src=p.reply;$('#state').textContent='已保存片段';$('#actor').play().catch(()=>{$('#actor').controls=true;});$('#replay').disabled=false;};
  $('#preview-reply').onclick=play;$('#replay').onclick=play;$('#interrupt').onclick=stop;$('#actor').onended=stop;$('#mute').onclick=()=>{$('#actor').muted=!$('#actor').muted;$('#mute').textContent=$('#actor').muted?'声音关':'声音开';};$('#composer').onsubmit=e=>e.preventDefault();
 }
}).catch(e=>{const status=$('#status')||$('#library-status');status.textContent=e.message;});
