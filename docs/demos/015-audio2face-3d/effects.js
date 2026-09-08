'use strict';
const frame=document.querySelector('#three-frame');
const views={mark:'mark.html#lab'};
let currentView='mark';
function stopVideos(){document.querySelectorAll('video').forEach(v=>v.pause());}
function choosePanel(name){
 stopVideos();
 document.querySelectorAll('[data-panel]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.panel===name)));
 document.querySelector('#panel-video').hidden=name!=='video';
 document.querySelector('#panel-three').hidden=name!=='three';
 if(name==='three'){if(!frame.hasAttribute('src'))frame.src=views[currentView];}
 else frame.removeAttribute('src');
}
document.querySelectorAll('[data-panel]').forEach(b=>b.addEventListener('click',()=>choosePanel(b.dataset.panel)));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{
 currentView=b.dataset.view;frame.src=views[currentView];document.querySelector('#three-link').href=views[currentView];
 document.querySelectorAll('[data-view]').forEach(n=>n.setAttribute('aria-pressed',String(n===b)));
}));
document.querySelectorAll('video').forEach(v=>{
 v.addEventListener('play',()=>document.querySelectorAll('video').forEach(other=>{if(other!==v)other.pause();}));
 v.addEventListener('error',()=>{const p=document.createElement('p');p.className='small';p.textContent='此片段暂时无法载入，请使用下方入口查看，或检查本机服务是否启动。';v.closest('.card').querySelector('.card-body').prepend(p);},{once:true});
});
if(new URLSearchParams(location.search).get('view')==='3d')choosePanel('three');
