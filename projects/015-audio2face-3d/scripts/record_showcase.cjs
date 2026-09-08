/* Record the actual 8020 viewport. Requires Playwright + its Chromium install.
 * Frames and media-clock events are saved locally; no model generation occurs.
 * Audio is muxed separately from the same source clips, using captured timings.
 */
const {chromium}=require('playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
(async()=>{
 const out=path.join(root,'.cache','public-recording');
 await fs.mkdir(path.join(out,'frames'),{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--autoplay-policy=no-user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{
   window.recordEvents=[];
   document.addEventListener('playing',e=>{
    if(e.target.id==='actor'&&!e.target.muted)window.recordEvents.push({at:performance.now(),mediaTime:e.target.currentTime,src:e.target.currentSrc});
   },true);
  });
  await page.goto('http://127.0.0.1:8020/',{waitUntil:'networkidle'});
  await page.waitForFunction(()=>!document.querySelector('#play-all').disabled&&document.querySelector('#idle').readyState>=2);
  await page.screenshot({path:path.join(out,'poster.png')});
  const frames=[];let done=false;
  const capture=(async()=>{
   while(!done){
    const file=`${String(frames.length).padStart(5,'0')}.jpg`;
    const before=await page.evaluate(()=>performance.now());
    await page.screenshot({path:path.join(out,'frames',file),type:'jpeg',quality:88});
    const after=await page.evaluate(()=>performance.now());
    frames.push({file,at:(before+after)/2});
    await page.waitForTimeout(30);
   }
  })();
  try{
   await page.waitForTimeout(1400);
   await page.locator('[data-mode="photo"]').click();
   await page.waitForTimeout(1800);
   await page.locator('[data-mode="motion"]').click();
   await page.waitForTimeout(2200);
   await page.locator('#play-all').click();
   await page.waitForFunction(()=>window.recordEvents.length>=3&&document.querySelector('#time').textContent==='播放完毕',null,{timeout:25000});
   await page.waitForTimeout(1600);
  }finally{done=true;await capture;}
  const events=await page.evaluate(()=>window.recordEvents);
  if(events.length!==3||errors.length)throw Error(JSON.stringify({events,errors}));
  await fs.writeFile(path.join(out,'capture.json'),JSON.stringify({viewport:{width:1440,height:1000},frames,events,errors,method:'Actual browser viewport screenshots with wall-clock timestamps; source audio aligned to captured HTML media clocks.'},null,2));
  console.log(`Recorded ${frames.length} frames and ${events.length} voiced scenes.`);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
