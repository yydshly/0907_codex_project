// Browser state-machine tests: controlled media promises, no product test hooks.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function harness(){
 const elements=new Map();
 function element(key){if(!elements.has(key))elements.set(key,{hidden:false,textContent:'',dataset:{},value:'',src:'',readyState:1,duration:6,plays:[],paused:true,pause(){this.paused=true;},play(){this.paused=false;this.plays.push(this.src);return Promise.resolve();},getAttribute(k){return this[k];},replaceChildren(){},append(){},remove(){}});return elements.get(key);}
 const ctx=vm.createContext({document:{querySelector:element,querySelectorAll:()=>[],createElement:()=>element('created')},console,Date,performance,setTimeout,clearTimeout,URLSearchParams,sessionStorage:{},history:{},location:{search:''},fetch:async()=>({ok:true,json:async()=>({busy:false})})});
 const source=fs.readFileSync('demo/dialogue-segmented.js','utf8').replace(/^init\(\)\.catch[^\n]*$/m,'');
 vm.runInContext(source,ctx);return {ctx,element,run:code=>vm.runInContext(code,ctx)};
}
const flush=()=>new Promise(r=>setImmediate(r));
(async()=>{
 const h=harness(),actor=h.element('#actor');
 h.run("epoch=1;const part={id:'p1',video:'/one.mp4',state:'comfort',text:'第一句'};const item={id:'job',mode:'segmented',segments:[part],segment_count:2,status:'rendering',submitted_at:Date.now()/1000};receive(item,1);receive(item,1);");
 await flush();assert.equal(actor.plays.length,1,'duplicate polls must not restart video');
 actor.onended();await flush();assert.equal(actor.plays.length,1,'missing next segment must wait');
 h.run("receive({...item,segments:[part,{...part,id:'p2',video:'/two.mp4'}],status:'done'},1)");
 await flush();assert.deepEqual(actor.plays,['/one.mp4','/two.mp4']);actor.onended();await flush();assert.equal(h.element('#state').textContent,'我在听');
 // A late media play promise after interruption cannot restore a stale subtitle/status.
 let resolve;actor.play=function(){this.plays.push(this.src);return new Promise(r=>resolve=r);};
 h.run("playback=null;receive({...item,id:'late'},1)");await h.run('interrupt()');resolve();await flush();
 assert.equal(h.element('#state').textContent,'我在听');assert.equal(h.element('#subtitle').textContent,'好，我在听。');
 // Replaying only the available part of a cancelled job must terminate normally.
 actor.play=function(){this.plays.push(this.src);return Promise.resolve();};
 h.run("lastResult=item");await h.element('#replay').onclick();await flush();actor.onended();await flush();assert.equal(h.element('#state').textContent,'我在听');
 // A session switch must block submit until the new session has loaded.
 let loadResolve;h.ctx.fetch=()=>new Promise(r=>loadResolve=r);
 h.ctx.sessionStorage.setItem=()=>{};h.ctx.history.replaceState=()=>{};
 h.run('configured=true;sessionLoading=false;active=null;');
 const switching=h.element('#new-session').onclick();await flush();
 assert.equal(h.element('#send').disabled,true,'session switch must block submissions to old history');
 loadResolve({ok:true,json:async()=>({id:'new-session',messages:[],avatar_id:'custom-avatar'})});await flush();
 loadResolve({ok:true,json:async()=>({id:'custom-avatar',name:'New visual',asset_base:'/avatars-media/custom-avatar/assets'})});await switching;
 assert.equal(h.element('#idle').src,'/avatars-media/custom-avatar/assets/listen/motion.mp4');
 assert.equal(h.element('#send').disabled,false);assert.equal(h.run('session.id'),'new-session');
 h.run("selectedAvatar={id:'body',asset_base:'/body',motion_backend:'minimax-body'};epoch=20;playback=null;receive({id:'body-job',mode:'segmented',segments:[{id:'bp',video:'/body-talk.mp4',state:'comfort',text:'ok',motion_phase_end:45}],segment_count:1,status:'done',submitted_at:Date.now()/1000},20)");await flush();actor.onended();await flush();
 assert.equal(h.element('#idle').src,'/body/comfort/motion.mp4');assert.equal(h.element('#idle').currentTime,1.8,'body idle continues at generated motion phase');
 console.log('PASS: duplicate polling, queue arrival, delayed play cancellation, partial replay, session switch');
})().catch(e=>{console.error(e);process.exitCode=1;});
