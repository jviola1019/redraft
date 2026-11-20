/** Full UI lifecycle: seven rounds, five seasons and official daily publication. No direct API mutations or response mocks. */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdirSync, readFileSync, existsSync, rmSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const out = resolve('tests/results/browser-full-run');
mkdirSync(out, { recursive: true });
const modulePath = process.env.REDRAFT_PLAYWRIGHT_MODULE;
const pw = await import(modulePath ? pathToFileURL(modulePath).href : 'playwright');
let server, browser, log = '', stage = 'setup';
const engine = process.env.REDRAFT_BROWSER || 'chromium';
const results = [];
const base = process.env.REDRAFT_BASE_URL || 'http://127.0.0.1:4173';
// Wait for finite entry transitions, not the stadium's continuous animation.
// A visible locator can still be almost transparent during a CSS fade.
async function settledEntry(page) {
  await page.evaluate(async () => {
    const animations = [...document.querySelectorAll('.fade-in, .modal')]
      .flatMap(element => element.getAnimations())
      .filter(animation => Number.isFinite(animation.effect?.getComputedTiming().endTime));
    await Promise.all(animations.map(animation => animation.finished.catch(() => {})));
  });
}
try {
  if (process.argv.includes('--start-server')) {
    const lock = '.vinext/dev/lock.json';
    if (existsSync(lock)) {
      const data = JSON.parse(readFileSync(lock, 'utf8'));
      try { process.kill(data.pid, 0); }
      catch (error) { if (error.code === 'ESRCH') rmSync(lock); else throw error; }
    }
    server = spawn(process.execPath, ['scripts/run-framework.mjs', 'dev', '--host', '127.0.0.1', '--port', '4173'], {
      env: { ...process.env, REDRAFT_LOCAL_IDENTITY: '1' }, stdio: ['ignore', 'pipe', 'pipe'],
    });
    for (const stream of [server.stdout, server.stderr]) stream.on('data', b => { log += b; });
    let ready = false;
    for (let i = 0; i < 120; i++) {
      if (server.exitCode !== null) throw Error(`Dev server exited: ${log}`);
      try { const response = await fetch(`${base}/api/game`); if (response.ok || response.status === 401) { ready = true; break; } }
      catch {}
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    assert.ok(ready, `Server/API did not become ready: ${log.slice(-4000)}`);
  }
  stage = 'browser launch';
  assert.ok(['chromium', 'webkit'].includes(engine));
  browser = await pw[engine].launch({ headless: true,
    ...(process.env.REDRAFT_BROWSER_EXECUTABLE ? { executablePath: process.env.REDRAFT_BROWSER_EXECUTABLE } : {}),
  });

  const context = await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page = await context.newPage();
  page.setDefaultTimeout(60000);
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  let latestGame;
  page.on('response', async response => {
    if (!response.url().includes('/api/game')) return;
    try { const payload=await response.json(); if(payload.game)latestGame=payload.game; } catch {}
  });
  async function clickAction(locator,action){
    const pending=page.waitForResponse(response=>{
      if(!response.url().includes('/api/game')||response.request().method()!=='POST')return false;
      try{return response.request().postDataJSON().action===action}catch{return false}
    });
    await locator.click();
    const response=await pending;
    const payload=await response.json();
    assert.ok(response.ok(),`${action}: ${payload.error||response.status()}`);
    assert.ok(payload.game,`${action} returns saved game`);
    latestGame=payload.game;
    await page.getByRole('progressbar',{name:'Processing request',exact:true}).waitFor({state:'detached'});
    return payload.game;
  }
  async function finishDraft(){
    let operations=0,userPicks=0;
    while(latestGame.status==='drafting'){
      assert.ok(++operations<=300,'Draft must finish within 300 UI actions');
      const before=latestGame.selections.length;
      const current=latestGame.picks[before];
      if(current.owner===latestGame.team){
        const scout=page.getByRole('button',{name:'Scout · 1 point',exact:true}).first();
        if(await scout.isVisible()&&await scout.isEnabled())await clickAction(scout,'scout');
        await page.getByRole('button',{name:'Review & pick',exact:true}).first().click();
        const dialog=page.getByRole('dialog');
        await dialog.waitFor();
        await clickAction(dialog.getByRole('button',{name:'Draft this prospect',exact:true}),'pick');
        await dialog.waitFor({state:'detached'});
        userPicks++;
      }else{
        await clickAction(page.getByRole('button',{name:'Jump to my pick',exact:true}),'advance');
      }
      assert.ok(latestGame.selections.length>before,'Every pick/advance makes real saved progress');
    }
    assert.equal(latestGame.selections.length,latestGame.picks.length,'All league picks completed');
    assert.equal(Math.max(...latestGame.selections.map(s=>s.round)),7,'Draft reached seventh round');
    assert.ok(userPicks>0,'Human-controlled team made UI selections');
    return {userPicks,leaguePicks:latestGame.selections.length};
  }
  async function simulateAndInspect(){
    await page.getByRole('button',{name:'Simulate the next five seasons',exact:true}).click();
    await page.getByRole('heading',{name:'Here’s what changed.',exact:true}).waitFor({timeout:900000});
    assert.equal(latestGame.status,'complete');
    // Season chooser is a labeled div, rather than a native navigation landmark.
    const seasons=page.locator('[aria-label="Select simulation season"] button');
    assert.equal(await seasons.count(),5,'Results expose all five seasons');
    const years=[];
    for(let i=0;i<5;i++){
      const button=seasons.nth(i),year=Number(await button.innerText());
      years.push(year);await button.click();
      await page.locator('.season-content .eyebrow').filter({hasText:`${year} season`}).waitFor();
    }
    assert.deepEqual(years,Array.from({length:5},(_,i)=>latestGame.year+i));
    const evidence=page.getByRole('list',{name:'Historical evidence by season'}).getByRole('listitem');
    const labels={recorded:'Recorded',incomplete:'Incomplete',future:'Projection'};
    assert.equal(await evidence.count(),5);
    for(const [index,year] of years.entries()){
      const actual=latestGame.results.actual.find(row=>row.year===year);
      assert.equal(await evidence.nth(index).locator('strong').innerText(),String(year));
      assert.equal(await evidence.nth(index).locator('span').innerText(),actual?labels[actual.state]:'Unavailable');
    }
    if(latestGame.mode==='historical'){
      const statuses=await evidence.locator('span').allTextContents();
      assert.ok(statuses.includes('Recorded'),'Historical fixture includes observed wins');
      assert.ok(statuses.some(value=>value==='Projection'||value==='Incomplete'),'Historical fixture crosses the history boundary');
    }
    await page.getByRole('button',{name:'Your draft class',exact:true}).click();
    await page.getByRole('heading',{name:'The class you built',exact:true}).waitFor();
    await page.getByRole('heading',{name:'Player development',exact:true}).waitFor();
    assert.deepEqual(errors,[],'No browser runtime errors throughout complete journey');
    await page.screenshot({path:`${out}/${latestGame.mode}-complete.png`,fullPage:false,animations:'disabled'});
    return latestGame.id;
  }
  stage='historical seven-round UI draft';
  await page.goto(`${base}/signin-with-chatgpt?return_to=/`,{waitUntil:'networkidle'});
  await page.getByRole('button',{name:'Start a draft',exact:true}).click();
  await page.getByLabel('Historical franchise').selectOption('CLE');
  await page.getByLabel('Draft class',{exact:true}).selectOption('2025');
  await page.getByRole('button',{name:'View pre-draft personnel'}).click();
  const snapshot=page.getByRole('dialog');
  await snapshot.getByRole('heading',{name:'Who could carry a workload again?'}).waitFor();
  await snapshot.getByText('Explore last season’s position groups').click();
  assert.ok(await snapshot.getByRole('table').first().isVisible());
  await snapshot.getByRole('button',{name:'Close dialog'}).click();
  await page.getByLabel('Run seed').fill('browser-full-seven-rounds');
  await clickAction(page.getByRole('button',{name:'Enter the draft room'}),'new');
  const historical=await finishDraft();
  stage='historical five-season UI simulation';
  historical.gameId=await simulateAndInspect();
  results.push({mode:'historical',status:'passed',...historical});

  stage='daily seven-round UI draft';
  await page.getByRole('navigation',{name:'Mobile navigation'}).getByRole('button',{name:'Daily challenge',exact:true}).click();
  const accept=page.getByRole('button',{name:'Accept today’s challenge',exact:true});
  assert.ok(await accept.isVisible(),'Use a fresh daily identity/database: existing attempt would not exercise submission');
  await clickAction(accept,'new');
  assert.equal(latestGame.mode,'daily');
  const daily=await finishDraft();
  stage='daily five-season simulation and official submission';
  daily.gameId=await simulateAndInspect();
  await page.getByText('Daily identities remain sealed.',{exact:true}).waitFor();
  const bootstrap=page.waitForResponse(response=>response.url().includes('/api/game?action=bootstrap'));
  await page.getByRole('navigation',{name:'Mobile navigation'}).getByRole('button',{name:'Daily challenge',exact:true}).click();
  const published=await (await bootstrap).json();
  assert.equal(published.daily.gameId,daily.gameId,'Official attempt is the completed UI draft');
  assert.equal(published.daily.status,'complete','Server persisted daily completion');
  const entry=published.leaderboard.find(row=>row.alias===published.user.alias);
  assert.ok(entry,'Server published participant result to daily leaderboard');
  assert.ok(Number.isFinite(entry.score),'Published official score is finite');
  await page.getByRole('button',{name:'View your official result',exact:true}).waitFor();
  await page.locator('.leaderboard tbody').getByText(published.user.alias,{exact:true}).waitFor();
  results.push({mode:'daily',status:'passed',...daily,officialScore:entry.score});
  await context.close();
} catch (error) {
  results.push({ engine, stage, status: 'failed', message: error.message });
  console.error(error);
  process.exitCode = 1;
} finally {
  await browser?.close();
  server?.kill('SIGTERM');
  if (server) writeFileSync(`${out}/server.log`, log);
  writeFileSync(`${out}/${process.env.REDRAFT_BROWSER || 'chromium'}-report.json`, JSON.stringify({ at: new Date().toISOString(), engine, executablePath: process.env.REDRAFT_BROWSER_EXECUTABLE || 'Playwright default', baseUrl: base, results, limitation: '390px mobile viewport is browser emulation, not a physical-device test. This suite uses full configured ensembles and can take several minutes. Screenshots require human review.' }, null, 2));
  console.log(JSON.stringify(results));
}
