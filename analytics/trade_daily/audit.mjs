import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { isMainThread, parentPort, Worker, workerData } from 'node:worker_threads';
import { cleanup, engine, hashes, loadScenario, sim } from '../runtime_loader.mjs';
import { scouting } from '../rubric_multiday/runtime.mjs';

const EXPECTED_PROTOCOL = '93dffa8433c5e6c1fe422b0fa1b73fb71333cdf179204a042d04b289e7064a24';
const fixturePath = '../rubric_multiday/fixtures.json';
const read = path => readFileSync(new URL(path, import.meta.url));
const digest = path => createHash('sha256').update(read(path)).digest('hex');
const directions = ['up', 'down'];
const mean = values => values.reduce((sum, value) => sum + value, 0) / values.length;

function* groups(items, min, max, start = 0, selected = []) {
  if (selected.length >= min) yield selected;
  if (selected.length === max) return;
  for (let index = start; index < items.length; index++) {
    yield* groups(items, min, max, index + 1, [...selected, items[index]]);
  }
}

function* offers(game, direction) {
  const available = game.picks.slice(game.selections.length);
  const own = available.filter(pick => pick.owner === game.team).map(pick => pick.overall);
  const [first, ...rest] = own;
  if (first === undefined) return;
  if (direction === 'up') {
    const earlier = available.filter(pick => pick.overall < first && pick.overall >= first - 32);
    for (const pick of earlier) {
      for (const extra of groups(rest, 1, 2)) {
        yield { target: pick.owner, give: [first, ...extra], receive: [pick.overall] };
      }
    }
  } else {
    const byTeam = Map.groupBy(available.filter(pick => pick.owner !== game.team && pick.overall > first), pick => pick.owner);
    for (const [target, picks] of byTeam) {
      for (const receive of groups(picks.map(pick => pick.overall), 2, 3)) {
        if (receive[0] <= first + 32) yield { target, give: [first], receive };
      }
    }
  }
}

function lexicographic(left, right) {
  for (let index = 0; index < Math.min(left.length, right.length); index++) {
    if (left[index] !== right[index]) return left[index] - right[index];
  }
  return left.length - right.length;
}

export function market(game, direction, dataset) {
  assert.ok(directions.includes(direction));
  const structural = [...offers(game, direction)];
  const counts = { structural: structural.length, aboveRatioCap: 0, withinRatioCap: 0, approved: 0, declined: 0 };
  const declinesByReason = {};
  let exampleDecline = null;
  const approved = [];
  for (const offer of structural) {
    const evaluation = engine.proposeTrade(game, offer, dataset);
    if (evaluation.ratio > 1.35) {
      counts.aboveRatioCap++;
      continue;
    }
    counts.withinRatioCap++;
    if (!evaluation.accepted) {
      counts.declined++;
      declinesByReason[evaluation.reason] = (declinesByReason[evaluation.reason] ?? 0) + 1;
      if (!exampleDecline || evaluation.ratio > exampleDecline.evaluation.ratio) {
        exampleDecline = { offer, evaluation };
      }
      continue;
    }
    counts.approved++;
    const move = Math.abs(offer.give[0] - offer.receive[0]);
    approved.push({ offer, evaluation, move });
  }
  const comparePriceAndMove = direction === 'up'
    ? (a, b) => b.move - a.move || a.evaluation.ratio - b.evaluation.ratio
    : (a, b) => a.move - b.move || b.evaluation.receiveValue - a.evaluation.receiveValue;
  approved.sort((a, b) => comparePriceAndMove(a, b) ||
    lexicographic(a.offer.give, b.offer.give) || lexicographic(a.offer.receive, b.offer.receive));
  return {
    atPick: engine.currentPick(game)?.overall ?? null,
    selectionCount: game.selections.length,
    counts, declinesByReason, exampleDecline,
    chosen: approved[0] ?? null,
  };
}

export function commitTrade(game, offer, dataset) {
  const baseline = JSON.stringify(dataset.actualPicks);
  const next = engine.applyTrade(game, offer, dataset);
  assert.equal(next.trades.length, game.trades.length + 1);
  const { from, to, give, receive, cpu } = next.trades.at(-1);
  assert.deepEqual({ from, target: to, give, receive, cpu }, { from: game.team, ...offer, cpu: false });
  assert.deepEqual(next.selections, game.selections);
  assert.equal(next.picks.length, game.picks.length);
  for (let index = 0; index < game.picks.length; index++) {
    const { overall, owner } = game.picks[index];
    const expectedOwner = give.includes(overall) ? to : receive.includes(overall) ? from : owner;
    assert.deepEqual(next.picks[index], { ...game.picks[index], owner: expectedOwner });
  }
  assert.equal(JSON.stringify(dataset.actualPicks), baseline);
  assert.equal(engine.validateGame(next, dataset), true);
  return next;
}

