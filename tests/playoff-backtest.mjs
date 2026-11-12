/** Replay seeding from recorded regular-season games, not simulated standings. */
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, mkdirSync, writeFileSync } from 'node:fs';
import { sim, dataset, cleanup } from '../analytics/runtime_loader.mjs';
const games = new Map();
for (const file of readdirSync('data/processed').filter(f => /^scenario-\d{4}\.json$/.test(f))) {
  for (const game of JSON.parse(readFileSync(`data/processed/${file}`, 'utf8')).games) {
    if (games.has(game.id)) assert.deepEqual(game, games.get(game.id), `Conflicting recorded game ${game.id}`);
    games.set(game.id, game);
  }
}
const results = [];
try {
  for (let year = 2018; year <= 2025; year++) {
    const rows = [...games.values()].filter(g => g.season === year);
    if (!sim.actualSeasonIsComplete({ ...dataset, games: rows }, year)) {
      results.push({ year, status: 'unsupported', reason: 'A complete observed season is not available in the bundled scenarios.' });
      continue;
    }
    const regular = rows.filter(g => g.type === 'REG'), post = rows.filter(g => g.type !== 'REG');
    const standings = dataset.teams.map(t => {
      const own = regular.filter(g => g.home === t.id || g.away === t.id);
      const margin = g => g.home === t.id ? g.homeScore - g.awayScore : g.awayScore - g.homeScore;
      return { team: t.id, wins: own.filter(g => margin(g) > 0).length, losses: own.filter(g => margin(g) < 0).length,
        ties: own.filter(g => margin(g) === 0).length, pointsFor: own.reduce((n, g) => n + (g.home === t.id ? g.homeScore : g.awayScore), 0),
        pointsAgainst: own.reduce((n, g) => n + (g.home === t.id ? g.awayScore : g.homeScore), 0), playoff: false, seed: null, conferenceChampion: false, champion: false };
    });
    const seedings = ['AFC', 'NFC'].map(c => sim.playoffSeeds(year, c, dataset, standings, regular));
    const expectedTeams = [...new Set(post.flatMap(g => [g.home, g.away]))].sort();
    const predictedTeams = seedings.flat().map(t => t.team).sort();
    const pairs = rows => rows.map(g => `${g.home}-${g.away}`).sort();
    const expectedWC = pairs(post.filter(g => g.type === 'WC'));
    const predictedWC = seedings.flatMap(seeds => sim.wildcardMatchups(seeds, year)).map(p => p.join('-')).sort();
    const expectedDIV = pairs(post.filter(g => g.type === 'DIV'));
    const predictedDIV = seedings.flatMap(seeds => {
      const ids = new Set(seeds.map(t => t.team));
      const survivors = [...new Set(post.filter(g => g.type === 'DIV').flatMap(g => [g.home, g.away]))].filter(id => ids.has(id));
      return sim.divisionalMatchups(seeds, survivors);
    }).map(p => p.join('-')).sort();
    const matches = JSON.stringify(expectedTeams) === JSON.stringify(predictedTeams) && JSON.stringify(expectedWC) === JSON.stringify(predictedWC) && JSON.stringify(expectedDIV) === JSON.stringify(predictedDIV);
    results.push({ year, status: matches ? 'passed' : 'failed', expectedTeams, predictedTeams, expectedWC, predictedWC, expectedDIV, predictedDIV });
  }
} finally {
  cleanup();
  mkdirSync('tests/results', { recursive: true });
  const report = { at: new Date().toISOString(), scope: 'Observed playoff qualification, wild-card pairings, divisional reseeding and home-field, 2018–2025. Does not validate predicted team quality or playoff probabilities.', results };
  writeFileSync('tests/results/playoff-backtest.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(results.map(({ year, status }) => ({ year, status }))));
}
assert.equal(results.filter(r => r.status !== 'passed').length, 0, 'Every observed year must pass; see tests/results/playoff-backtest.json');
