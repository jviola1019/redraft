import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { isMainThread, parentPort, Worker, workerData } from 'node:worker_threads';
import { cleanup, engine, hashes, loadScenario, sim } from '../runtime_loader.mjs';
import { compareRanks, rankedScores } from '../rank_sensitivity.mjs';
import { dates, scouting, verifyProtocol } from './runtime.mjs';

const policies = [
  { name: 'CPU utility benchmark' },
  { name: 'Scouted probability', bonus: () => 0 },
  { name: 'Quarterback priority', bonus: p => p.position === 'QB' ? 0.25 : 0 },
  { name: 'Line priority', bonus: p => ['OL', 'DL'].includes(p.position) ? 0.20 : 0 },
];
const mean = rows => rows.reduce((sum, n) => sum + n, 0) / rows.length;
const digest = url => createHash('sha256').update(readFileSync(url)).digest('hex');

export async function draft(config, policy, { dataset, models, scoutingPolicy }) {
  const now = new Date(`${config.date}T12:00:00.000Z`);
  let game = engine.createGame({
    ...config, now: now.toISOString(), mode: 'daily',
  }, dataset);
  if (policy.bonus) {
    const aliases = await scouting.aliasCatalog(config.blindSalt, dataset);
    const view = () => scouting.prospectDisclosure(game, dataset, models, scoutingPolicy, aliases, now).prospects;
    const initial = view().sort((a, b) => policy.bonus(b) - policy.bonus(a) || a.id.localeCompare(b.id));
    const unlocked = new Set();
    for (const candidate of initial) {
      if (unlocked.has(candidate.id)) continue;
      game = engine.scout(game, aliases.toCanonical.get(candidate.id), dataset);
      for (const row of view()) {
        if (row.scouted) unlocked.add(row.id);
      }
      if (!game.scoutingPoints) break;
    }
    const value = row => (row.projection.roleProbability ?? 0) + policy.bonus(row);
    const board = view().sort((a, b) => value(b) - value(a) || a.id.localeCompare(b.id))
      .slice(0, 100).map(row => aliases.toCanonical.get(row.id));
    game = engine.setBoard(game, board, dataset);
  }
  return engine.autoComplete(game, dataset, models);
}

export function perturbations(components) {
  const weights = components.map(c => c.weight);
  return [
    { name: 'Default', weights },
    ...components.flatMap((component, index) => [0.5, 1.5].map(scale => {
      const shifted = weights.map((weight, i) => i === index ? weight * scale : weight);
      const total = shifted.reduce((sum, weight) => sum + weight, 0);
      return { name: `${component.name} ×${scale}`, weights: shifted.map(weight => weight / total) };
    })),
  ];
}

export function rankings(results) {
  const variants = perturbations(results[0].scoreComponents).map(variant => {
    const rows = results.map(result => {
      const score = result.scoreComponents.reduce((sum, component, i) => sum + component.score * variant.weights[i], 0);
      if (variant.name === 'Default') assert.equal(Math.round(score), result.decisionScore, result.name);
      return { name: result.name, score };
    });
    const independent = rankedScores(rows);
    const official = engine.rankLeaderboard(rows.map(row => ({ ...row, score: Math.round(row.score) })));
    assert.deepEqual(
      new Map(official.map(row => [row.name, row.rank])),
      new Map(independent.map(row => [row.name, row.sharedRank])),
    );
    return { ...variant, ranking: independent, rawRanking: rankedScores(rows, false) };
  });
  return variants.map(row => ({
    ...row,
    official: compareRanks(variants[0].ranking, row.ranking),
    raw: compareRanks(variants[0].rawRanking, row.rawRanking),
  }));
}

export async function runDate(config) {
  const bundle = loadScenario(config.year);
  const { dataset, models, scoutingPolicy } = bundle;
  assert.equal(config.modelVersion, models.version);
  assert.equal(config.datasetVersion, dataset.metadata.version);
  assert.ok(engine.supportsEngineVersion(config.engineVersion));
  assert.equal(config.scoringVersion, engine.SCORING_VERSION);
  assert.equal(config.scoutingVersion, scouting.BLIND_POLICY_VERSION);
  assert.equal(config.ensembleSize, engine.ENSEMBLE_SIZE);
  assert.equal(config.ensembleSize, 256);
  assert.ok(dataset.teams.some(team => team.id === config.team));
  const summaries = { full: [], first: [], second: [] };
  for (const policy of policies) {
    const game = await draft(config, policy, bundle);
    const reps = Array.from({ length: config.ensembleSize }, (_, index) =>
      sim.compactReplicate(sim.simulateReplicate(game, index, dataset, models), game.team));
    const studied = [...new Set(game.scouted.flatMap(id => scoutingPolicy.profiles[id]?.memberIds ?? [id]))];
    const scoredGame = { ...game, scouted: studied };
    for (const [slice, paths] of Object.entries({ full: reps, first: reps.slice(0, 128), second: reps.slice(128) })) {
      const { scoreComponents, decisionScore, summary } = sim.summarizeResults(scoredGame, paths, dataset, models);
      summaries[slice].push({
        name: policy.name, scoreComponents, decisionScore, pairedWins: summary,
        reportsUnlocked: game.scouted.length,
        selections: game.selections.filter(row => row.team === game.team).map(row => row.prospectId),
      });
    }
  }
  const { date, team, year } = config;
  const bySlice = Object.fromEntries(Object.entries(summaries).map(([slice, results]) => [slice, rankings(results)]));
  const components = summaries.full[0].scoreComponents;
  const invariantComponents = components.filter((component, i) =>
    summaries.full.every(row => row.scoreComponents[i].score === component.score)).map(component => component.name);
  return { date, team, year, invariantComponents, summaries, rankings: bySlice };
}

