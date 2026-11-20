import test from 'node:test';
import assert from 'node:assert/strict';
import source2019 from '../data/processed/scenario-2019.json';
import source2021 from '../data/processed/scenario-2021.json';
import { applyTrade, createGame, validateGame } from '../lib/engine';
import { coverage, getScenario } from '../lib/server-data';
import type { Dataset } from '../lib/types';

const inclusive = (from: number, through: number) => Array.from({ length: through - from + 1 }, (_, index) => from + index);

test('runtime scenarios classify every 2019 and 2021 slot with contemporaneous evidence', () => {
    const sources = [
        [2019, source2019, [...inclusive(96, 102), ...inclusive(135, 138), ...inclusive(171, 173), ...inclusive(205, 214), ...inclusive(247, 254)]],
        [2021, source2021, [...inclusive(96, 105), ...inclusive(138, 144), ...inclusive(177, 184), ...inclusive(217, 228)]],
    ] as const;

    for (const [year, archive, slots] of sources) {
        const { dataset } = getScenario(year);
        assert.equal(dataset.metadata.version, archive.metadata.version);
        assert.equal(dataset.metadata.informationCutoff, archive.metadata.informationCutoff);
        assert.deepEqual(dataset.picks, archive.picks.map(pick => ({ ...pick, compensatory: slots.includes(pick.overall) })));
        assert.deepEqual(dataset.actualPicks, archive.actualPicks);
        assert.deepEqual(dataset.prospects, archive.prospects);
        const report = coverage.find(record => record.year === year);
        assert.ok(report?.compensatoryEvidence);
        assert.ok(!report.blockers.some(blocker => blocker.includes('unknown for 2019 and 2021')));
    }
});

test('the 2019 compensatory flag follows its slot across a trade and earlier saves still validate', () => {
    const { dataset, models } = getScenario(2019);
    const config = { year: 2019, team: 'ARI', seed: 'historical-compensatory-slot', modelVersion: models.version };
    const earlierSave = createGame(config, source2019 as unknown as Dataset);
    assert.equal(earlierSave.picks[95].compensatory, undefined);
    assert.equal(validateGame(earlierSave, dataset), true);

    const game = createGame(config, dataset);
    assert.deepEqual(game.picks[95], { overall: 96, round: 3, owner: 'WAS', compensatory: true });
    const changed = applyTrade(game, { target: 'WAS', give: [1], receive: [96] }, dataset);
    assert.deepEqual(changed.picks[95], { overall: 96, round: 3, owner: 'ARI', compensatory: true });
    assert.equal(game.picks[95].owner, 'WAS');
    assert.equal(dataset.picks[95].owner, 'WAS');
    assert.equal(dataset.actualPicks[95].team, 'BUF');
});

test('2020 uses the April 15 order snapshot and discloses the April 23 opening date', () => {
    const { dataset } = getScenario(2020);
    const report = coverage.find(record => record.year === 2020);
    assert.ok(report?.orderSnapshot);
    assert.equal(report.orderSnapshot.asOfDate, '2020-04-15');
    assert.equal(report.orderSnapshot.draftOpeningDate, '2020-04-23');
    assert.equal(report.orderSnapshot.openingOrderComplete, false);
    assert.equal(dataset.metadata.informationCutoff, '2020-04-15T23:59:00Z');
    assert.equal(dataset.picks[138].owner, 'TB');
    assert.equal(dataset.picks[240].owner, 'NE');
});
