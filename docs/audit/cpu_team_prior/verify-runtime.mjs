#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { engine, cleanup } from '../../../analytics/runtime_loader.mjs';

cleanup();

const dir = process.argv[2] ?? '/tmp';
const read = name => JSON.parse(fs.readFileSync(`${dir}/team-prior-${name}.json`, 'utf8'));
const experimental = read('candidate');
const baseline = read('current');
const runtime = read('runtime');
const legacy = read('legacy');
const artifact = JSON.parse(fs.readFileSync(new URL('../../../analytics/cpu-position-capital-v1.json', import.meta.url)));
assert.deepEqual(artifact.counts, experimental.priorFit.positionRoundPrior);
assert.equal(artifact.rows, experimental.priorFit.rows);
assert.equal(artifact.sourceSha256, experimental.sourceHashes['data/raw/draft_picks.csv']);
assert.equal(runtime.engineVersion, engine.RULE_VERSION);
assert.equal(legacy.engineVersion, engine.LEGACY_RULE_VERSION);
assert.deepEqual(runtime.sourceHashes, legacy.sourceHashes);
for (const result of [runtime, legacy]) {
  assert.equal(result.totalDrafts, 108);
  assert.deepEqual(result.failures, []);
}
for (const [i, currentClass] of runtime.classes.entries()) {
  for (const [j, run] of currentClass.runs.entries()) {
    const legacyRun = legacy.classes[i].runs[j];
    const referenceRun = experimental.classes[i].runs[j];
    const baselineRun = baseline.classes[i].runs[j];
    assert.equal(run.selectionSha256, referenceRun.selectionSha256);
    assert.equal(legacyRun.selectionSha256, baselineRun.selectionSha256);
    assert.equal(run.tradeSha256, referenceRun.tradeSha256);
    assert.equal(run.tradeSha256, legacyRun.tradeSha256);
    assert.equal(run.tradeSha256, baselineRun.tradeSha256);
  }
}
console.log(JSON.stringify({
  engine:runtime.engineVersion,
  legacyEngine:legacy.engineVersion,
  runtimeMatchesCandidate:runtime.totalDrafts,
  legacyMatchesBaseline:legacy.totalDrafts,
  matchedTradeLedgers:runtime.totalDrafts,
  sourceHashes:runtime.sourceHashes
}, null, 2));