export function aggregate(days) {
  const nonDefault = day => day.rankings.full.slice(1);
  const rows = days.flatMap(nonDefault);
  const correlations = rows.map(row => row.official.spearmanToDefault).filter(Number.isFinite);
  const fraction = rows.filter(row => row.official.topPolicyChanged).length;
  return {
    dates: days.length,
    franchises: new Set(days.map(day => day.team)).size,
    scenarioYears: new Set(days.map(day => day.year)).size,
    perturbationComparisons: rows.length,
    changedLeaderSets: fraction,
    datesWithChangedLeaderSet: days.filter(day => nonDefault(day).some(row => row.official.topPolicyChanged)).length,
    rawChangedLeaderSets: rows.filter(row => row.raw.topPolicyChanged).length,
    tiedDefaultLeaders: days.filter(day => day.rankings.full[0].official.topPolicySet.length > 1).length,
    minSpearman: correlations.length ? Math.min(...correlations) : null,
    meanSpearman: correlations.length ? mean(correlations) : null,
    undefinedSpearman: rows.length - correlations.length,
    perturbations: nonDefault(days[0]).map((row, i) => ({
      name: row.name,
      changedLeaderSets: days.filter(day => nonDefault(day)[i].official.topPolicyChanged).length,
    })),
    halfEnsembles: Object.fromEntries(['first', 'second'].map(slice => [slice, {
      differentDefaultLeaderSets: days.filter(day => {
        const leaders = rank => JSON.stringify(rank[0].official.topPolicySet);
        return leaders(day.rankings.full) !== leaders(day.rankings[slice]);
      }).length,
      differentLeaderChangeCalls: days.reduce((sum, day) => sum + nonDefault(day).filter((row, i) =>
        row.official.topPolicyChanged !== day.rankings[slice][i + 1].official.topPolicyChanged).length, 0),
    }])),
  };
}

function worker(config) {
  return new Promise((resolve, reject) => {
    const task = new Worker(new URL(import.meta.url), { workerData: config });
    task.once('message', resolve);
    task.once('error', reject);
    task.once('exit', code => {
      if (code !== 0) reject(Error(`Worker exited with code ${code}`));
    });
  });
}

export function validateFixtures(snapshot) {
  const { fixtures, protocolSha256 } = snapshot;
  assert.equal(protocolSha256, verifyProtocol());
  assert.deepEqual(fixtures.map(row => row.date), dates);
  assert.ok(new Set(fixtures.map(row => row.team)).size >= 3);
  assert.ok(new Set(fixtures.map(row => row.year)).size >= 3);
  for (const row of fixtures) {
    assert.match(row.seed, /^[a-f0-9-]{72}$/);
    assert.match(row.blindSalt, /^[a-f0-9-]{72}$/);
  }
  return fixtures;
}

async function main() {
  const fixtureUrl = new URL('./fixtures.json', import.meta.url);
  const fixtures = validateFixtures(JSON.parse(readFileSync(fixtureUrl)));
  const days = [];
  for (let index = 0; index < fixtures.length; index += 2) {
    const completed = await Promise.all(fixtures.slice(index, index + 2).map(worker));
    days.push(...completed);
    for (const { date, team, year } of completed) console.log(`Completed ${date} ${team} ${year}`);
  }
  const summary = aggregate(days);
  const sources = [
    '../../app/api/game/route.ts', '../../drizzle/0000_spotty_patriot.sql',
    '../runtime_loader.mjs', '../rank_sensitivity.mjs', './capture.mjs', './runtime.mjs', './audit.mjs',
  ];
  writeFileSync(new URL('./results.json', import.meta.url), JSON.stringify({
    protocolSha256: verifyProtocol(),
    fixtureSha256: digest(fixtureUrl),
    sourceHashes: { ...hashes(), ...Object.fromEntries(sources.map(source => [source, digest(new URL(source, import.meta.url))])) },
    summary, days,
  }, null, 2) + '\n');
  console.log(JSON.stringify(summary, null, 2));
}

if (!isMainThread) {
  try {
    parentPort.postMessage(await runDate(workerData));
  } finally {
    cleanup();
  }
} else if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    await main();
  } finally {
    cleanup();
  }
}
