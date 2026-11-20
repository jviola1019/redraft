import assert from 'node:assert/strict';

export const matrixSeeds = ['a', 'b', 'c'].map(suffix => 'redraft-structural-matrix-v1-' + suffix);
const hash = /^[a-f0-9]{64}$/;

export function validateReleaseYears(years) {
  assert.ok(years.length > 0 && new Set(years).size === years.length, 'Missing or duplicate scenario years');
  for (let year = 2018; year <= 2026; year++) assert.ok(years.includes(year), 'Missing released scenario ' + year);
}

export function validateMatrixReceipt(report, {year, teams, datasetVersion, engineVersion, modelVersion}) {
  assert.equal(report.status, 'passed');
  assert.deepEqual(report.failures, []);
  assert.equal(report.sourceChanged, false);
  assert.ok(Object.keys(report.sourceHashes).length > 0);
  assert.deepEqual(report.finalHashes, report.sourceHashes);
  const config = report.configuration;
  assert.equal(config.scenarioYear, year);
  assert.equal(config.datasetVersion, datasetVersion);
  assert.equal(config.engineVersion, engineVersion);
  assert.equal(config.modelVersion, modelVersion);
  assert.equal(new Set(teams).size, 32);
  assert.deepEqual([...config.teams].sort(), [...teams].sort());
  assert.deepEqual(config.seeds, matrixSeeds);
  assert.equal(config.pairedReplicatesPerCase, 2);
  const pending = new Set(teams.flatMap(team => matrixSeeds.map(seed => team + '/' + seed)));
  for (const row of report.rows) {
    assert.ok(pending.delete(row.team + '/' + row.seed), 'Duplicate or unexpected team/seed fixture');
    assert.equal(row.status, 'passed');
    assert.match(row.draftHash, hash);
    assert.equal(row.replay, row.seed === matrixSeeds[0]);
    assert.deepEqual(row.replicates.map(rep => rep.index), [0, 1]);
    for (const rep of row.replicates) {
      assert.match(rep.hash, hash);
      assert.match(rep.worldHash, hash);
    }
    assert.notEqual(row.replicates[0].worldHash, row.replicates[1].worldHash);
  }
  assert.equal(pending.size, 0, 'Missing team/seed fixtures');
  for (const [key, count] of Object.entries({draftCases:96, passedCases:96, failedCases:0, pairedReplicates:192, replayPairs:32, worlds:384, seasons:1920})) {
    assert.equal(report.actual[key], count, key);
  }
}
