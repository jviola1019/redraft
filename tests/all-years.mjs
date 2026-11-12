/** Finite, prespecified structural audit of every registered scenario. */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, createWriteStream, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { supportedYears, cleanup } from '../analytics/runtime_loader.mjs';
const years = [...supportedYears];
cleanup();
const output = resolve(process.argv[2] || `tests/results/all-years-${new Date().toISOString().replace(/[:.]/g, '-')}`);
mkdirSync(output, { recursive: true });
const results = [];
let cursor = 0;
async function worker() {
  while (cursor < years.length) {
    const year = years[cursor++], log = createWriteStream(`${output}/${year}.log`, { flags: 'wx' });
    const code = await new Promise((done, reject) => {
      const child = spawn(process.execPath, ['tests/league-matrix.mjs', `${output}/${year}.json`], {
        env: { ...process.env, REDRAFT_SCENARIO_YEAR: String(year) }, stdio: ['ignore', 'pipe', 'pipe'],
      });
      child.stdout.pipe(log, { end: false }); child.stderr.pipe(log, { end: false });
      child.on('error', reject);
      child.on('close', code => { log.end(); done(code); });
    });
    let report;
    try { report = JSON.parse(readFileSync(`${output}/${year}.json`, 'utf8')); } catch {}
    const passed = code === 0 && report?.status === 'passed' && !report.sourceChanged && report.actual.draftCases === 96 && report.actual.pairedReplicates === 192 && report.actual.replayPairs === 32;
    results.push({ year, exitCode: code, status: passed ? 'passed' : 'failed', actual: report?.actual });
    console.log(`${year}: ${passed ? 'passed' : 'failed'}`);
  }
}
await Promise.all(Array.from({ length: 3 }, worker));
results.sort((a,b) => a.year - b.year);
writeFileSync(`${output}/summary.json`, JSON.stringify({ at: new Date().toISOString(), years, results, limitation: 'Structural consistency only; does not establish statistical calibration or historical completeness.' }, null, 2) + '\n', { flag: 'wx' });
process.exitCode = results.every(r => r.status === 'passed') ? 0 : 1;
