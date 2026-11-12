import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { actualSeasonIsComplete, divisionalMatchups, playoffSeeds, rankTiedTeams, wildcardMatchups } from '../lib/simulation';
import type { Dataset, SimGame, TeamSeason } from '../lib/types';

const dataset = JSON.parse(readFileSync('data/clean/scenario_2018.json', 'utf8')) as Dataset;
const standings = (teams: string[], wins = 10): TeamSeason[] => teams.map(team => ({ team, wins, losses: 7, ties: 0, pointsFor: 300, pointsAgainst: 300, playoff: false, seed: null, conferenceChampion: false, champion: false }));
const game = (id: string, home: string, away: string, homeScore: number, awayScore: number): SimGame => ({ id, season: 2025, week: 1, type: 'REG', home, away, homeScore, awayScore });
const seeded = (count: number): TeamSeason[] => Array.from({ length: count }, (_, i) => ({ ...standings([`T${i + 1}`])[0], playoff: true, seed: i + 1 }));

test('2018–19 field has 12 teams, two byes and reseeds the lowest survivor to seed 1', () => {
    const seeds = seeded(6);
    assert.deepEqual(wildcardMatchups(seeds, 2019), [['T3', 'T6'], ['T4', 'T5']]);
    assert.deepEqual(divisionalMatchups(seeds, ['T1', 'T2', 'T4', 'T5']), [['T1', 'T5'], ['T2', 'T4']]);
    const field = playoffSeeds(2019, 'AFC', dataset, standings(dataset.teams.filter(t => t.conference === 'AFC').map(t => t.id)), []);
    assert.equal(field.length, 6);
    assert.deepEqual(field.slice(0, 4).map(t => dataset.teams.find(x => x.id === t.team)!.division).sort(), ['East', 'North', 'South', 'West']);
});

test('2020+ field has 14 teams, one bye and reseeds the lowest wild-card survivor', () => {
    const seeds = seeded(7);
    assert.deepEqual(wildcardMatchups(seeds, 2020), [['T2', 'T7'], ['T3', 'T6'], ['T4', 'T5']]);
    assert.deepEqual(divisionalMatchups(seeds, ['T1', 'T3', 'T5', 'T7']), [['T1', 'T7'], ['T3', 'T5']]);
    const field = playoffSeeds(2020, 'NFC', dataset, standings(dataset.teams.filter(t => t.conference === 'NFC').map(t => t.id)), []);
    assert.equal(field.length, 7);
    assert.deepEqual(field.slice(0, 4).map(t => dataset.teams.find(x => x.id === t.team)!.division).sort(), ['East', 'North', 'South', 'West']);
});

test('tie groups use available head-to-head results and do not substitute a two-team comparison for a multi-team sweep', () => {
    const tied = standings(['KC', 'BUF', 'BAL']);
    const games: SimGame[] = [game('kc-buf', 'KC', 'BUF', 21, 10), game('kc-bal', 'KC', 'BAL', 24, 14)];
    const ranked = rankTiedTeams(tied, dataset, games, 'wildcard');
    assert.equal(ranked[0].team, 'KC');
    const twoTeam = rankTiedTeams(standings(['CLE', 'PIT']), dataset, [game('cle-pit-1', 'CLE', 'PIT', 17, 10), game('cle-pit-2', 'PIT', 'CLE', 13, 20)], 'division');
    assert.equal(twoTeam[0].team, 'CLE');
});

test('a single head-to-head win is not a sweep of a three-team wildcard tie', () => {
    const games = [game('a', 'KC', 'BUF', 21, 10), game('b', 'BAL', 'NE', 24, 0), game('c', 'LAC', 'KC', 20, 10)];
    assert.equal(rankTiedTeams(standings(['KC', 'BUF', 'BAL']), dataset, games, 'wildcard')[0].team, 'BAL');
});

test('actual record completeness accepts the 2022 BUF-CIN cancellation and rejects missing or invalid game data', () => {
    assert.equal(actualSeasonIsComplete(dataset, 2018), true);
    assert.equal(actualSeasonIsComplete(dataset, 2022), true);
    const missing = structuredClone(dataset);
    missing.games = missing.games.filter(g => !(g.season === 2022 && g.type === 'REG'));
    assert.equal(actualSeasonIsComplete(missing, 2022), false);
    const invalid = structuredClone(dataset);
    const gameWithBadScore = invalid.games.find(g => g.season === 2022 && g.type === 'REG')!;
    gameWithBadScore.homeScore = Number.NaN;
    assert.equal(actualSeasonIsComplete(invalid, 2022), false);
});