async function prepare(config, { dataset, models, scoutingPolicy }) {
  assert.equal(config.modelVersion, models.version);
  assert.equal(config.datasetVersion, dataset.metadata.version);
  assert.ok(engine.supportsEngineVersion(config.engineVersion));
  assert.equal(config.scoringVersion, engine.SCORING_VERSION);
  assert.equal(config.scoutingVersion, scouting.BLIND_POLICY_VERSION);
  assert.equal(config.ensembleSize, engine.ENSEMBLE_SIZE);
  const now = new Date(`${config.date}T12:00:00.000Z`);
  let game = engine.createGame({ ...config, mode: 'daily', now: now.toISOString() }, dataset);
  const aliases = await scouting.aliasCatalog(config.blindSalt, dataset);
  const view = () => scouting.prospectDisclosure(game, dataset, models, scoutingPolicy, aliases, now).prospects;
  const byAlias = (a, b) => a.id.localeCompare(b.id);
  const initial = view().sort(byAlias);
  const unlocked = new Set();
  for (const row of initial) {
    if (unlocked.has(row.id)) continue;
    game = engine.scout(game, aliases.toCanonical.get(row.id), dataset);
    for (const candidate of view()) if (candidate.scouted) unlocked.add(candidate.id);
    if (!game.scoutingPoints) break;
  }
  const value = row => row.projection.roleProbability ?? 0;
  const board = view().sort((a, b) => value(b) - value(a) || byAlias(a, b))
    .slice(0, 100).map(row => aliases.toCanonical.get(row.id));
  return engine.setBoard(game, board, dataset);
}

export function pairedSummary(deltas) {
  const average = mean(deltas);
  const sorted = [...deltas].sort((a, b) => a - b);
  const quantile = percentile => {
    const index = (sorted.length - 1) * percentile;
    const low = Math.floor(index);
    return sorted[low] + (sorted[Math.ceil(index)] - sorted[low]) * (index - low);
  };
  return {
    samples: deltas.length, mean: average, p10: quantile(0.10), p90: quantile(0.90),
    standardError: Math.sqrt(deltas.reduce((sum, value) => sum + (value - average) ** 2, 0) /
      (deltas.length * (deltas.length - 1))),
    positive: deltas.filter(value => value > 0).length,
    zero: deltas.filter(value => value === 0).length,
    negative: deltas.filter(value => value < 0).length,
  };
}

function scoreDraft(game, { dataset, models, scoutingPolicy }, ensembleSize) {
  const reps = Array.from({ length: ensembleSize }, (_, index) =>
    sim.compactReplicate(sim.simulateReplicate(game, index, dataset, models), game.team));
  const studied = [...new Set(game.scouted.flatMap(id => scoutingPolicy.profiles[id]?.memberIds ?? [id]))];
  const scoredGame = { ...game, scouted: studied };
  const half = ensembleSize / 2;
  const score = draws => {
    const { decisionScore, scoreComponents, summary } = sim.summarizeResults(scoredGame, draws, dataset, models);
    return { decisionScore, scoreComponents, pairedWinsVsHistory: summary };
  };
  return {
    full: score(reps), first: score(reps.slice(0, half)), second: score(reps.slice(half)),
    alternateWins: reps.map(row => row.alternate.totalWins),
    baselineWins: reps.map(row => row.baseline.totalWins),
    ownPicks: game.selections.filter(row => row.team === game.team).map(row => row.overall),
    cpuTrades: game.trades.filter(row => row.cpu).length,
  };
}

