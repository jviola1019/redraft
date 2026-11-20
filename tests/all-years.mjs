/** Finite, prespecified structural audit of every registered scenario. */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, createWriteStream, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import {validateMatrixReceipt, validateReleaseYears} from './matrix-receipt.mjs';
import { engine, loadScenario, supportedYears, cleanup } from '../analytics/runtime_loader.mjs';
const years = [...supportedYears];
validateReleaseYears(years);
const expected = new Map(years.map(year => {
  const {dataset, models} = loadScenario(year);
  return [year, {year, teams: dataset.teams.map(team => team.id), datasetVersion: dataset.metadata.version, engineVersion: engine.RULE_VERSION, modelVersion: models.version}];
}));
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
    let report, validationError;
    try {
      report = JSON.parse(readFileSync(`${output}/${year}.json`, 'utf8'));
      validateMatrixReceipt(report, expected.get(year));
    } catch (error) {
      validationError = error.message;
    }
    const passed = code === 0 && validationError === undefined;
    results.push({ year, exitCode: code, status: passed ? 'passed' : 'failed', actual: report?.actual, validationError });
    console.log(`${year}: ${passed ? 'passed' : 'failed'}`);
  }
}
await Promise.all(Array.from({ length: 3 }, worker));
results.sort((a,b) => a.year - b.year);
writeFileSync(`${output}/summary.json`, JSON.stringify({ at: new Date().toISOString(), years, results, limitation: 'Structural consistency only; does not establish statistical calibration or historical completeness.' }, null, 2) + '\n', { flag: 'wx' });
process.exitCode = results.every(r => r.status === 'passed') ? 0 : 1;
