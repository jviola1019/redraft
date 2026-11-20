#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine, loadScenario, cleanup} from '../../../analytics/runtime_loader.mjs';

const dir = process.argv[2] ?? '/tmp';
const read = name => JSON.parse(fs.readFileSync(`${dir}/team-prior-${name}.json`, 'utf8'));
const baseline = read('current');
const prior = read('candidate');
const forced = read('forced');
const digest = data => crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');
const mean = values => values.reduce((n, x) => n + x, 0) / values.length;
const measurements = c => ({
  firstRoundTv: c.metrics.firstRoundPositionTv.mean,
  firstRoundQb: c.metrics.firstRoundQb.mean,
  firstRoundQbError: Math.abs(c.actualFirstRoundQb - c.metrics.firstRoundQb.mean),
  franchiseTv: c.metrics.franchiseMeanActualPositionTv.mean,
  franchiseDiversity: c.metrics.franchiseMeanEffectivePositions.mean,
  diversityError: mean(c.byFranchise.map(t => Math.abs(t.actualEffectivePositions - t.cpuEffectivePositions.mean))),
  wholeDraftTv: c.metrics.overallPositionTv.mean,
  roundTv: c.byRound.map(r => r.individualRunVsActualTv.mean),
});
const invariants = [];
try {
  assert.deepEqual(baseline.sourceHashes, prior.sourceHashes);
  assert.deepEqual(baseline.sourceHashes, forced.sourceHashes);
  assert.deepEqual(prior.priorFit.cohorts, [2013, 2017]);
  assert.equal(prior.priorFit.rows, 1272);
  for (const report of [baseline, prior, forced]) {
    assert.equal(report.totalDrafts, 108);
    assert.deepEqual(report.failures, []);
  }

  const classes = baseline.classes.map((c, index) => {
    const experimental = prior.classes[index], comparison = forced.classes[index];
    for (const [i, run] of c.runs.entries()) {
      assert.ok(run.tradeSha256);
      for (const other of [experimental.runs[i], comparison.runs[i]]) {
        assert.equal(other.seed, run.seed);
        assert.equal(other.designatedUserTeam, run.designatedUserTeam);
        assert.equal(other.tradeSha256, run.tradeSha256);
      }
    }
    const {dataset, models} = loadScenario(c.year);
    const config = {id: 'team-prior-poison', year: c.year, seed: c.runs[0].seed, team: c.runs[0].designatedUserTeam, now: '2026-11-20T00:00:00Z'};
    const model = {...models, teamRoundPrior: prior.priorFit.teamRoundPrior};
    const poisoned = structuredClone(dataset);
    poisoned.actualPicks.reverse().forEach((pick, i) => { pick.team = dataset.teams[i % dataset.teams.length].id; });
    poisoned.games.filter(game => game.season >= c.year).forEach(game => { game.homeScore = 999; game.awayScore = 0; });
    poisoned.prospects.forEach((p, i) => Object.assign(p, {draftPick: i + 1, draftRound: 1, careerAv: 1e8 - i, rookieSnaps: 1e7 - i}));
    for (const input of [dataset, poisoned]) {
      const game = engine.autoComplete(engine.createGame(config, input), input, model);
      assert.equal(digest(game.selections), experimental.runs[0].selectionSha256);
      assert.equal(digest(game.trades), experimental.runs[0].tradeSha256);
    }
    invariants.push({year: c.year, seed: config.seed, replayEqual: true, historyPoisonEqual: true, exactTradeReplays: c.runs.length});
    return {year:c.year, actualQb:c.actualFirstRoundQb, actualDiversity:c.actualMeanEffectivePositions, baseline:measurements(c), prior:measurements(experimental), forced:measurements(comparison)};
  });
  const windows = [classes.slice(0,4), classes.slice(4)].map(window => {
    const averages = Object.fromEntries(['baseline','prior','forced'].map(policy => [
      policy, Object.fromEntries(Object.keys(window[0][policy]).filter(k => k !== 'roundTv').map(k => [k, mean(window.map(c => c[policy][k]))])),
    ]));
    const {baseline, prior, forced} = averages;
    const checks = {
      firstRoundTv: prior.firstRoundTv < baseline.firstRoundTv,
      firstRoundQbError: prior.firstRoundQbError < baseline.firstRoundQbError,
      franchiseTv: prior.franchiseTv <= baseline.franchiseTv + 0.02,
      diversityError: prior.diversityError <= baseline.diversityError + 0.10,
      wholeDraftTv: prior.wholeDraftTv <= baseline.wholeDraftTv + 0.02,
      forcedFranchiseTv: prior.franchiseTv < forced.franchiseTv,
    };
    return {years:window.map(c => c.year), averages, checks};
  });
  const qbTotal = report => report.classes.flatMap(c=>c.runs).reduce((n, x) => n+x.firstRoundQb,0);
  console.log(JSON.stringify({
    qbFloor: 9,
    qbCounts: {baseline: qbTotal(baseline), prior: qbTotal(prior), forced: qbTotal(forced)},
    classes, windows, invariants, sourceHashes: baseline.sourceHashes, priorFit: prior.priorFit
  },null,2));
} finally { cleanup(); }
