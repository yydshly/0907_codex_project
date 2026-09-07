// Reproducible demo assets; requires a separately cloned anyCreature checkout.
const fs=require('fs'),path=require('path'),cp=require('child_process');
const root=path.resolve(__dirname,'../../..');
const upstream=path.resolve(process.argv[2]||path.join(root,'.research/anyCreature'));
const out=path.join(__dirname,'assets');fs.mkdirSync(out,{recursive:true});
const base=JSON.parse(fs.readFileSync(path.join(upstream,'example/wolf.json')));
const variants=[
 {id:'wolf',name:'原野狼',tag:'官方样例',description:'官方四足样例：观察身体截面、左右肢体和两段骨骼动画。',colors:null},
 {id:'frost',name:'冰原狼',tag:'配色变体',description:'保留同一套骨架，修改材质与身体色带，得到冷色角色变体。',colors:['#719ba6','#abcad0','#60949e','#557b89','#74929d','#20343f','#98bcc8','#f9df90']},
 {id:'horn',name:'弯角兽',tag:'部件扩展',description:'在狼的结构上增加一对分段弯角；弯角跟随头部骨骼运动。',colors:['#675247','#815143','#715241','#4d4543','#655248','#211e22','#945f44','#ffd786']}
];
const records=[];
for(const v of variants)for(let level=0;level<3;level++){
 const s=structuredClone(base),width=[1,1.15,1.3][level],height=[1,1.08,1.16][level];
 s.name=v.id+'_'+level;
 if(v.colors){Object.keys(s.palette).forEach((key,i)=>s.palette[key].color=v.colors[i]);
  for(const vol of s.volumes)if(vol.colors)vol.colors.arcs.forEach((a,i)=>a.color=v.id==='frost'?(i?'#cbdfe1':'#466878'):(i?'#ae9576':'#443a35'));}
 const body=s.volumes.find(x=>x.chain==='body');body.profile.forEach(row=>{row[1]*=width;row[2]*=height;});
 if(v.id==='horn'){
  s.palette.horn={color:'#d7bc8e',rough:0.7};
  s.parts.push({type:'curve',host:'Skull',material:'horn',mirrored:true,offset:[0.13,0.085,-0.02],dir:[0.4,1,-0.3],sides:10,
   segments:[{len:0.22,r:0.075},{len:0.21,r:0.058,behind:22},{len:0.18,r:0.032,behind:30},{len:0.13,r:0.012,ahead:20,taper:true}]});
 }
 const file=v.id+'-'+level;fs.writeFileSync(path.join(out,file+'.json'),JSON.stringify(s,null,2));
 const r=cp.spawnSync(process.execPath,[path.join(upstream,'engine/cli.js'),path.join(out,file+'.json'),path.join(out,file+'.glb')],{encoding:'utf8'});
 if(r.status!==0)throw new Error(file+' failed: '+r.stderr);
 const metrics=JSON.parse(r.stdout.trim());const b=fs.readFileSync(path.join(out,file+'.glb'));const g=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString());
 const triangles=g.meshes.flatMap(m=>m.primitives).reduce((sum,p)=>sum+g.accessors[p.indices].count/3,0);
 records.push({...v,colors:undefined,level,width,height,file,metrics:{bytes:metrics.bytes,triangles,joints:metrics.joints,animations:metrics.anims},changes:{bodyWidth:width,bodyHeight:height,addedParts:v.id==='horn'?2:0,palette:s.palette}});
 console.log(file+' OK · '+triangles+' triangles');
}
fs.writeFileSync(path.join(out,'catalog.json'),JSON.stringify(records,null,2));
fs.copyFileSync(path.join(upstream,'harness/assets/three-bundle.js'),path.join(out,'three-bundle.js'));
fs.copyFileSync(path.join(upstream,'LICENSE'),path.join(out,'ANYCREATURE-LICENSE.txt'));
fs.copyFileSync(path.join(upstream,'THIRD-PARTY-NOTICES.md'),path.join(out,'UPSTREAM-NOTICES.md'));
const target=path.join(root,'docs/demos/011-anycreature');fs.mkdirSync(target,{recursive:true});
for(const file of ['index.html','capture.html','style.css','app.js','THIRD_PARTY_NOTICES.md'])if(fs.existsSync(path.join(__dirname,file)))fs.copyFileSync(path.join(__dirname,file),path.join(target,file));
fs.cpSync(out,path.join(target,'assets'),{recursive:true});
// Keep the new original creature in the catalog when rebuilding the full demo.
for(let level=0;level<3;level++){
 const original=cp.spawnSync(process.execPath,[path.join(__dirname,'create-snail.cjs'),upstream,String(level)],{stdio:'inherit'});
 if(original.status)process.exit(original.status);
}
const butterfly=cp.spawnSync(process.execPath,[path.join(__dirname,'create-butterfly.cjs'),upstream],{stdio:'inherit'});
if(butterfly.status)process.exit(butterfly.status);
const human=cp.spawnSync(process.execPath,[path.join(__dirname,'create-human.cjs'),upstream],{stdio:'inherit'});
if(human.status)process.exit(human.status);

const cover=path.join(__dirname,'../assets/human-wave.png');if(fs.existsSync(cover))fs.copyFileSync(cover,path.join(target,'assets/human-wave.png'));
