// Original stylized person. Geometry and animations are authored from empty data.
const fs=require('fs'),path=require('path'),cp=require('child_process');
const up=path.resolve(process.argv[2]||'.research/anyCreature'),out=path.join(__dirname,'assets'),dest=path.resolve(__dirname,'../../../docs/demos/011-anycreature/assets');
const catalog=JSON.parse(fs.readFileSync(path.join(out,'catalog.json'))).filter(e=>e.id!=='human');
for(let level=0;level<3;level++){
 const width=[1,1.12,1.24][level];
 const s={name:'garden_walker',smooth_angle:65,ao:{strength:.32},shading:{gradient:{top:.14,bottom:-.22},noise:{size:.02,amount:.035}},
 palette:{shirt:{color:'#cf784e',rough:.85},skin:{color:'#e9bc91',rough:.85},pants:{color:'#415a77',rough:.9},shoe:{color:'#293943',rough:.9},eye:{color:'#293334',rough:.25}},
 joints:{Hips:[0,1.02,0],Waist:[0,1.27,0],Chest:[0,1.61,0],Neck:[0,1.77,0],HeadRoot:[0,1.72,.015],Skull:[0,2.04,.015],Crown:[0,2.27,0],
 LShoulder:[.19,1.58,0],LElbow:[.37,1.23,.025],LWrist:[.42,.94,.055],LHand:[.43,.81,.065],
 LHip:[.135,1.015,0],LKnee:[.175,.57,.025],LAnkle:[.185,.12,0],LToe:[.185,.04,.16]},
 chains:{body:['Hips','Waist','Chest','Neck'],head:['HeadRoot','Skull','Crown'],LArm:['LShoulder','LElbow','LWrist','LHand'],LLeg:['LHip','LKnee','LAnkle','LToe']},attach:{head:'Neck',LArm:'Chest',LLeg:'Hips'},mirror:['LArm','LLeg'],
 volumes:[{chain:'body',material:'shirt',sides:18,ring_step:.08,profile:[[0,.25*width,.17],[.25,.21*width,.15],[.72,.29*width,.18],[.85,.25*width,.16],[1,.09,.085]],caps:['dome','dome']},
 {chain:'head',material:'skin',sides:18,ring_step:.07,profile:[[0,.065,.065],[.2,.15,.145],[.5,.22,.19],[.73,.205,.18],[1,.125,.115]],caps:['dome','dome']},
 {chain:'LArm',material:'skin',sides:12,ring_step:.07,profile:[[0,.08,.08],[.26,.091,.087],[.55,.073,.075],[.78,.053,.052],[.9,.07,.046],[1,.046,.03]],caps:['dome','dome']},
 {chain:'LLeg',material:'pants',sides:14,ring_step:.08,profile:[[0,.11,.12],[.25,.12,.125],[.5,.09,.095],[.8,.067,.07],[1,.052,.052]],caps:['dome','dome']}],
 parts:[{type:'paw',host:'LToe',material:'shoe',mirrored:true,size:[.32,.22,.11]},
 {type:'eye',host:'Skull',material:'eye',face:.213,spread:.076,height:.015,size:.028},
 {type:'spike',host:'Skull',material:'skin',offset:[0,-.035,.19],dir:[0,0,1],sides:8,segments:[{len:.074,r:.034}]}],
 animations:{idle:{duration:3,loop:true,mirror_phase:0,tracks:{Chest:{rx:[[0,-1.5],[.5,1.5],[1,-1.5]]},LShoulder:{rz:[[0,0],[.5,2],[1,0]]}}},
 move:{duration:1.2,loop:true,mirror_phase:.5,tracks:{LHip:{rx:[[0,-18],[.5,18],[1,-18]]},LKnee:{rx:[[0,5],[.25,28],[.5,5],[.75,2],[1,5]]},LShoulder:{rx:[[0,15],[.5,-15],[1,15]]},LElbow:{rx:[[0,-8],[.5,-15],[1,-8]]}}},
 wave:{duration:2.5,loop:true,mirror_phase:0,tracks:{LShoulder:{rz:[[0,102],[.5,108],[1,102]]},LElbow:{rz:[[0,20],[.25,48],[.5,20],[.75,48],[1,20]]},LWrist:{rz:[[0,-8],[.25,10],[.5,-8],[.75,10],[1,-8]]},RShoulder:{rz:[[0,0],[1,0]]},RElbow:{rz:[[0,0],[1,0]]},RWrist:{rz:[[0,0],[1,0]]}}}}
 };
 const file='human-'+level;fs.writeFileSync(path.join(out,file+'.json'),JSON.stringify(s,null,2));
 const r=cp.spawnSync(process.execPath,[path.join(up,'engine/cli.js'),path.join(out,file+'.json'),path.join(out,file+'.glb')],{encoding:'utf8'});fs.writeFileSync(path.join(out,file+'-build.txt'),r.stderr+r.stdout);if(r.status){console.error(r.stderr);process.exit(r.status);}
 const b=fs.readFileSync(path.join(out,file+'.glb')),g=JSON.parse(b.subarray(20,20+b.readUInt32LE(12))),m=JSON.parse(r.stdout.trim());
 catalog.unshift({id:'human',name:'花园行者',tag:'从零设计 · 简化人形',description:'独立创建头、躯干、双臂和双腿；GLB 内含待机、行走与单手挥手动作。',level,width,height:1,file,metrics:{bytes:b.length,triangles:g.meshes.flatMap(m=>m.primitives).reduce((n,p)=>n+g.accessors[p.indices].count/3,0),joints:m.joints,animations:m.anims}});
 for(const ext of ['.json','.glb','-build.txt'])fs.copyFileSync(path.join(out,file+ext),path.join(dest,file+ext));console.log(file+' compiled');
}
fs.writeFileSync(path.join(out,'catalog.json'),JSON.stringify(catalog,null,2));fs.copyFileSync(path.join(out,'catalog.json'),path.join(dest,'catalog.json'));
