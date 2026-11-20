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
  for (const [label, options] of [
    ['desktop', { viewport: { width: 1440, height: 1000 } }],
    ['phone', { ...pw.devices['iPhone 13'], defaultBrowserType: undefined, reducedMotion: 'reduce' }],
    ['narrow-phone', { viewport: { width: 320, height: 568 }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' }],
    ['tablet', { viewport: { width: 768, height: 1024 }, hasTouch: true }],
  ]) {
    stage = `${engine}/${label} journey`;
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
    await page.getByRole('button', { name: 'See prospects' }).click();
    await page.waitForFunction(() => document.activeElement?.id === 'available-prospects');
    await page.getByRole('button', { name: 'Scout · 1 point', exact: true }).first().click();
    await page.getByRole('button', { name: 'Scouted', exact: true }).first().waitFor();
    await page.getByRole('button', { name: 'Review & pick', exact: true }).first().click();
    const dialog = page.getByRole('dialog');
    await dialog.waitFor();
    await settledEntry(page);
    const statusCannotCoverDialog = await page.locator('.toast').evaluateAll(elements =>
      elements.every(element => getComputedStyle(element).pointerEvents === 'none'
        && getComputedStyle(element).clipPath !== 'none'));
    assert.ok(statusCannotCoverDialog, 'A status notification must not cover scouting details');
    const dialogBounds = await dialog.boundingBox();
    const viewport = page.viewportSize();
    assert.ok(dialogBounds && viewport && dialogBounds.x >= -1 && dialogBounds.y >= -1
      && dialogBounds.x + dialogBounds.width <= viewport.width + 1
      && dialogBounds.y + dialogBounds.height <= viewport.height + 1, 'Dialog must fit inside the viewport');
    assert.equal(await dialog.evaluate(element => element.contains(document.activeElement)), true, 'Dialog receives keyboard focus');
    // Full-page capture can resize the viewport and misplace fixed bottom sheets.
    await page.screenshot({ path: `${out}/${engine}-${label}-profile.png`, fullPage: false, animations: 'disabled' });
    await page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'detached' });
    // Exercise real selection and CPU progression; opening a profile is not a completed pick.
    const progress = page.getByRole('progressbar', { name: 'Draft selections completed' });
    const initialProgress = Number(await progress.getAttribute('aria-valuenow'));
    await page.getByRole('button', { name: 'Review & pick', exact: true }).first().click();
    await page.getByRole('dialog').getByRole('button', { name: 'Draft this prospect' }).click();
    await page.getByRole('dialog').waitFor({ state: 'detached' });
    await page.waitForFunction(initial => Number(document.querySelector('[aria-label="Draft selections completed"]').getAttribute('aria-valuenow')) > initial, initialProgress);
    await page.getByRole('button', { name: 'Jump to my pick', exact: true }).click();
    await page.getByRole('heading', { name: 'You’re up. Make your pick.' }).waitFor();
    const savedProgress = Number(await progress.getAttribute('aria-valuenow'));
    assert.ok(savedProgress > initialProgress + 1, 'CPU draft progresses to next user selection');
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Continue your saved draft' }).click();
    await page.getByRole('heading', { name: 'You’re up. Make your pick.' }).waitFor();
    await settledEntry(page);
    assert.equal(await page.locator('.draft-page').evaluate(element => Number(getComputedStyle(element).opacity)), 1, 'Draft content must finish fading into view');
    assert.equal(Number(await progress.getAttribute('aria-valuenow')), savedProgress, 'Draft selections must survive reload');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `${label} has ${overflow}px horizontal overflow`);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.screenshot({ path: `${out}/${engine}-${label}-draft.png`, fullPage: false, animations: 'disabled' });
    assert.deepEqual(errors, [], 'Browser runtime errors');
    const navigation = await page.evaluate(() => { const n = performance.getEntriesByType('navigation')[0]; return n ? { domContentLoadedMs: Math.round(n.domContentLoadedEventEnd), loadMs: Math.round(n.loadEventEnd) } : null; });
    results.push({ engine, viewport: label, navigation, status: 'passed', durationMs: Math.round(performance.now() - started), checks: ['new historical draft', 'scouting', 'profile dialog inside viewport', 'dialog focus', 'keyboard dismissal', 'confirmed user selection', 'CPU progression to next user pick', 'save/reload preserves draft progress', 'entry animation completes', 'no horizontal overflow', 'no browser errors'] });
    await context.close();
  }
} catch (error) {
  results.push({ engine, stage, status: 'failed', message: error.message });
  console.error(error);
  process.exitCode = 1;
} finally {
  await browser?.close();
  server?.kill('SIGTERM');
  if (server) writeFileSync(`${out}/server.log`, log);
  writeFileSync(`${out}/${process.env.REDRAFT_BROWSER || 'chromium'}-report.json`, JSON.stringify({ at: new Date().toISOString(), engine, executablePath: process.env.REDRAFT_BROWSER_EXECUTABLE || 'Playwright default', baseUrl: base, results, limitation: 'Phone viewport/device emulation is not a physical iPhone test. Screenshots require human review; no approved visual regression baseline exists.' }, null, 2));
  console.log(JSON.stringify(results));
}
