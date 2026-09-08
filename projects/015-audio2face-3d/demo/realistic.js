'use strict';
const $ = id => document.getElementById(id);
const audio = $('audio');
const state = {sample:'hello',emotion:'neutral',clip:null,serial:0,lastFrame:-1,peaks:[],service:false,custom:null,busy:false};
const texts = {hello:'你好，欢迎来到语音驱动面部动画实验室。看，我的嘴型正在跟着声音变化。',phonemes:'爸爸，妈妈。你好，世界。乌云，微笑。我们一起，慢慢说话。'};
const renderer = new THREE.WebGLRenderer({canvas:$('face'),antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(30,1,.1,350);camera.position.set(0,155,58);
const orbit=new OrbitControls(camera,$('face'));orbit.target.set(0,153.5,1);orbit.enablePan=false;orbit.enableDamping=true;orbit.minDistance=32;orbit.maxDistance=105;orbit.minPolarAngle=.65;orbit.maxPolarAngle=2.1;
scene.add(new THREE.HemisphereLight(0xfff5eb,0x54464c,1.8));
function light(color,power,x,y,z){const l=new THREE.DirectionalLight(color,power);l.position.set(x,y,z);l.target.position.set(0,151,0);scene.add(l,l.target);return l;}
const key=light(0xffeee0,3.5,-25,183,40);
key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-28,right:28,top:28,bottom:-28,near:1,far:150});key.shadow.normalBias=.045;key.shadow.bias=-.0001;key.shadow.radius=3;
light(0xdce9ff,1.7,30,155,25);light(0xffce9a,4,15,175,-30);
const actors=[];
const jawUniform={value:0};
function bindJaw(material){material.onBeforeCompile=shader=>{
 shader.uniforms.jawAngle=jawUniform;
 shader.vertexShader='uniform float jawAngle; attribute float jawWeight; vec3 jawRotate(vec3 v){float c=cos(jawAngle),s=sin(jawAngle);return vec3(v.x,c*v.y-s*v.z,s*v.y+c*v.z);}\n'+shader.vertexShader;
 shader.vertexShader=shader.vertexShader.replace('#include <morphtarget_vertex>','#include <morphtarget_vertex>\nvec3 jawPivot=vec3(.0414,150.3755,-.0235); transformed=mix(transformed,jawRotate(transformed-jawPivot)+jawPivot,jawWeight);');
 shader.vertexShader=shader.vertexShader.replace('#include <morphnormal_vertex>','#include <morphnormal_vertex>\nobjectNormal=mix(objectNormal,jawRotate(objectNormal),jawWeight);');
};material.customProgramCacheKey=()=> 'camila-jaw-v1';}
const textureLoader=new THREE.TextureLoader();const textureCache=new Map();
async function get(url,type='json'){const r=await fetch(url);if(!r.ok)throw new Error('资源加载失败：'+url);return type==='bin'?r.arrayBuffer():r.json();}
async function texture(name,color=false){if(!name)return null;const id=name+color;if(!textureCache.has(id))textureCache.set(id,textureLoader.loadAsync('/character/'+name).then(t=>{if(color)t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;t.wrapS=t.wrapT=THREE.RepeatWrapping;return t;}));return textureCache.get(id);}
async function geometry(){
 const character=await get('/character/character.json');
 await Promise.all(character.meshes.map(async part=>{
  const base='/character/'+part.name;
  const [p,u,i,m,jaw,diffuse,normal,opacity]=await Promise.all([get(base+'.position.bin','bin'),get(base+'.uv.bin','bin'),get(base+'.index.bin','bin'),get(base+'.morph.bin','bin'),get(base+'.jaw.bin','bin'),texture(part.textures.Diffuse,true),texture(part.textures.Normal),texture(part.textures.Opacity)]);
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(p),3));g.setAttribute('uv',new THREE.BufferAttribute(new Float32Array(u),2));g.setIndex(new THREE.BufferAttribute(new Uint32Array(i),1));g.computeVertexNormals();g.setAttribute('jawWeight',new THREE.BufferAttribute(new Float32Array(jaw),1));
  const data=new Float32Array(m);if(part.morphs.length)g.morphAttributes.position=part.morphs.map((id,j)=>new THREE.BufferAttribute(data.slice(j*part.vertices*3,(j+1)*part.vertices*3),3));g.morphTargetsRelative=true;
  const hair=/Hair|Scalp|Brow|Eyelash/.test(part.name),eye=/Eye_|Cornea/.test(part.name),skin=/Skin/.test(part.name);
  const material=new THREE.MeshPhysicalMaterial({map:diffuse,normalMap:normal,normalScale:new THREE.Vector2(.4,.4),color:hair?0x604331:0xffffff,roughness:hair?.68:eye?.2:skin?.6:.55,metalness:0,side:THREE.DoubleSide,alphaMap:opacity,alphaTest:opacity?.2:0,alphaToCoverage:!!opacity,clearcoat:eye?.35:skin?.08:0,clearcoatRoughness:.35,sheen:skin?.18:0,sheenColor:new THREE.Color(0xffc2a7)});
  if(part.jaw)bindJaw(material);const mesh=new THREE.Mesh(g,material);if(part.jaw){mesh.customDepthMaterial=new THREE.MeshDepthMaterial({depthPacking:THREE.RGBADepthPacking,map:diffuse,alphaMap:opacity,alphaTest:opacity?.32:0});bindJaw(mesh.customDepthMaterial);}mesh.frustumCulled=false;mesh.castShadow=!eye;mesh.receiveShadow=!eye;if(eye){mesh.position.z=0;material.normalMap=null;material.emissiveMap=diffuse;material.emissive.set(0xffffff);material.emissiveIntensity=.16;}if(part.name.includes('Cornea')){material.map=null;material.color.set(0xffffff);material.transparent=true;material.opacity=.06;material.depthWrite=false;material.roughness=.08;material.emissiveIntensity=0;}if(part.name==='Std_Upper_Teeth')mesh.position.y=-.4;mesh.userData.channels=part.morphs;actors.push(mesh);scene.add(mesh);
 }));
}
function pose(time,force=false){
 if(!state.clip)return;const meta=state.clip.meta;
 const at=Math.min(meta.frames-1,Math.max(0,time*meta.fps));const frame=Math.floor(at);const next=Math.min(frame+1,meta.frames-1),mix=at-frame;jawUniform.value=(meta.weights[frame][17]*(1-mix)+meta.weights[next][17]*mix)*Math.PI/6;
 const phase=(performance.now()/1000)%4.7;const blink=phase<.18?Math.sin(Math.PI*phase/.18):0;for(const mesh of actors){if(!mesh.morphTargetInfluences)continue;mesh.userData.channels.forEach((id,j)=>{mesh.morphTargetInfluences[j]=meta.weights[frame][id]*(1-mix)+meta.weights[next][id]*mix;if(id===0||id===7)mesh.morphTargetInfluences[j]=Math.max(mesh.morphTargetInfluences[j],blink);});}
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
  const meta=await get(url);if(serial!==state.serial)return;
  state.clip={meta};state.lastFrame=-1;audio.src=base+meta.audio_file;audio.playbackRate=+$('speed').value;audio.load();
  $('frames').textContent=meta.frames;$('infer').textContent=meta.inference_seconds.toFixed(2)+'s';$('stage-status').textContent='真实模型输出 · '+({neutral:'平静',joy:'喜悦',anger:'生气'}[meta.emotion]||meta.emotion);
  $('play').disabled=false;$('seek').disabled=false;$('loading').hidden=true;pose(0,true);$('play').textContent='▶';$('seek').value=0;$('time').textContent='0:00 / '+stamp(meta.duration);
  makeWave(audio.src,serial).catch(()=>{state.peaks=[];wave();});
 }catch(e){if(serial!==state.serial)return;$('loading').textContent=e.message;$('stage-status').textContent='载入失败';}
}
async function select(){
 document.querySelectorAll('[data-sample]').forEach(b=>{const yes=!state.custom&&b.dataset.sample===state.sample;b.classList.toggle('active',yes);b.setAttribute('aria-pressed',yes);});
 document.querySelectorAll('[data-emotion]').forEach(b=>{const yes=b.dataset.emotion===state.emotion;b.classList.toggle('active',yes);b.setAttribute('aria-pressed',yes);});
 if(state.custom){await generateCustom();return;}
 $('transcript').textContent=texts[state.sample];if(state.service)$('upload-status').textContent='音频仅发送到本机服务。';await loadClip('/character/'+state.sample+'-'+state.emotion+'.json');
}
document.querySelectorAll('[data-sample]').forEach(b=>b.onclick=()=>{if(state.busy)return;state.custom=null;state.sample=b.dataset.sample;select();});
document.querySelectorAll('[data-emotion]').forEach(b=>b.onclick=()=>{if(state.busy)return;state.emotion=b.dataset.emotion;select();});
$('play').onclick=async()=>{if(audio.paused){try{await audio.play();}catch(e){$('stage-status').textContent='声音播放失败，请重新选择样例';}}else audio.pause();};
audio.addEventListener('play',()=>{$('play').textContent='Ⅱ';$('play').setAttribute('aria-label','暂停语音与动画');});
audio.addEventListener('pause',()=>{$('play').textContent='▶';$('play').setAttribute('aria-label','播放语音与动画');});
$('seek').oninput=()=>{if(Number.isFinite(audio.duration)){audio.currentTime=+$('seek').value*audio.duration;pose(audio.currentTime,true);wave();}};
$('speed').onchange=()=>{audio.playbackRate=+$('speed').value;};
$('front').onclick=()=>{camera.position.set(0,155,58);orbit.target.set(0,153.5,1);orbit.update();};
$('side').onclick=()=>{camera.position.set(39,155,52);orbit.target.set(0,153.5,1);orbit.update();};
$('wire').onclick=()=>{const on=!actors[0].material.wireframe;actors.forEach(m=>m.material.wireframe=on);$('wire').classList.toggle('active',on);$('wire').setAttribute('aria-pressed',on);};
new ResizeObserver(()=>{const w=$('stage').clientWidth,h=$('stage').clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();wave();}).observe($('stage'));
function animate(){requestAnimationFrame(animate);orbit.update();pose(audio.currentTime);renderer.render(scene,camera);if(state.clip){$('time').textContent=stamp(audio.currentTime)+' / '+stamp(state.clip.meta.duration);if(Number.isFinite(audio.duration))$('seek').value=audio.currentTime/audio.duration;wave();}}
async function checkService(){
 try{if(!['127.0.0.1','localhost'].includes(location.hostname)||!['/','/index.html','/realistic.html'].includes(location.pathname))throw new Error();const r=await fetch('/api/status');if(!r.ok)throw new Error();const s=await r.json();state.service=s.ready;$('service-dot').textContent=s.ready?'本机已就绪':'初始化中';if(!s.ready)throw new Error();}
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
 try{const r=await fetch('/api/generate?emotion='+state.emotion,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:state.custom.pcm.buffer});const result=await r.json();if(!r.ok)throw new Error(result.error||'生成失败');$('transcript').textContent='自定义录音：'+state.custom.name;$('upload-status').textContent='已生成 · 录音只在本机处理。点击播放查看结果。';await loadClip(result.camila_url,result.base);}
 catch(e){$('upload-status').textContent='未生成：'+e.message;$('loading').hidden=true;$('play').disabled=!state.clip;$('seek').disabled=!state.clip;}
 finally{state.busy=false;$('upload').disabled=false;document.querySelectorAll('[data-sample],[data-emotion]').forEach(b=>b.disabled=false);}
}
geometry().then(select).then(()=>{animate();checkService();}).catch(e=>{$('loading').textContent='三维资源无法加载：'+e.message;});
