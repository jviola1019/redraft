import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { playerDevelopment } from '../components/redraft/player-development';
import { autoComplete, createGame } from '../lib/engine';
import { compactReplicate, simulateReplicate } from '../lib/simulation';
import type { Dataset, ReplicateResult } from '../lib/types';

const dataset = JSON.parse(readFileSync('data/processed/scenario-2018.json', 'utf8')) as Dataset;
const game = autoComplete(createGame({ seed: 'player-development-test', team: 'CLE' }, dataset), dataset);
const featured = simulateReplicate(game, 0, dataset);
const compacted = compactReplicate(simulateReplicate(game, 1, dataset), game.team);

test('player development uses the featured alternate season rows and each team game count', () => {
  const development = playerDevelopment(game, [compacted, featured], true);
  assert.deepEqual(development.map(({ pick }) => pick), game.selections.filter(pick => pick.team === game.team));
  for (const { pick, seasons } of development) {
    assert.equal(seasons.length, 5);
    for (const { year, games, starts, startShare, contribution } of seasons) {
      const result = featured.alternate.seasons.find(season => season.year === year)!;
      const player = result.players.find(player => player.prospectId === pick.prospectId)!;
      const team = result.teams.find(team => team.team === game.team)!;
      assert.deepEqual({ games, starts, contribution }, {
        games: player.games, starts: player.starts, contribution: player.contribution,
      });
      assert.equal(startShare, player.starts / (team.wins + team.losses + team.ties));
      assert.equal(team.wins + team.losses + team.ties, year >= 2021 ? 17 : 16);
    }
  }
});

test('absent rows and compacted runs remain missing while a simulated zero stays zero', () => {
  const pick = game.selections.find(pick => pick.team === game.team)!;
  const source = featured.alternate.seasons[0];
  const unplayed = { prospectId: pick.prospectId, team: game.team, season: game.year, games: 0, starts: 0, contribution: 0 };
  const sparse: ReplicateResult = {
    ...featured,
    alternate: { ...featured.alternate, seasons: [
      { ...source, players: [unplayed] },
      { ...source, year: game.year + 1, players: [{ ...unplayed, season: game.year + 1, team: 'KC' }] },
    ] },
  };
  const rows = playerDevelopment(game, [sparse], true)[0].seasons;
  assert.deepEqual(rows[0], { year: game.year, games: 0, starts: 0, startShare: 0, contribution: 0 });
  for (const [index, row] of rows.slice(1).entries()) {
    assert.deepEqual(row, { year: game.year + index + 1, games: null, starts: null, startShare: null, contribution: null });
  }
  assert.ok(playerDevelopment(game, [compacted], true).every(({ seasons }) => seasons.every(season => season.games === null)));
});

test('embargoed results withhold all player-level development', () => {
  assert.deepEqual(playerDevelopment(game, [featured, compacted], false), []);
});
