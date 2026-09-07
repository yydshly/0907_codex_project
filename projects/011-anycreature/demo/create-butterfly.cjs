// Original butterfly: radial membrane wings and explicit wingbeat keyframes.
const fs=require('fs'),path=require('path'),cp=require('child_process');
const up=path.resolve(process.argv[2]||'.research/anyCreature'),out=path.join(__dirname,'assets'),dest=path.resolve(__dirname,'../../../docs/demos/011-anycreature/assets');
let catalog=JSON.parse(fs.readFileSync(path.join(out,'catalog.json'))).filter(e=>e.id!=='butterfly');
for(let level=0;level<3;level++){
 const width=[1,1.25,1.5][level];
 const s={name:'azure_gold_butterfly',smooth_angle:65,ao:{strength:.22,samples:16},shading:{gradient:{top:.12,bottom:-.18},noise:{size:.015,amount:.05}},
 palette:{body:{color:'#294851',rough:.8},wing:{color:'#1d9dbc',rough:.65},gold:{color:'#efb956',rough:.7},eye:{color:'#172928',rough:.2},vein:{color:'#264859',rough:.8}},
 joints:{Tail:[0,.25,-.58],Abdomen:[0,.25,-.2],Thorax:[0,.25,.06],Head:[0,.25,.38],Face:[0,.25,.51],LFrontRoot:[.055,.28,.1],LBackRoot:[.055,.28,-.12]},
 chains:{body:['Tail','Abdomen','Thorax','Head','Face']},attach:{},mirror:[],
 volumes:[{chain:'body',material:'body',frame:'up',sides:14,ring_step:.06,profile:[[0,.025,.025],[.22,.09*width,.09],[.5,.14*width,.13],[.74,.16*width,.15],[.88,.11*width,.11],[1,.07*width,.07]],caps:['dome','dome']}],
 parts:[{type:'eye',host:'Head',face:.075,spread:.073*width,size:.042,material:'eye'},
 {type:'curve',host:'Head',material:'gold',mirrored:true,offset:[.065,.035,.04],dir:[.35,.22,1],sides:8,segments:[{len:.2,r:.012},{len:.17,r:.009,rise:28},{len:.06,r:.023}]}],
 animations:{idle:{duration:2.2,loop:true,mirror_phase:0,tracks:{}},move:{duration:.65,loop:true,mirror_phase:0,tracks:{}}}};
 for(const [name,host,points,color] of [
  ['Front','Thorax',[[1.03,.35,1.03],[1.48,.36,.82],[1.65,.33,.39],[1.42,.3,.03],[.75,.29,-.16],[.08,.28,-.08]],'wing'],
  ['Back','Abdomen',[[.74,.29,-.1],[1.22,.3,-.46],[1.13,.29,-.82],[.79,.28,-1.02],[.31,.27,-.84],[.06,.27,-.33]],'gold']]){
  const root='L'+name+'Root',ribs=[];points.forEach(p=>p[1]=.28);
  points.forEach((p,i)=>{const tip='L'+name+'Tip'+i,chain='L'+name+'Rib'+i;s.joints[tip]=p;s.chains[chain]=[root,tip];s.attach[chain]=host;s.mirror.push(chain);ribs.push({chain});});
  s.parts.push({type:'membrane',name:name+'Wing',material:color,mirrored:true,along:8,across:3,cusp:.04,ribs});
  // A smaller contrasting membrane patch, attached to the same joint tree.
  const patchRibs=[];for(let i=0;i<points.length-1;i++){const p=points[i],tip='L'+name+'Mark'+i,chain='L'+name+'Patch'+i,r=s.joints[root];s.joints[tip]=[r[0]+(p[0]-r[0])*.68,p[1]+.009,r[2]+(p[2]-r[2])*.68];s.chains[chain]=[root,tip];s.attach[chain]=host;s.mirror.push(chain);patchRibs.push({chain});}
  s.parts.push({type:'membrane',name:name+'Mark',material:name==='Front'?'gold':'wing',mirrored:true,along:6,across:3,cusp:.08,ribs:patchRibs});
  s.animations.idle.tracks[root]={rz:[[0,8],[.5,24],[1,8]]};
  s.animations.move.tracks[root]={rz:[[0,-22],[.24,58],[.5,-22],[.74,58],[1,-22]]};
 }
 const file='butterfly-'+level;fs.writeFileSync(path.join(out,file+'.json'),JSON.stringify(s,null,2));
 const r=cp.spawnSync(process.execPath,[path.join(up,'engine/cli.js'),path.join(out,file+'.json'),path.join(out,file+'.glb')],{encoding:'utf8'});fs.writeFileSync(path.join(out,file+'-build.txt'),r.stderr+r.stdout);if(r.status){console.error(r.stderr);process.exit(r.status);}
 const b=fs.readFileSync(path.join(out,file+'.glb')),g=JSON.parse(b.subarray(20,20+b.readUInt32LE(12))),m=JSON.parse(r.stdout.trim());
 catalog.push({id:'butterfly',name:'蓝金蝴蝶',tag:'从零设计 · 骨骼振翅',description:'独立设计的膜状前后翅，振翅动作写进 GLB；花园飞行路线由场景驱动。',level,width,height:1,file,metrics:{bytes:b.length,triangles:g.meshes.flatMap(m=>m.primitives).reduce((n,p)=>n+g.accessors[p.indices].count/3,0),joints:m.joints,animations:m.anims}});
 for(const ext of ['.json','.glb','-build.txt'])fs.copyFileSync(path.join(out,file+ext),path.join(dest,file+ext));console.log(file+' compiled');
}
fs.writeFileSync(path.join(out,'catalog.json'),JSON.stringify(catalog,null,2));fs.copyFileSync(path.join(out,'catalog.json'),path.join(dest,'catalog.json'));
