const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');
(async()=>{
 let browser;try{browser=await chromium.launch();}catch{browser=await chromium.launch({channel:'msedge'});}
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1050},reducedMotion:'reduce'});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.url()+':'+r.status());});
 await page.goto('http://127.0.0.1:8099/demos/009-ux-ui-agent-skills/effects.html');
 const embedded=()=>page.frameLocator('#demo-frame');
 await embedded().locator('#themeBtn').click();
 assert.equal(await embedded().locator('html').getAttribute('data-theme'),'dark');
 await embedded().locator('#notify').click();
 await embedded().locator('#exportBtn').click();
 await embedded().locator('#exportStatus').filter({hasText:'Export ready'}).waitFor();
 await embedded().locator('#delBtn').click();
 assert.equal(await embedded().locator('#confirmBtn').isDisabled(),true);
 await embedded().locator('#confirmInput').fill('DELETE');
 assert.equal(await embedded().locator('#confirmBtn').isDisabled(),false);
 await page.keyboard.press('Escape');
 assert.equal(await embedded().locator('#backdrop').isVisible(),false);
 const shots=path.resolve(__dirname,'../../../.cache/009-web-qa');fs.mkdirSync(shots,{recursive:true});
 await page.locator('#examples button').first().focus();await page.evaluate(()=>{document.activeElement.blur();scrollTo(0,0);});
 await page.screenshot({path:path.join(shots,'effects-desktop.png'),fullPage:true});
 await page.locator('#examples button').nth(1).click();await embedded().locator('#t').click();assert.equal(await embedded().locator('html').getAttribute('data-theme'),'dark');
 await page.locator('#examples button').nth(2).click();await embedded().locator('h1').filter({hasText:'Button'}).waitFor();assert.equal(await embedded().locator('[aria-busy=true]').count(),1);
 await page.locator('#examples button').nth(3).click();await embedded().locator('#cb2').check();assert.equal(await embedded().locator('#cb2').isChecked(),true);await embedded().locator('#r2').check();assert.equal(await embedded().locator('#r1').isChecked(),false);
 await page.locator('#examples button').nth(4).click();await embedded().locator('.sortbtn').first().click();assert.match(await embedded().locator('tbody tr').first().innerText(),/Grace Hopper/);await embedded().locator('#all').check();assert.equal(await embedded().locator('tbody input:checked').count(),3);
 await page.locator('#examples button').nth(5).click();await embedded().locator('#openBtn').click();await embedded().locator('#confirmBtn').focus();await page.keyboard.press('Tab');assert.equal(await embedded().locator('#cancelBtn').evaluate(e=>e===e.ownerDocument.activeElement),true);await page.keyboard.press('Escape');assert.equal(await embedded().locator('#openBtn').evaluate(e=>e===e.ownerDocument.activeElement),true);
 await page.locator('#phone').click();assert.equal(await page.locator('#phone').getAttribute('aria-pressed'),'true');await page.locator('#reload').click();await embedded().locator('#openBtn').waitFor();
 for(const width of [1440,768,390,320]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);}
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(shots,'effects-mobile.png'),fullPage:true});
 assert.match(await page.locator('#skill-mapping').innerText(),/a11y-audit/);
 await page.goto('http://127.0.0.1:8099/demos/009-ux-ui-agent-skills/effects.html?sample=4');
 assert.match(await page.locator('#skill-mapping').innerText(),/design-qa/);
 assert.equal(await page.locator('#sample-title').innerText(),'可操作数据表');
 await page.goto('http://127.0.0.1:8099/demos/009-ux-ui-agent-skills/standards.html');
 for(const width of [1440,390,320]){await page.setViewportSize({width,height:950});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);}
 await page.setViewportSize({width:1440,height:1000});await page.screenshot({path:path.join(shots,'standards-desktop.png')});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(shots,'standards-mobile.png')});
 assert.equal(await page.locator('#standards article').count(),6);
 assert.deepEqual(errors,[]);console.log('PASS: six examples and interactions; skill mapping; sample deep link; standards page at three widths; no script or HTTP errors.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
