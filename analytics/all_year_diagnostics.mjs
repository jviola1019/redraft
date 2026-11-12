/**
 * Frozen all-scenario simulation diagnostics. This is descriptive validation,
 * not release clearance: the 95% ranges cover Monte Carlo variation only.
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import { engine, sim, supportedYears, loadScenario, cleanup, hashes } from './runtime_loader.mjs';

const YEARS = Array.from({ length: 9 }, (_, i) => 2018 + i);
const EXPECTED_YEARS = supportedYears.filter(year => YEARS.includes(year)).sort((a, b) => a - b);
if (JSON.stringify(EXPECTED_YEARS) !== JSON.stringify(YEARS)) {
  throw new Error(`Expected every supported scenario 2018–2026; loader returned ${EXPECTED_YEARS.join(',')}.`);
}
const REPLICATES = 128;
const FIXED_SEED = 'redraft-all-year-diagnostics-2026-11-12-v1';
const FIXED_NOW = '2026-11-12T12:00:00.000Z';
const OUTPUT_JSON = 'tests/results/all-year-distributions-2026-11-12.json';
const OUTPUT_MD = 'tests/results/all-year-distributions-2026-11-12.md';
const METRICS = ['meanTotal', 'meanMargin', 'shutoutRate', 'tieRate', 'teamWinVariance'];
const startedAt = new Date().toISOString();
const started = performance.now();
const scriptSha256 = () => createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex');
const sourceHashesAtStart = { ...hashes(), 'analytics/all_year_diagnostics.mjs': scriptSha256() };
const classes = [];
let replicateWorlds = 0;

function quantile(sorted, q) {
  if (!sorted.length) return null;
  const index = (sorted.length - 1) * q;
  const lo = Math.floor(index), hi = Math.ceil(index);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (index - lo);
}

function interval(values) {
  const ordered = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!ordered.length) return { samples: 0, mean: null, median: null, lower95: null, upper95: null };
  return {
    samples: ordered.length,
    mean: ordered.reduce((sum, value) => sum + value, 0) / ordered.length,
    median: quantile(ordered, 0.5),
    lower95: quantile(ordered, 0.025),
    upper95: quantile(ordered, 0.975),
  };
}

function scoreMetrics(games, teamRows) {
  const regular = games.filter(game => game.type === 'REG');
  if (!regular.length) throw new Error('Simulation season has no regular-season games.');
  const totals = regular.map(game => game.homeScore + game.awayScore);
  const margins = regular.map(game => game.homeScore - game.awayScore);
  const wins = teamRows.map(team => team.wins);
  const meanWins = wins.reduce((sum, value) => sum + value, 0) / wins.length;
  return {
    meanTotal: totals.reduce((sum, value) => sum + value, 0) / totals.length,
    meanMargin: margins.reduce((sum, value) => sum + value, 0) / margins.length,
    shutoutRate: regular.filter(game => game.homeScore === 0 || game.awayScore === 0).length / regular.length,
    tieRate: regular.filter(game => game.homeScore === game.awayScore).length / regular.length,
    teamWinVariance: wins.reduce((sum, value) => sum + (value - meanWins) ** 2, 0) / wins.length,
  };
}

function invariants(season, dataset) {
  const regular = season.games.filter(game => game.type === 'REG');
  const stats = new Map(season.teams.map(team => [team.team, {
    wins: 0, losses: 0, ties: 0, pointsFor: 0, pointsAgainst: 0, games: 0,
  }]));
  let validScores = true;
  for (const game of regular) {
    if (![game.homeScore, game.awayScore].every(score => Number.isInteger(score) && score >= 0)) validScores = false;
    const home = stats.get(game.home), away = stats.get(game.away);
    if (!home || !away || game.home === game.away) { validScores = false; continue; }
    home.games++; away.games++;
    home.pointsFor += game.homeScore; home.pointsAgainst += game.awayScore;
    away.pointsFor += game.awayScore; away.pointsAgainst += game.homeScore;
    if (game.homeScore > game.awayScore) { home.wins++; away.losses++; }
    else if (game.homeScore < game.awayScore) { away.wins++; home.losses++; }
    else { home.ties++; away.ties++; }
  }
  const regularPerTeam = season.year >= 2021 ? 17 : 16;
  const rowsMatch = season.teams.every(team => {
    const row = stats.get(team.team);
    return row && row.wins === team.wins && row.losses === team.losses && row.ties === team.ties &&
      row.pointsFor === team.pointsFor && row.pointsAgainst === team.pointsAgainst && row.games === regularPerTeam;
  });
  const wins = season.teams.reduce((sum, team) => sum + team.wins, 0);
  const losses = season.teams.reduce((sum, team) => sum + team.losses, 0);
  const teamTies = season.teams.reduce((sum, team) => sum + team.ties, 0);
  const gameTies = regular.filter(game => game.homeScore === game.awayScore).length;
  const pointsFor = season.teams.reduce((sum, team) => sum + team.pointsFor, 0);
  const pointsAgainst = season.teams.reduce((sum, team) => sum + team.pointsAgainst, 0);
  return {
    validScores,
    leagueWinsEqualLosses: wins === losses,
    tieEntriesReconcile: teamTies === gameTies * 2,
    pointsReconcile: pointsFor === pointsAgainst,
    teamRecordsMatchGames: rowsMatch,
    allPass: validScores && wins === losses && teamTies === gameTies * 2 && pointsFor === pointsAgainst && rowsMatch,
    totalWins: wins,
    totalLosses: losses,
    tieEntries: teamTies,
    regularGames: regular.length,
  };
}

function actualSeason(dataset, year) {
  const timeline = sim.timelineState(year, new Date(FIXED_NOW));
  const complete = sim.actualSeasonIsComplete(dataset, year);
  if (timeline !== 'recorded') {
    return { used: false, state: timeline, reason: `Timeline state is ${timeline}; actual games are excluded.`, metrics: null };
  }
  if (!complete) {
    return { used: false, state: timeline, reason: 'Season is timeline-recorded, but the scenario data fails exact actual-season completeness checks.', metrics: null };
  }
  const games = dataset.games.filter(game => game.season === year && game.type === 'REG');
  const records = new Map(dataset.teams.map(team => [team.id, { team: team.id, wins: 0 }]));
  for (const game of games) {
    if (game.homeScore > game.awayScore) records.get(game.home).wins++;
    else if (game.awayScore > game.homeScore) records.get(game.away).wins++;
  }
  return { used: true, state: timeline, reason: null, metrics: scoreMetrics(games, [...records.values()]) };
}

function outsideRange(value, range) {
  return value < range.lower95 || value > range.upper95;
}

try {
  for (const draftYear of YEARS) {
    const { dataset, models } = loadScenario(draftYear);
    const game = engine.autoComplete(engine.createGame({
      team: 'CLE', year: draftYear, seed: FIXED_SEED, now: FIXED_NOW, mode: 'historical',
    }, dataset), dataset, models);
    if (game.status !== 'ready' || game.selections.length !== dataset.picks.length) {
      throw new Error(`Could not build a complete seven-round draft for ${draftYear}.`);
    }

    const seasonRows = Array.from({ length: 5 }, (_, offset) => {
      const year = draftYear + offset;
      return {
        year,
        actual: actualSeason(dataset, year),
        baseline: Object.fromEntries(METRICS.map(metric => [metric, []])),
        alternate: Object.fromEntries(METRICS.map(metric => [metric, []])),
        pairedDelta: Object.fromEntries(METRICS.map(metric => [metric, []])),
        invariantChecks: { baselineFailures: 0, alternateFailures: 0 },
        adverseFlags: [],
      };
    });

    for (let index = 0; index < REPLICATES; index++) {
      const replicate = sim.simulateReplicate(game, index, dataset, models);
      replicateWorlds += 2;
      for (const row of seasonRows) {
        const baselineSeason = replicate.baseline.seasons.find(season => season.year === row.year);
        const alternateSeason = replicate.alternate.seasons.find(season => season.year === row.year);
        if (!baselineSeason || !alternateSeason) throw new Error(`Missing simulated season ${row.year}.`);
        const baselineMetrics = scoreMetrics(baselineSeason.games, baselineSeason.teams);
        const alternateMetrics = scoreMetrics(alternateSeason.games, alternateSeason.teams);
        const baselineInvariant = invariants(baselineSeason, dataset);
        const alternateInvariant = invariants(alternateSeason, dataset);
        row.invariantChecks.baselineFailures += Number(!baselineInvariant.allPass);
        row.invariantChecks.alternateFailures += Number(!alternateInvariant.allPass);
        if (!baselineInvariant.allPass) row.adverseFlags.push(`replicate-${index}-baseline-win-or-score-invariant-failed`);
        if (!alternateInvariant.allPass) row.adverseFlags.push(`replicate-${index}-alternate-win-or-score-invariant-failed`);
        for (const metric of METRICS) {
          row.baseline[metric].push(baselineMetrics[metric]);
          row.alternate[metric].push(alternateMetrics[metric]);
          row.pairedDelta[metric].push(alternateMetrics[metric] - baselineMetrics[metric]);
        }
      }
    }

    const seasons = seasonRows.map(row => {
      const baseline = Object.fromEntries(METRICS.map(metric => [metric, interval(row.baseline[metric])]));
      const alternate = Object.fromEntries(METRICS.map(metric => [metric, interval(row.alternate[metric])]));
      const pairedDelta = Object.fromEntries(METRICS.map(metric => [metric, interval(row.pairedDelta[metric])]));
      const actualOutsideBaseline95 = row.actual.used
        ? Object.fromEntries(METRICS.map(metric => [metric, outsideRange(row.actual.metrics[metric], baseline[metric])]))
        : Object.fromEntries(METRICS.map(metric => [metric, null]));
      if (row.actual.used) {
        for (const [metric, outside] of Object.entries(actualOutsideBaseline95)) {
          if (outside) row.adverseFlags.push(`actual-${metric}-outside-baseline-central-95-monte-carlo-range`);
        }
      }
      return {
        year: row.year,
        actualComparison: row.actual,
        baseline,
        alternate,
        pairedDelta,
        winInvariance: {
          baselineFailedReplicates: row.invariantChecks.baselineFailures,
          alternateFailedReplicates: row.invariantChecks.alternateFailures,
          expectedFailureCount: 0,
        },
        adverseFlags: [...new Set(row.adverseFlags)],
        actualOutsideBaselineCentral95MonteCarlo: actualOutsideBaseline95,
      };
    });

    classes.push({
      draftYear,
      datasetVersion: dataset.metadata.version,
      cutoff: dataset.metadata.informationCutoff,
      completedDraft: { status: game.status, selections: game.selections.length, totalSlots: dataset.picks.length, userTeam: game.team },
      replicates: REPLICATES,
      seasons,
    });
  }

  const sourceHashesAtEnd = { ...hashes(), 'analytics/all_year_diagnostics.mjs': scriptSha256() };
  const changed = Object.keys(sourceHashesAtStart).filter(path => sourceHashesAtStart[path] !== sourceHashesAtEnd[path]);
  const artifact = {
    version: 'redraft-all-year-distributions-v1',
    createdAt: new Date().toISOString(),
    frozenReviewDate: FIXED_NOW,
    scenarios: YEARS,
    fixedSeed: FIXED_SEED,
    replicatesPerDraftClass: REPLICATES,
    replicatePairing: 'Each replicate compares actual-draft baseline and completed user draft under the same keyed random seed/index.',
    comparisonPolicy: 'Actual season metrics are populated only when timelineState(year) is recorded and actualSeasonIsComplete(dataset, year) is true; otherwise actual metrics are null with a reason.',
    metrics: {
      meanTotal: 'Mean combined score per regular-season game.',
      meanMargin: 'Mean home-minus-away score per regular-season game.',
      shutoutRate: 'Share of regular-season games with at least one team scoring zero.',
      tieRate: 'Share of regular-season games ending tied.',
      teamWinVariance: 'Population variance of regular-season wins across the 32 teams.',
      winInvariance: 'Per-replicate league wins/losses, ties, points and team records reconcile to simulated regular-season games.',
    },
    adverseFlagPolicy: 'Flags identify failed game/record invariants or actual metrics outside the baseline central 95% Monte Carlo range; they are descriptive, not release gates or statistical clearance.',
    limitations: [
      'Central 95% ranges represent simulation randomness only and omit model, parameter, data and structural uncertainty.',
      'Scenario prospect pools and career-development assumptions are incomplete; these diagnostics do not establish realism or causal effects.',
      'A single completed regular season is a sparse reference for out-of-sample calibration; outside-range flags are not significance tests.',
      'Partial/future seasons are not compared with actual outcomes.',
    ],
    runtime: {
      elapsedSeconds: Number(((performance.now() - started) / 1000).toFixed(3)),
      replicateWorlds,
      startedAt,
      node: process.version,
      platform: process.platform,
      architecture: process.arch,
      cpuModel: os.cpus()[0]?.model ?? null,
      cpuCount: os.cpus().length,
    },
    sourceHashesAtStart,
    sourceHashesAtEnd,
    inputDrift: { detected: changed.length > 0, changedPaths: changed },
    classes,
  };
  writeFileSync(OUTPUT_JSON, JSON.stringify(artifact, null, 2) + '\n');

  const lines = [
    '# All-year baseline distribution diagnostics',
    '',
    `Generated ${artifact.createdAt}; fixed seed matrix ${FIXED_SEED}; ${REPLICATES} paired replicates per draft class.`,
    '',
    'The baseline is the scenario’s recorded actual draft; the alternate is one completed seven-round CPU draft for CLE. Each replicate uses the same keyed random seed/index for both worlds.',
    '',
    'Central 95% Monte Carlo ranges capture simulation randomness only. They omit model and parameter uncertainty. This report does not claim statistical clearance or tune thresholds.',
    '',
    '| Draft class | Simulated season | Actual comparison | Baseline mean total [95% MC] | Shutout rate [95% MC] | Tie rate [95% MC] | Team win variance [95% MC] | Baseline invariant failures | Actual outside baseline range | Flags |',
    '|---:|---:|---|---:|---:|---:|---:|---:|---|---|',
  ];
  const fmt = range => `${range.mean.toFixed(2)} [${range.lower95.toFixed(2)}, ${range.upper95.toFixed(2)}]`;
  for (const cls of classes) for (const season of cls.seasons) {
    const actual = season.actualComparison.used ? 'recorded + complete' : `${season.actualComparison.state}: excluded`;
    const flags = season.adverseFlags.length ? season.adverseFlags.join('; ') : 'none';
    lines.push(`| ${cls.draftYear} | ${season.year} | ${actual} | ${fmt(season.baseline.meanTotal)} | ${fmt(season.baseline.shutoutRate)} | ${fmt(season.baseline.tieRate)} | ${fmt(season.baseline.teamWinVariance)} | ${season.winInvariance.baselineFailedReplicates} | ${Object.entries(season.actualOutsideBaselineCentral95MonteCarlo).filter(([, v]) => v === true).map(([k]) => k).join(', ') || (season.actualComparison.used ? 'none' : 'n/a')} | ${flags} |`);
  }
  lines.push('', 'Actual comparison reasons for excluded seasons are included in the JSON artifact. Actual records are used only when the timeline is recorded and the game dataset passes completeness checks.', '');
  writeFileSync(OUTPUT_MD, lines.join('\n'));
  console.log(JSON.stringify({
    json: OUTPUT_JSON, markdown: OUTPUT_MD, years: YEARS,
    replicatesPerClass: REPLICATES, replicateWorlds,
    parity: 'Not modified; this report consumes existing runtime outputs.',
    inputDrift: artifact.inputDrift,
    elapsedSeconds: artifact.runtime.elapsedSeconds,
  }, null, 2));
} finally {
  cleanup();
}
