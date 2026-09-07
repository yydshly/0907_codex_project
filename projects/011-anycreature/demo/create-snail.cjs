// Original creature authored from an empty spec. No example meshes/specs are read.
const fs=require('fs'),path=require('path'),cp=require('child_process');
const out=path.join(__dirname,'assets'),up=process.argv[2]?path.resolve(process.argv[2]):path.resolve(__dirname,'../../../.research/anyCreature');
const level=Number(process.argv[3]||0),bodyWidth=[1,1.25,1.5][level],bodyHeight=[1,1.1,1.2][level];
const s={name:'moss_lantern_snail',palette:{body:{color:'#638c70',rough:.82},shell:{color:'#bc8048',rough:.72},rim:{color:'#e7c17a',rough:.65},stalk:{color:'#83ac87',rough:.8},eye:{color:'#152a24',rough:.25}},
 shading:{gradient:{top:.18,bottom:-.35},noise:{size:.018,amount:.1}},smooth_angle:65,
 joints:{Tail:[0,.19,-1.05],Belly:[0,.24,-.3],Chest:[0,.28,.35],Face:[0,.38,.83],Nose:[0,.34,1.08],ShellRoot:[0,.33,-.22],ShellMid:[0,.86,-.23],ShellTop:[0,1.46,-.24],LStalkRoot:[.2,.39,.78],LStalkMid:[.32,.82,.97],LStalkTip:[.4,1.12,1.05]},
 chains:{body:['Tail','Belly','Chest','Face','Nose'],shell:['ShellRoot','ShellMid','ShellTop'],LStalk:['LStalkRoot','LStalkMid','LStalkTip']},attach:{shell:'Belly',LStalk:'Face'},mirror:['LStalk'],touch:[['body','shell']],
 volumes:[{chain:'body',material:'body',frame:'up',sides:20,ring_step:.06,profile:[[0,.05,.04],[.18,.26,.12],[.45,.44,.23],[.7,.42,.23],[.88,.31,.25],[1,.13,.13]],caps:['dome','dome']},
 {chain:'shell',material:'shell',sides:24,ring_step:.12,profile:[[0,.06,.06],[.2,.38,.37],[.45,.6,.58],[.65,.55,.54],[.86,.36,.35],[1,.04,.04]],caps:['dome','dome']},
 {chain:'LStalk',material:'stalk',sides:10,profile:[[0,.065,.065],[.5,.047,.047],[1,.065,.065]],caps:['dome','dome']}],
 parts:[{type:'spike',host:'LStalkTip',material:'eye',mirrored:true,offset:[0,0,.04],dir:[0,0,1],sides:8,segments:[{len:.07,r:.047}]}],
 animations:{idle:{duration:3.8,loop:true,mirror_phase:.25,tracks:{LStalkRoot:{rz:[[0,-3],[.5,4],[1,-3]]},LStalkMid:{rx:[[0,-4],[.5,5],[1,-4]]}}},move:{duration:2.8,loop:true,mirror_phase:.4,tracks:{Belly:{ty:[[0,0],[.5,.025],[1,0]]},Chest:{ry:[[0,-2],[.5,2],[1,-2]]},Face:{rx:[[0,-2],[.5,2],[1,-2]]},LStalkRoot:{rz:[[0,-5],[.5,6],[1,-5]]},LStalkMid:{rx:[[0,-6],[.5,4],[1,-6]]}}}}
};
s.volumes[0].profile.forEach(row=>{row[1]*=bodyWidth;row[2]*=bodyHeight;});
for(const tr of Object.values(s.animations.move.tracks))for(const [axis,keys]of Object.entries(tr))for(const key of keys)key[1]*=axis==='ty'?2:1.8;
// Find the surface of our newly generated shell; place the relief on it.
const preview=structuredClone(s);require(path.join(up,'engine/core/relative.js')).resolveJoints(preview);
require(path.join(up,'engine/core/skeleton.js')).buildSkeleton(preview);
const shellMesh=require(path.join(up,'engine/core/compile.js')).compile(preview).find(m=>m.chain==='shell');
function flank(y,z){let hit=0;for(const face of shellMesh.F){for(let i=1;i<face.length-1;i++){
 const [a,b,c]=[face[0],face[i],face[i+1]].map(j=>shellMesh.V[j]);
 const den=(b[2]-c[2])*(a[1]-c[1])+(c[1]-b[1])*(a[2]-c[2]);if(Math.abs(den)<1e-10)continue;
 const u=((b[2]-c[2])*(y-c[1])+(c[1]-b[1])*(z-c[2]))/den,v=((c[2]-a[2])*(y-c[1])+(a[1]-c[1])*(z-c[2]))/den,w=1-u-v;
 if(Math.min(u,v,w)>=-1e-6)hit=Math.max(hit,u*a[0]+v*b[0]+w*c[0]);
 }}return hit;}
// Raised spiral relief, generated as short, connected curve segments.
for(const sign of [-1,1]){
 const points=[];for(let i=0;i<=48;i++){const t=i/48,a=t*Math.PI*3.5,r=.34*(1-t)+.03,y=.95+Math.sin(a)*r,z=-.23+Math.cos(a)*r;points.push([sign*(flank(y,z)+.007),y,z]);}
 for(let i=0;i<points.length-1;i++){const a=points[i],b=points[i+1],d=b.map((v,k)=>v-a[k]),len=Math.hypot(...d);s.parts.push({type:'curve',host:'ShellMid',material:'rim',offset:a.map((v,k)=>v-s.joints.ShellMid[k]),dir:d,sides:8,segments:[{len:len*1.08,r:.022}]});}
}
fs.writeFileSync(path.join(out,`snail-${level}.json`),JSON.stringify(s,null,2));
const result=cp.spawnSync(process.execPath,[path.join(up,'engine/cli.js'),path.join(out,`snail-${level}.json`),path.join(out,`snail-${level}.glb`)],{encoding:'utf8'});
fs.writeFileSync(path.join(out,`snail-${level}-build.txt`),result.stderr+'\n'+result.stdout);process.stdout.write(result.stderr+result.stdout);if(result.status)process.exit(result.status);
const b=fs.readFileSync(path.join(out,`snail-${level}.glb`)),g=JSON.parse(b.subarray(20,20+b.readUInt32LE(12))),metrics=JSON.parse(result.stdout.trim());
const entry={id:'snail',name:'苔灯蜗牛',tag:'本次从零创作',description:'从空白参数设计腹足、螺壳、长触角与摆动动画，不读取官方狼的骨架或模型。',level,width:bodyWidth,height:bodyHeight,file:`snail-${level}`,metrics:{bytes:b.length,triangles:g.meshes.flatMap(m=>m.primitives).reduce((n,p)=>n+g.accessors[p.indices].count/3,0),joints:metrics.joints,animations:metrics.anims}};
const catPath=path.join(out,'catalog.json'),catalog=JSON.parse(fs.readFileSync(catPath)).filter(e=>!(e.id==='snail'&&e.level===level));catalog.unshift(entry);fs.writeFileSync(catPath,JSON.stringify(catalog,null,2));
const dest=path.resolve(__dirname,'../../../docs/demos/011-anycreature');for(const file of [`snail-${level}.json`,`snail-${level}.glb`,`snail-${level}-build.txt`,'catalog.json'])fs.copyFileSync(path.join(out,file),path.join(dest,'assets',file));