export async function runDate(config, marketsOnly = false) {
  const bundle = loadScenario(config.year);
  const { dataset, models } = bundle;
  const initial = await prepare(config, bundle);
  const beforeFirst = engine.advance(initial, dataset, models);
  assert.equal(engine.currentPick(beforeFirst)?.owner, initial.team);
  const up = market(initial, 'up', dataset);
  const down = market(beforeFirst, 'down', dataset);
  const markets = { up, down };
  const day = { date: config.date, team: config.team, year: config.year, markets };
  if (marketsOnly) return day;
  const noTradeDraft = engine.autoComplete(initial, dataset, models);
  const noTrade = scoreDraft(noTradeDraft, bundle, config.ensembleSize);
  const comparisons = {};
  for (const direction of directions) {
    const chosen = markets[direction].chosen;
    const start = direction === 'up' ? initial : beforeFirst;
    const completed = chosen
      ? engine.autoComplete(commitTrade(start, chosen.offer, dataset), dataset, models)
      : noTradeDraft;
    const traded = chosen ? scoreDraft(completed, bundle, config.ensembleSize) : noTrade;
    assert.deepEqual(traded.baselineWins, noTrade.baselineWins);
    assert.equal(completed.trades.filter(row => !row.cpu).length, chosen ? 1 : 0);
    const deltas = traded.alternateWins.map((wins, index) => wins - noTrade.alternateWins[index]);
    const half = config.ensembleSize / 2;
    const bySlice = { full: deltas, first: deltas.slice(0, half), second: deltas.slice(half) };
    comparisons[direction] = {
      ownPicks: traded.ownPicks, cpuTrades: traded.cpuTrades, pairedDeltasVsNoTrade: deltas,
      ...Object.fromEntries(Object.entries(bySlice).map(([slice, paths]) => {
        const reference = noTrade[slice];
        const candidate = traded[slice];
        const difference = {
          decisionScore: candidate.decisionScore - reference.decisionScore,
          weightedComponents: Object.fromEntries(candidate.scoreComponents.map(({ name, score, weight }, i) =>
            [name, (score - reference.scoreComponents[i].score) * weight])),
          pairedWinsVsNoTrade: pairedSummary(paths),
        };
        assert.ok(Math.abs(candidate.pairedWinsVsHistory.mean - reference.pairedWinsVsHistory.mean -
          difference.pairedWinsVsNoTrade.mean) < 1e-10);
        return [slice, { ...candidate, difference }];
      })),
    };
  }
  const { alternateWins, baselineWins, ...control } = noTrade;
  return { ...day, noTrade: control, comparisons };
}

export function aggregate(days) {
  return Object.fromEntries(directions.map(direction => {
    const executed = days.filter(day => day.markets[direction].chosen);
    const sum = field => days.reduce((total, day) => total + day.markets[direction].counts[field], 0);
    const describe = subset => {
      const values = subset.map(day => day.comparisons[direction].full.difference);
      const count = rows => ({
        higher: rows.filter(value => value > 0).length,
        tied: rows.filter(value => value === 0).length,
        lower: rows.filter(value => value < 0).length,
        averageDifference: rows.length ? mean(rows) : null,
      });
      return {
        dates: subset.length,
        decisionScore: count(values.map(row => row.decisionScore)),
        fiveYearWins: count(values.map(row => row.pairedWinsVsNoTrade.mean)),
      };
    };
    return [direction, {
      executed: executed.length, totalDates: days.length,
      structural: sum('structural'), withinRatioCap: sum('withinRatioCap'),
      approved: sum('approved'), declined: sum('declined'),
      ...(days[0].comparisons ? { allDates: describe(days), executedDates: describe(executed) } : {}),
    }];
  }));
}

function worker(config, marketsOnly) {
  return new Promise((resolve, reject) => {
    const task = new Worker(new URL(import.meta.url), { workerData: { config, marketsOnly } });
    task.once('message', resolve);
    task.once('error', reject);
    task.once('exit', code => { if (code !== 0) reject(Error(`Worker exited with code ${code}`)); });
  });
}

async function main() {
  assert.equal(digest('./PROTOCOL.md'), EXPECTED_PROTOCOL);
  const marketsOnly = process.argv.includes('--markets-only');
  const { validateFixtures } = await import('../rubric_multiday/audit.mjs');
  const fixtures = validateFixtures(JSON.parse(read(fixturePath)));
  const days = [];
  for (let index = 0; index < fixtures.length; index += 2) {
    const batch = await Promise.all(fixtures.slice(index, index + 2).map(config => worker(config, marketsOnly)));
    days.push(...batch);
    for (const { date, team, year } of batch) console.log(`Completed ${date} ${team} ${year}`);
  }
  const summary = aggregate(days);
  const result = {
    protocolSha256: EXPECTED_PROTOCOL, fixtureSha256: digest(fixturePath),
    sourceHashes: { ...hashes(), ...Object.fromEntries([
      './audit.mjs', '../../app/api/game/route.ts', '../runtime_loader.mjs', '../rubric_multiday/audit.mjs',
      '../rubric_multiday/runtime.mjs', '../../data/clean/johnson-values.json',
    ].map(path => [path, digest(path)])) },
    summary, days,
  };
  const filename = marketsOnly ? 'feasibility.json' : 'results.json';
  writeFileSync(new URL(filename, import.meta.url), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(summary, null, 2));
}

if (!isMainThread) {
  try {
    parentPort.postMessage(await runDate(workerData.config, workerData.marketsOnly));
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
