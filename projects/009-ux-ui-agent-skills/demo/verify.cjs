// Requires Playwright and Chromium. Run against the local docs server.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  let browser;
  try { browser = await chromium.launch(); }
  catch { browser = await chromium.launch({channel:'msedge'}); }
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
    const errors=[];
    page.on('pageerror', error=>errors.push(error.message));
    const address=process.argv[2] || 'http://127.0.0.1:8099/demos/009-ux-ui-agent-skills/';
    await page.goto(address);
    assert.equal(await page.locator('.skill').count(),17);
    const counts=[17,3,4,3,5,2];
    for(let i=0;i<counts.length;i++) {
      await page.locator('#filters button').nth(i).click();
      assert.equal(await page.locator('.skill').count(),counts[i]);
    }
    await page.locator('#reset').click();
    await page.locator('#search').fill('Figma');
    assert.equal(await page.locator('.skill').count(),1);
    await page.locator('.skill summary').click();
    assert.equal(await page.locator('.skill[open]').count(),1);
    assert.match(await page.locator('.skill-body').innerText(),/外部工具/);
    await page.locator('#search').fill('不存在的能力xyz');
    assert.equal(await page.locator('.skill').count(),0);
    assert.equal(await page.locator('#empty').isVisible(),true);
    await page.locator('#reset').click();
    assert.equal(await page.locator('.skill').count(),17);
    for(const name of ['dark','clay','light']) {
      await page.locator(`.theme-controls [data-theme="${name}"]`).click();
      assert.equal(await page.locator('#token-preview').getAttribute('data-theme'),name);
      assert.equal(await page.locator('.theme-controls [aria-pressed="true"]').count(),1);
    }
    await page.locator('#sample-button').click();
    assert.match(await page.locator('#sample-feedback').innerText(),/未运行检查/);
    await page.locator('#sample-button').click();
    assert.equal(await page.locator('#sample-button').getAttribute('aria-expanded'),'false');
    for(let i=0;i<5;i++) {
      await page.locator('#scenario-buttons button').nth(i).click();
      assert.equal(await page.locator('#scenario-buttons [aria-pressed="true"]').count(),1);
      assert.ok((await page.locator('#scenario-detail h3').innerText()).length>0);
    }
    await page.locator('.trial summary').click();
    assert.equal(await page.locator('.trial').getAttribute('open'),'');
    await page.locator('.trial summary').click();
    const brokenAnchors=await page.locator('a[href^="#"]').evaluateAll(links=>links.filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash));
    assert.deepEqual(brokenAnchors,[]);
    const shots=path.resolve(__dirname,'../../../.cache/009-web-qa');fs.mkdirSync(shots,{recursive:true});
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.waitForFunction(()=>document.querySelector('.sidebar [aria-current]')?.hash==='#overview');
    await page.screenshot({path:path.join(shots,'desktop.png'),fullPage:false});
    await page.evaluate(()=>document.querySelector('#mechanism').scrollIntoView());
    await page.waitForFunction(()=>document.querySelector('.sidebar [aria-current]')?.hash==='#mechanism');
    await page.screenshot({path:path.join(shots,'mechanism.png'),fullPage:false});
    for(const width of [1440,1024,768,390,320]) {
      await page.setViewportSize({width,height:900});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`overflow at ${width}`);
    }
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(shots,'mobile.png'),fullPage:false});
    await page.locator('#search').fill('主题');
    assert.ok(await page.locator('.skill').count()>0);
    await page.locator('#reset').click();
    await page.locator('.skill summary').first().focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('.skill[open]').count(),1);
    assert.deepEqual(errors,[]);
    console.log('PASS: 17 skills; category/search/empty/reset; detail/keyboard; three themes; sample action; five scenarios; trial; anchors; five responsive widths; no page errors.');
    console.log('Screenshots: '+shots);
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
