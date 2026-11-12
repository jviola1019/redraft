import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { createGame, autoComplete, positionGroup } from '../lib/engine';
import type { Dataset } from '../lib/types';
const donors = JSON.parse(readFileSync('analytics/five_year_strict_2018.json', 'utf8'));
const donorPositions = new Set(donors.donors.map((d: {position: string}) => d.position));

for (const file of readdirSync('data/processed').filter(f => /^scenario-\d{4}\.json$/.test(f))) {
    const dataset = JSON.parse(readFileSync(`data/processed/${file}`, 'utf8')) as Dataset;
    const year = Number(dataset.metadata.draftYear ?? dataset.metadata.year);
    test(`${year} source scenario has coherent eligible identities, ownership and recorded scores`, () => {
        assert.equal(dataset.teams.length, 32);
        assert.equal(new Set(dataset.teams.map(t => t.id)).size, 32);
        assert.equal(new Set(dataset.prospects.map(p => p.id)).size, dataset.prospects.length);
        assert.equal(new Set(dataset.picks.map(p => p.round)).size, 7);
        assert.deepEqual(dataset.picks.map(p => p.overall), Array.from({length:dataset.picks.length}, (_, i) => i + 1));
        assert.ok(dataset.picks.every(p => dataset.teams.some(t => t.id === p.owner)));
        assert.equal(dataset.actualPicks.length, dataset.picks.length);
        assert.equal(new Set(dataset.actualPicks.map(p => p.prospectId)).size, dataset.actualPicks.length);
        for (const p of dataset.prospects) {
            assert.ok(Date.parse(p.availableBy) <= Date.parse(String(dataset.metadata.informationCutoff)));
            const group = positionGroup(p.position);
            assert.ok(donorPositions.has(group) || ['K','P','LS'].includes(group), `Unsupported development group: ${p.position} → ${group}`);
        }
        for (const g of dataset.games) {
            assert.ok(Number.isInteger(g.homeScore) && g.homeScore >= 0);
            assert.ok(Number.isInteger(g.awayScore) && g.awayScore >= 0);
        }
    });
    test(`${year} draft policy ignores poisoned post-cutoff actuals`, () => {
        const config = { team: dataset.teams[0].id, seed: 'cutoff-poison-regression', now: '2026-11-12T00:00:00Z' };
        const original = autoComplete(createGame(config, dataset), dataset);
        const poisoned = structuredClone(dataset);
        poisoned.actualPicks.reverse();
        for (const g of poisoned.games.filter(g => g.season >= year)) { g.homeScore = 999; g.awayScore = 0; }
        assert.deepEqual(autoComplete(createGame(config, poisoned), poisoned), original);
    });
}
