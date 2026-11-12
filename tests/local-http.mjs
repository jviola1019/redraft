/** Local installation smoke test through actual HTTP, Vite and local D1. */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { readFileSync, existsSync, rmSync, mkdirSync, writeFileSync } from 'node:fs';
const origin = 'http://127.0.0.1:4174', started = performance.now();
const lock = '.vinext/dev/lock.json';
if (existsSync(lock)) {
  const data = JSON.parse(readFileSync(lock, 'utf8'));
  try { process.kill(data.pid, 0); }
  catch (error) { if (error.code === 'ESRCH') rmSync(lock); else throw error; }
}
const server = spawn(process.execPath, ['scripts/run-framework.mjs', 'dev', '--host', '127.0.0.1', '--port', '4174'], { stdio: ['ignore','pipe','pipe'] });
let log = '', status = 'failed', checks = [], failure;
for (const stream of [server.stdout, server.stderr]) stream.on('data', b => { log += b; });
try {
  let ready = false;
  for (let i = 0; i < 90; i++) {
    if (server.exitCode !== null) throw Error('Server exited before readiness.');
    try { const r = await fetch(origin + '/api/game'); if (r.status === 401) { ready = true; break; } } catch {}
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  assert.ok(ready, 'Local server must run and require sign-in'); checks.push('unauthenticated 401');
  const login = await fetch(origin + '/signin-with-chatgpt?return_to=/', { redirect: 'manual' });
  assert.equal(login.status, 302);
  const cookie = login.headers.get('set-cookie')?.split(';')[0]; assert.ok(cookie);
  const headers = { cookie, origin, 'content-type': 'application/json' };
  const home = await fetch(origin, { headers }); assert.equal(home.status, 200); assert.match(await home.text(), /REDRAFT/i);
  checks.push('loopback sign-in and rendered homepage');
  const boot = await fetch(origin + '/api/game', { headers }); assert.equal(boot.status, 200);
  const bootstrap = await boot.json(); assert.ok(bootstrap.years.includes(2018));
  checks.push('real bootstrap and local D1');
  const post = async body => { const response = await fetch(origin + '/api/game', { method: 'POST', headers, body: JSON.stringify({ ...body, requestId: crypto.randomUUID() }) }); const data = await response.json(); assert.ok(response.ok, JSON.stringify(data)); return data; };
  let view = await post({ action: 'new', mode: 'historical', team: 'CLE', year: 2018, seed: 'local-http-installation' });
  const id = view.game.id, prospectId = view.prospects[0].id;
  view = await post({ action: 'scout', id, revision: view.game.revision, prospectId });
  assert.equal(view.game.scoutingPoints, 11);
  const reload = await fetch(origin + '/api/game?action=load&id=' + id, { headers });
  assert.equal(reload.status, 200); assert.equal((await reload.json()).game.scoutingPoints, 11);
  checks.push('new game, scouting transaction, persistent reload');
  status = 'passed';
} catch (error) { failure = error.message; console.error(error); process.exitCode = 1; }
finally {
  server.kill('SIGTERM');
  mkdirSync('tests/results', { recursive: true });
  writeFileSync('tests/results/local-http-server.log', log);
  const report = { at: new Date().toISOString(), status, checks, failure, durationMs: Math.round(performance.now() - started), limitation: 'HTTP and server rendering only; does not replace a browser or physical iPhone test.' };
  writeFileSync('tests/results/local-http.json', JSON.stringify(report, null, 2)); console.log(JSON.stringify(report));
}
