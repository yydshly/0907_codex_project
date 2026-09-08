'use strict';
const $ = id => document.getElementById(id);
const audio = $('audio');
const state = {sample:'hello',emotion:'neutral',clip:null,serial:0,lastFrame:-1,peaks:[],service:false,custom:null,busy:false};
const texts = {hello:'你好，欢迎来到语音驱动面部动画实验室。看，我的嘴型正在跟着声音变化。',phonemes:'爸爸，妈妈。你好，世界。乌云，微笑。我们一起，慢慢说话。'};
const renderer = new THREE.WebGLRenderer({canvas:$('face'),antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.25;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(32,1,.1,300);
camera.position.set(0,157,65);
const orbit = new OrbitControls(camera,$('face'));
orbit.target.set(0,154,0);orbit.enablePan=false;orbit.minDistance=25;orbit.maxDistance=95;orbit.maxPolarAngle=Math.PI*.73;orbit.minPolarAngle=Math.PI*.2;orbit.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xe5f3df,0x152e2a,2));
const key = new THREE.DirectionalLight(0xf3eddc,3);key.position.set(-25,180,38);scene.add(key);
const fill = new THREE.DirectionalLight(0x8ec8b8,1.6);fill.position.set(28,155,20);scene.add(fill);
const rim = new THREE.DirectionalLight(0xe5f599,3);rim.position.set(12,167,-25);scene.add(rim);
const material = new THREE.MeshStandardMaterial({color:0xaaa99a,roughness:.62,metalness:.08,side:THREE.DoubleSide});
const skinGeometry = new THREE.BufferGeometry();
const skin = new THREE.Mesh(skinGeometry,material);scene.add(skin);
let positions;
async function get(url,type='json') {const r=await fetch(url);if(!r.ok)throw new Error('资源加载失败：'+url);return type==='bin'?r.arrayBuffer():r.json();}
async function geometry(){
 const list=await get('assets/geometry.json');
 for(const part of list){
  const [v,i]=await Promise.all([get('assets/'+part.name+'.vertices.bin','bin'),get('assets/'+part.name+'.indices.bin','bin')]);
  const g=part.name==='skin'?skinGeometry:new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(v),3));g.setIndex(new THREE.BufferAttribute(new Uint32Array(i),1));g.computeVertexNormals();
  if(part.name==='skin'){positions=g.attributes.position.array;g.attributes.position.setUsage(THREE.DynamicDrawUsage);}
  else{const lens=part.name.includes('lens');scene.add(new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:lens?0x151e19:0xddddc5,roughness:lens?.19:.4,metalness:0})));}
 }
}
function parseClip(buffer,meta){
 const n=meta.vertices*3,k=meta.rank;let offset=0;
 const mean=new Float32Array(buffer,offset,n);offset+=n*4;
 const scales=new Float32Array(buffer,offset,k);offset+=k*4;
 const basis=new Int16Array(buffer,offset,n*k);offset+=n*k*2;
 const weights=new Float32Array(buffer,offset,meta.frames*k);
 if(offset+weights.byteLength!==buffer.byteLength)throw new Error('动画文件长度不一致');
 return {mean,scales,basis,weights,meta};
}
function pose(time,force=false){
 if(!state.clip||!positions)return;
 const c=state.clip,frame=Math.min(c.meta.frames-1,Math.max(0,Math.round(time*c.meta.fps)));
 if(!force&&state.lastFrame===frame)return;state.lastFrame=frame;
 positions.set(c.mean);const n=positions.length,k=c.meta.rank;
 for(let j=0;j<k;j++){const w=c.weights[frame*k+j]*c.scales[j],ofs=j*n;for(let p=0;p<n;p++)positions[p]+=c.basis[ofs+p]*w;}
 skinGeometry.attributes.position.needsUpdate=true;skinGeometry.computeVertexNormals();
 // Positions remain in the coordinate system of the official Maya scene.
 if(force){skinGeometry.computeBoundingSphere();skinGeometry.computeBoundingBox();}
}
function stamp(t){if(!Number.isFinite(t))return '0:00';return Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0');}
function wave(){
 const canvas=$('wave'),dpr=Math.min(devicePixelRatio,2),rect=canvas.getBoundingClientRect();
 if(canvas.width!==Math.round(rect.width*dpr)||canvas.height!==Math.round(rect.height*dpr)){canvas.width=Math.round(rect.width*dpr);canvas.height=Math.round(rect.height*dpr);}
 const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height,progress=audio.duration?audio.currentTime/audio.duration:0;ctx.clearRect(0,0,w,h);
 const count=Math.max(1,Math.floor(w/(4*dpr)));
 for(let i=0;i<count;i++){const p=state.peaks[Math.floor(i/count*state.peaks.length)]||.035,bar=Math.max(2*dpr,p*h*.9);ctx.fillStyle=i/count<=progress?'#d9f18c':'#435347';ctx.fillRect(i/count*w,(h-bar)/2,2*dpr,bar);}
 ctx.fillStyle='#eff9d2';ctx.fillRect(progress*w,0,1*dpr,h);
}
async function makeWave(url,serial){
 const context=new AudioContext();
 try {const b=await get(url,'bin'),decoded=await context.decodeAudioData(b);if(serial!==state.serial)return;const a=decoded.getChannelData(0),peaks=[];for(let i=0;i<180;i++){let peak=0;for(let j=Math.floor(i*a.length/180);j<(i+1)*a.length/180;j++)peak=Math.max(peak,Math.abs(a[j]));peaks.push(peak);}const max=Math.max(...peaks,.001);state.peaks=peaks.map(p=>p/max);wave();}finally{await context.close();}
}
async function loadClip(url,base='assets/'){
 const serial=++state.serial;audio.pause();$('play').disabled=true;$('seek').disabled=true;$('loading').hidden=false;$('loading').textContent='正在加载真实动画数据…';
 try{
  const meta=await get(url),buffer=await get(base+meta.motion_file,'bin');if(serial!==state.serial)return;
  state.clip=parseClip(buffer,meta);state.lastFrame=-1;audio.src=base+meta.audio_file;audio.playbackRate=+$('speed').value;audio.load();
  $('frames').textContent=meta.frames;$('infer').textContent=meta.inference_seconds.toFixed(2)+'s';$('stage-status').textContent='真实模型输出 · '+({neutral:'平静',joy:'喜悦',anger:'生气'}[meta.emotion]||meta.emotion);
  $('play').disabled=false;$('seek').disabled=false;$('loading').hidden=true;pose(0,true);$('play').textContent='▶';$('seek').value=0;$('time').textContent='0:00 / '+stamp(meta.duration);
  makeWave(audio.src,serial).catch(()=>{state.peaks=[];wave();});
 }catch(e){if(serial!==state.serial)return;$('loading').textContent=e.message;$('stage-status').textContent='载入失败';}
}
async function select(){
 document.querySelectorAll('[data-sample]').forEach(b=>{const yes=!state.custom&&b.dataset.sample===state.sample;b.classList.toggle('active',yes);b.setAttribute('aria-pressed',yes);});
 document.querySelectorAll('[data-emotion]').forEach(b=>{const yes=b.dataset.emotion===state.emotion;b.classList.toggle('active',yes);b.setAttribute('aria-pressed',yes);});
 if(state.custom){await generateCustom();return;}
 $('transcript').textContent=texts[state.sample];if(state.service)$('upload-status').textContent='音频仅发送到本机服务。';await loadClip('assets/'+state.sample+'-'+state.emotion+'.json');
}
document.querySelectorAll('[data-sample]').forEach(b=>b.onclick=()=>{if(state.busy)return;state.custom=null;state.sample=b.dataset.sample;select();});
document.querySelectorAll('[data-emotion]').forEach(b=>b.onclick=()=>{if(state.busy)return;state.emotion=b.dataset.emotion;select();});
$('play').onclick=async()=>{if(audio.paused){try{await audio.play();}catch(e){$('stage-status').textContent='声音播放失败，请重新选择样例';}}else audio.pause();};
audio.addEventListener('play',()=>{$('play').textContent='Ⅱ';$('play').setAttribute('aria-label','暂停语音与动画');});
audio.addEventListener('pause',()=>{$('play').textContent='▶';$('play').setAttribute('aria-label','播放语音与动画');});
$('seek').oninput=()=>{if(Number.isFinite(audio.duration)){audio.currentTime=+$('seek').value*audio.duration;pose(audio.currentTime,true);wave();}};
$('speed').onchange=()=>{audio.playbackRate=+$('speed').value;};
$('front').onclick=()=>{camera.position.set(0,157,65);orbit.target.set(0,154,0);orbit.update();};
$('side').onclick=()=>{camera.position.set(48,157,40);orbit.target.set(0,154,0);orbit.update();};
$('wire').onclick=()=>{material.wireframe=!material.wireframe;$('wire').classList.toggle('active',material.wireframe);$('wire').setAttribute('aria-pressed',material.wireframe);};
new ResizeObserver(()=>{const w=$('stage').clientWidth,h=$('stage').clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();wave();}).observe($('stage'));
function animate(){requestAnimationFrame(animate);orbit.update();pose(audio.currentTime);renderer.render(scene,camera);if(state.clip){$('time').textContent=stamp(audio.currentTime)+' / '+stamp(state.clip.meta.duration);if(Number.isFinite(audio.duration))$('seek').value=audio.currentTime/audio.duration;wave();}}
async function checkService(){
 try{if(!['127.0.0.1','localhost'].includes(location.hostname)||!['/','/index.html','/mark.html'].includes(location.pathname))throw new Error();const r=await fetch('/api/status');if(!r.ok)throw new Error();const s=await r.json();state.service=s.ready;$('service-dot').textContent=s.ready?'本机已就绪':'初始化中';if(!s.ready)throw new Error();}
 catch{$('service-dot').textContent='需本机服务';$('upload-status').textContent='此页面可播放样例。上传生成需使用项目提供的启动脚本打开本地服务。';$('upload').disabled=true;document.querySelector('.upload-button').classList.add('disabled');}
}
$('upload').onchange=async event=>{
 if(!state.service||state.busy)return;const file=event.target.files[0];if(!file)return;
 if(file.size>20*1024*1024){$('upload-status').textContent='文件过大，请选择 20MB 以下的短录音。';return;}
 const context=new AudioContext({sampleRate:16000});
 try{const decoded=await context.decodeAudioData(await file.arrayBuffer());if(decoded.duration>20||decoded.duration<.25)throw new Error('请使用 0.25–20 秒的录音。');
  const pcm=new Float32Array(decoded.length);for(let channel=0;channel<decoded.numberOfChannels;channel++){const data=decoded.getChannelData(channel);for(let i=0;i<pcm.length;i++)pcm[i]+=data[i]/decoded.numberOfChannels;}
  state.custom={pcm,name:file.name};await select();
 }catch(e){$('upload-status').textContent='未生成：'+e.message;state.custom=null;}finally{await context.close();event.target.value='';}
};
async function generateCustom(){
 state.busy=true;audio.pause();$('upload').disabled=true;$('play').disabled=true;$('seek').disabled=true;document.querySelectorAll('[data-sample],[data-emotion]').forEach(b=>b.disabled=true);$('upload-status').textContent='正在本机运行官方模型，请稍候…';$('loading').hidden=false;$('loading').textContent='正在根据你的声音生成面部动画…';
 try{const r=await fetch('/api/generate?emotion='+state.emotion,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:state.custom.pcm.buffer});const result=await r.json();if(!r.ok)throw new Error(result.error||'生成失败');$('transcript').textContent='自定义录音：'+state.custom.name;$('upload-status').textContent='已生成 · 录音只在本机处理。点击播放查看结果。';await loadClip(result.url,result.base);}
 catch(e){$('upload-status').textContent='未生成：'+e.message;$('loading').hidden=true;$('play').disabled=!state.clip;$('seek').disabled=!state.clip;}
 finally{state.busy=false;$('upload').disabled=false;document.querySelectorAll('[data-sample],[data-emotion]').forEach(b=>b.disabled=false);}
}
geometry().then(select).then(()=>{animate();checkService();}).catch(e=>{$('loading').textContent='三维资源无法加载：'+e.message;});
