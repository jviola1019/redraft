/** Real browser and local API smoke tests. No mocked game responses. */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdirSync, readFileSync, existsSync, rmSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const out = resolve('tests/results/browser');
mkdirSync(out, { recursive: true });
const modulePath = process.env.REDRAFT_PLAYWRIGHT_MODULE;
const pw = await import(modulePath ? pathToFileURL(modulePath).href : 'playwright');
let server, browser, log = '';
const results = [];
const base = process.env.REDRAFT_BASE_URL || 'http://127.0.0.1:4173';
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
  const engine = process.env.REDRAFT_BROWSER || 'chromium';
  assert.ok(['chromium', 'webkit'].includes(engine));
  browser = await pw[engine].launch({ headless: true,
    ...(process.env.REDRAFT_BROWSER_EXECUTABLE ? { executablePath: process.env.REDRAFT_BROWSER_EXECUTABLE } : {}),
  });
  for (const [label, options] of [
    ['desktop', { viewport: { width: 1440, height: 1000 } }],
    ['phone', { ...pw.devices['iPhone 13'], defaultBrowserType: undefined, reducedMotion: 'reduce' }],
  ]) {
    const context = await browser.newContext(options), page = await context.newPage();
    page.setDefaultTimeout(30000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const started = performance.now();
    await page.goto(`${base}/signin-with-chatgpt?return_to=/`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Start a draft', exact: true }).click();
    await page.getByLabel('Historical franchise').selectOption('CLE');
    await page.getByLabel('Draft class', { exact: true }).selectOption('2018');
    await page.getByLabel('Run seed').fill(`browser-${label}`);
    await page.getByRole('button', { name: 'Enter the draft room' }).click();
    await page.getByRole('heading', { name: 'You’re up. Make your pick.' }).waitFor();
    await page.getByRole('button', { name: 'Scout · 1 point', exact: true }).first().click();
    await page.getByRole('button', { name: 'Scouted', exact: true }).first().waitFor();
    await page.getByRole('button', { name: 'Review & pick', exact: true }).first().click();
    const dialog = page.getByRole('dialog');
    await dialog.waitFor();
    await page.screenshot({ path: `${out}/${engine}-${label}-profile.png`, fullPage: true });
    await page.keyboard.press('Escape');
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Continue your saved draft' }).click();
    await page.getByRole('heading', { name: 'You’re up. Make your pick.' }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Scouted', exact: true }).count() > 0, true, 'Scouting must survive reload');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `${label} has ${overflow}px horizontal overflow`);
    await page.screenshot({ path: `${out}/${engine}-${label}-draft.png`, fullPage: true });
    assert.deepEqual(errors, [], 'Browser runtime errors');
    results.push({ engine, viewport: label, status: 'passed', durationMs: Math.round(performance.now() - started), checks: ['new historical draft', 'scouting', 'profile dialog', 'keyboard dismissal', 'save/reload', 'no horizontal overflow', 'no browser errors'] });
    await context.close();
  }
} catch (error) {
  results.push({ status: 'failed', message: error.message });
  console.error(error);
  process.exitCode = 1;
} finally {
  await browser?.close();
  server?.kill('SIGTERM');
  writeFileSync(`${out}/server.log`, log);
  writeFileSync(`${out}/${process.env.REDRAFT_BROWSER || 'chromium'}-report.json`, JSON.stringify({ at: new Date().toISOString(), results, limitation: 'Phone viewport/device emulation is not a physical iPhone test. Screenshots require human review; no approved visual regression baseline exists.' }, null, 2));
  console.log(JSON.stringify(results));
}
