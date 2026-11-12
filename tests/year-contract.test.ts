/**
 * Recovery replacement authored November 12, 2026 after environment loss.
 * This is a new contract suite, not recovered original test text.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { getScenario } from '../lib/server-data';
import { autoComplete, createGame, pickValue, positionGroup } from '../lib/engine';
import { generateSchedule, simulateReplicate, summarizeResults } from '../lib/simulation';
import type { Dataset, TeamSeason } from '../lib/types';

const CLE = 'CLE';
const PIT = 'PIT';

function standings(dataset: Dataset): TeamSeason[] {
  return dataset.teams.map(team => ({
    team: team.id,
    wins: team.priorWins,
    losses: team.priorLosses,
    ties: team.priorTies,
    pointsFor: team.priorPointsFor,
    pointsAgainst: team.priorPointsAgainst,
    playoff: false,
    seed: null,
    conferenceChampion: false,
    champion: false,
  }));
}

function swapClePittStandings(rows: TeamSeason[]): TeamSeason[] {
  const result = rows.map(row => ({ ...row }));
  const cle = result.find(row => row.team === CLE);
  const pit = result.find(row => row.team === PIT);
  assert.ok(cle && pit, '2018 scenario includes Cleveland and Pittsburgh');
  for (const key of ['wins', 'losses', 'ties', 'pointsFor', 'pointsAgainst'] as const) {
    const value = cle[key];
    cle[key] = pit[key];
    pit[key] = value;
  }
  return result;
}

function opponents(fixtures: { home: string; away: string }[], team: string): string[] {
  return fixtures
    .flatMap(fixture => fixture.home === team ? [fixture.away] : fixture.away === team ? [fixture.home] : [])
    .sort();
}

test('scenario year must match the requested draft year and unsupported years reject', () => {
  const { dataset } = getScenario(2025);
  assert.throws(
    () => createGame({ id: 'year-mismatch', team: CLE, year: 2018, seed: 'mismatch' }, dataset),
    /year|scenario|unsupported/i,
  );
  assert.throws(() => getScenario(2031), /year|scenario|unsupported|installed/i);
});

test('a 2025 draft simulates 2025–2029 and leaves future actuals null', () => {
  const { dataset, models } = getScenario(2025);
  const initial = createGame(
    { id: 'five-year-2025', team: CLE, year: 2025, seed: 'five-year-2025', now: '2026-11-12T00:00:00Z' },
    dataset,
  );
  const complete = autoComplete(initial, dataset, models);
  const replicate = simulateReplicate(complete, 0, dataset, models);
  const results = summarizeResults(complete, [replicate], dataset, models);

  assert.deepEqual(results.actual.map(season => season.year), [2025, 2026, 2027, 2028, 2029]);
  const season2025 = results.actual.find(season => season.year === 2025);
  assert.equal(season2025?.state, 'recorded');
  for (const year of [2027, 2028, 2029]) {
    const season = results.actual.find(row => row.year === year);
    assert.equal(season?.state, 'future');
    assert.ok(season);
    assert.equal(season.wins, null);
    assert.equal(season.losses, null);
    assert.equal(season.ties, null);
    assert.equal(season.playoff, null);
    assert.equal(season.champion, null);
  }
});

test('future schedules react to swapped Cleveland/Pittsburgh standings while 2018 stays fixed', () => {
  const { dataset } = getScenario(2018);
  const initialStandings = standings(dataset);
  const swappedStandings = swapClePittStandings(initialStandings);

  const expected2018 = dataset.games
    .filter(game => game.season === 2018 && game.type === 'REG')
    .map(game => ({ home: game.home, away: game.away, week: game.week }));
  assert.deepEqual(generateSchedule(2018, dataset, initialStandings), expected2018);
  assert.deepEqual(generateSchedule(2018, dataset, swappedStandings), expected2018);

  const futureOriginal = generateSchedule(2019, dataset, initialStandings);
  const futureSwapped = generateSchedule(2019, dataset, swappedStandings);
  assert.notDeepEqual(opponents(futureOriginal, CLE), opponents(futureSwapped, CLE));
  assert.notDeepEqual(opponents(futureOriginal, PIT), opponents(futureSwapped, PIT));
});

test('position aliases resolve to their documented first-role gameplay groups', () => {
  assert.equal(positionGroup('CB/WR'), 'DB');
  assert.equal(positionGroup('SAF'), 'DB');
  assert.equal(positionGroup('H-back'), 'TE');
});

test('pick values extend through 400 and reject unsupported or fractional picks', () => {
  assert.equal(pickValue(257), 1);
  assert.equal(pickValue(262), 1);
  assert.throws(() => pickValue(401));
  assert.throws(() => pickValue(257.5));
});

