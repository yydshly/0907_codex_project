/* anyCreature produces GLB animation; this viewer adds a garden and travel. */
const $=id=>document.getElementById(id);
let catalog=[],variant='human',level=0,mode='color',animation='move',paused=false;
let model,mixer,bones,carrier,action,materials=[],ticket=0,routeTime=0,elapsed=0,seekFraction=0;
let scene,camera,renderer,controls,clock,garden,studio,target,distance=6,radius=1;
const shapeNames=['原始','结实','厚重'];
function active(selector,key,value){document.querySelectorAll(selector).forEach(b=>{const on=b.dataset[key]===value;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});}
function view(name='hero'){
 if(!camera||!target)return;
 const vectors={hero:[3,2.6,4],front:[0,1.2,4],side:[4,1.2,0],top:[0,4,.001]};
 camera.position.copy(target).add(new THREE.Vector3(...vectors[name]).normalize().multiplyScalar(distance));controls.target.copy(target);controls.update();active('[data-view]','view',name);
}
function fitScene(){
 if(!model)return;const habitat=$('environment').value==='garden';garden.visible=habitat;studio.visible=!habitat;
 target=habitat?new THREE.Vector3(0,.65,0):new THREE.Vector3(0,radius*.65,0);
 distance=(habitat?9.4:radius/Math.sin(camera.fov*Math.PI/360)*1.32)/Math.min(1,camera.aspect);
 controls.minDistance=habitat?3:radius;controls.maxDistance=distance*2;
 carrier.scale.setScalar(habitat&&variant==='butterfly'?.62:habitat?.7:1);
 routeTime=0;positionActor();view('hero');
}
function positionActor(){
 if(!carrier)return;const habitat=$('environment').value==='garden',travel=habitat&&$('travel').checked&&animation==='move';
 if(travel){const a=routeTime*(variant==='butterfly'?.7:variant==='snail'?.12:.28),r=variant==='butterfly'?1.55:1.4;carrier.position.set(Math.sin(a)*r,variant==='butterfly'?1.4+.25*Math.sin(a*2):0,Math.cos(a)*r);carrier.rotation.y=a+Math.PI/2;}
 else{carrier.position.set(0,habitat&&variant==='butterfly'?1.3:0,0);carrier.rotation.y=0;}
}
function playbackUI(){
 $('pause').textContent=paused?'继续播放':'暂停';$('pause').setAttribute('aria-pressed',String(paused));
 const duration=action?.getClip().duration||0,time=action?.time||0;
 if(document.activeElement!==$('timeline'))$('timeline').value=duration?time/duration*100:0;
 $('motion-readout').textContent=animation==='pose'?'静止姿态':`${paused?'已暂停':'播放中'} · ${time.toFixed(2)} / ${duration.toFixed(2)} 秒`;
 $('timeline').disabled=!duration;
 $('position-readout').textContent=$('environment').value==='garden'&&$('travel').checked&&animation==='move'?`场景位置 ${carrier.position.x.toFixed(2)}, ${carrier.position.z.toFixed(2)}`:'仅播放模型内的骨骼动作';
}
function play(){
 if(!mixer)return;mixer.stopAllAction();action=null;
 if(animation!=='pose'){const clip=model.userData.clips.find(c=>c.name===animation);if(clip)action=mixer.clipAction(clip).reset().play();}
 routeTime=0;mixer.update(0);if(paused&&action)mixer.setTime(seekFraction*action.getClip().duration);positionActor();active('[data-anim]','anim',animation);playbackUI();
}
function appearance(){materials.forEach(m=>m.mesh.material=mode==='wire'?m.wire:mode==='silhouette'?m.silhouette:m.color);if(bones)bones.visible=$('bones').checked;active('[data-mode]','mode',mode);}
function release(g){g.traverse(o=>{if(o.isMesh){o.geometry.dispose();(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose());}});}
function dispose(){
 if(!model)return;mixer.stopAllAction();mixer.uncacheRoot(model);scene.remove(carrier);if(bones){scene.remove(bones);bones.dispose();}
 const geometries=new Set(),mats=new Set();materials.forEach(m=>{geometries.add(m.mesh.geometry);[m.color,m.wire,m.silhouette].forEach(mat=>mats.add(mat));});geometries.forEach(g=>g.dispose());mats.forEach(m=>m.dispose());materials=[];model=null;
}
async function load(){
 if(!catalog.length)return;const n=++ticket,entry=catalog.find(e=>e.id===variant&&e.level===level);
 $('status').textContent='正在切换模型…';document.body.dataset.ready='loading';
 try{
  if(!entry)throw Error('该体型尚无编译结果');
  const [g,spec]=await Promise.all([new GLTFLoader().loadAsync(`assets/${entry.file}.glb`),fetch(`assets/${entry.file}.json`).then(r=>{if(!r.ok)throw Error('参数加载失败');return r.json();})]);
  if(n!==ticket){release(g.scene);return;}
  dispose();model=g.scene;model.userData.clips=g.animations;if(animation!=='pose'&&!g.animations.some(c=>c.name===animation))animation='idle';document.querySelector('[data-anim="wave"]').hidden=!g.animations.some(c=>c.name==='wave');carrier=new THREE.Group();carrier.add(model);scene.add(carrier);
  model.traverse(o=>{o.frustumCulled=false;if(o.isMesh){o.castShadow=true;o.receiveShadow=true;materials.push({mesh:o,color:o.material,wire:new THREE.MeshBasicMaterial({color:0x496b4f,wireframe:true}),silhouette:new THREE.MeshBasicMaterial({color:0x20392e,side:THREE.DoubleSide})});}});
  const box=new THREE.Box3().setFromObject(model),center=box.getCenter(new THREE.Vector3());model.position.set(-center.x,-box.min.y,-center.z);radius=box.getBoundingSphere(new THREE.Sphere()).radius;
  mixer=new THREE.AnimationMixer(model);bones=new THREE.SkeletonHelper(model);bones.material.depthTest=false;bones.material.vertexColors=false;bones.material.color.set(0xe98035);bones.renderOrder=10;scene.add(bones);
  play();appearance();fitScene();
  $('model-name').textContent=entry.name;$('model-tag').textContent=entry.tag+' / '+shapeNames[level];$('specimen').textContent=String(catalog.indexOf(entry)+1).padStart(2,'0');$('description').textContent=entry.description;
  $('body-size').disabled=false;$('body-size').value=level;$('size-label').textContent=shapeNames[level];
  $('triangles').textContent=entry.metrics.triangles.toLocaleString();$('joints').textContent=entry.metrics.joints;$('bytes').textContent=Math.round(entry.metrics.bytes/1024)+' KiB';
  $('download-model').href=`assets/${entry.file}.glb`;$('download-spec').href=`assets/${entry.file}.json`;$('spec-code').textContent=JSON.stringify(spec,null,2);
  $('change-summary').textContent=`${entry.name}：躯干宽度 ${entry.width.toFixed(2)} 倍、厚度 ${entry.height.toFixed(2)} 倍。这是引擎重新编译的真实模型。${['snail','butterfly','human'].includes(variant)?'独立设计的骨架与动作，不复用官方狼。':''} 动作随 GLB 下载；花园和路线属于展示场景。`;
  active('[data-variant]','variant',variant);$('status').textContent='';document.body.dataset.ready='true';
 }catch(e){if(n===ticket){$('status').textContent='加载失败，请重试切换角色或刷新。';document.body.dataset.ready='error';}console.error(e);}
}
function makeGarden(){
 const group=new THREE.Group(),material=c=>new THREE.MeshStandardMaterial({color:c,roughness:.95});
 const grass=material(0x91ab70),soil=material(0x75634a),stem=material(0x517245),leaf=material(0x60894e);
 function mesh(geometry,mat,x,y,z){const m=new THREE.Mesh(geometry,mat);m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;group.add(m);return m;}
 mesh(new THREE.CylinderGeometry(3.45,3.12,.32,64),soil,0,-.23,0);mesh(new THREE.CylinderGeometry(3.45,3.45,.08,64),grass,0,-.03,0);
 const pathMesh=mesh(new THREE.RingGeometry(1.06,1.76,96),material(0xd2c7a0),0,.013,0);pathMesh.rotation.x=-Math.PI/2;
 const petalMats=[material(0xf6d274),material(0xe9a7b6),material(0xd5dced)],pollen=material(0xc28b35);
 for(let i=0;i<22;i++){
  const a=i*2.39996,r=2.12+(i%4)*.22,x=Math.cos(a)*r,z=Math.sin(a)*r,h=.24+(i%5)*.065;
  mesh(new THREE.CylinderGeometry(.015,.021,h,6),stem,x,h/2,z);
  const l=mesh(new THREE.SphereGeometry(.1,7,5),leaf,x+.05,h*.42,z);l.scale.set(1.25,.18,.65);l.rotation.z=.3;
  for(let p=0;p<5;p++){const t=p/5*Math.PI*2,m=mesh(new THREE.SphereGeometry(.105,8,6),petalMats[i%3],x+Math.cos(t)*.095,h,z+Math.sin(t)*.095);m.scale.set(1,.38,1);}
  mesh(new THREE.SphereGeometry(.055,8,6),pollen,x,h+.022,z);
 }
 const stoneMat=material(0x9ca593);for(let i=0;i<8;i++){const a=i*.78,r=3.12,m=mesh(new THREE.DodecahedronGeometry(.12+(i%3)*.03),stoneMat,Math.cos(a)*r,.04,Math.sin(a)*r);m.scale.y=.55;}
 return group;
}
async function init(){
 scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(38,1,.01,150);renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;$('stage').appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-label','角色与花园的实时三维场景');
 scene.add(new THREE.HemisphereLight(0xffffff,0x748064,2.4));const key=new THREE.DirectionalLight(0xfff5df,2.8);key.position.set(3,7,5);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-6,right:6,top:6,bottom:-6});key.shadow.bias=-.0003;scene.add(key);
 const fill=new THREE.DirectionalLight(0xc9e9ff,1.1);fill.position.set(-5,4,-2);scene.add(fill);
 garden=makeGarden();scene.add(garden);studio=new THREE.Group();scene.add(studio);
 const floor=new THREE.Mesh(new THREE.PlaneGeometry(100,100),new THREE.ShadowMaterial({opacity:.14}));floor.rotation.x=-Math.PI/2;floor.position.y=-.005;floor.receiveShadow=true;studio.add(floor);
 controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;controls.autoRotateSpeed=.8;controls.addEventListener('start',()=>{controls.autoRotate=false;$('rotate').setAttribute('aria-pressed','false');});clock=new THREE.Clock();
 const fit=()=>{renderer.setSize($('stage').clientWidth,$('stage').clientHeight);camera.aspect=$('stage').clientWidth/$('stage').clientHeight;camera.updateProjectionMatrix();if(model)fitScene();};new ResizeObserver(fit).observe($('stage'));fit();
 renderer.setAnimationLoop(()=>{const dt=Math.min(clock.getDelta(),.05),speed=Number($('speed').value);if(mixer&&!paused&&animation!=='pose'){mixer.update(dt*speed);routeTime+=dt*speed;positionActor();}elapsed+=dt;if(mixer&&elapsed>.08){playbackUI();elapsed=0;}controls.update();renderer.render(scene,camera);});
 const r=await fetch('assets/catalog.json');if(!r.ok)throw Error('目录加载失败');catalog=await r.json();await load();
}
document.querySelectorAll('[data-variant]').forEach(b=>b.onclick=()=>{variant=b.dataset.variant;load();});
$('body-size').oninput=()=>{level=Number($('body-size').value);$('size-label').textContent=shapeNames[level];load();};
document.querySelectorAll('[data-anim]').forEach(b=>b.onclick=()=>{animation=b.dataset.anim;paused=false;play();});
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;appearance();});
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));
$('pause').onclick=()=>{paused=!paused;if(action)seekFraction=action.time/action.getClip().duration;playbackUI();};$('restart').onclick=()=>{paused=false;seekFraction=0;play();};
$('timeline').oninput=()=>{seekFraction=Number($('timeline').value)/100;paused=true;if(action)mixer.setTime(seekFraction*action.getClip().duration);if(mixer)playbackUI();};
$('speed').oninput=()=>$('speed-label').textContent=Number($('speed').value).toFixed(2)+'×';
$('environment').onchange=fitScene;$('travel').onchange=()=>{positionActor();playbackUI();};$('bones').onchange=appearance;
$('reset').onclick=()=>view('hero');$('rotate').onclick=()=>{if(controls){controls.autoRotate=!controls.autoRotate;$('rotate').setAttribute('aria-pressed',String(controls.autoRotate));}};
init().catch(e=>{$('status').textContent='三维场景启动失败，请刷新重试。';console.error(e);});
