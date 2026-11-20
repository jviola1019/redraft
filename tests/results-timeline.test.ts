import { strict as assert } from 'node:assert';
import test from 'node:test';
import { resultsTimeline } from '../components/redraft/results-timeline';
import type { SimulationResults } from '../lib/types';

function resultFixture() {
    const world = { seasons: [
        { year: 2025, teams: [{ team: 'CLE', wins: 0 }] },
        { year: 2027, teams: [{ team: 'CLE', wins: 8 }] }
    ] };
    return {
        actual: [
            { year: 2025, state: 'recorded', wins: 0 },
            { year: 2026, state: 'incomplete', wins: 4 },
            { year: 2027, state: 'future', wins: null }
        ],
        replicates: [{ baseline: world, alternate: world }]
    } as unknown as SimulationResults;
}

test('timeline distinguishes a recorded winless season, incomplete history and projections', () => {
    const rows = resultsTimeline(2025, 'CLE', resultFixture());
    assert.deepEqual(rows.map(row => row.actual), [0, null, null, null, null]);
    assert.deepEqual(rows.map(row => row.status), ['Recorded', 'Incomplete', 'Projection', 'Unavailable', 'Unavailable']);
    assert.deepEqual(rows.map(row => row.baseline), [0, null, 8, null, null]);
});

test('timeline withholds incomplete ensemble means and ignores another team’s record', () => {
    const result = resultFixture();
    result.replicates.push({ baseline: { seasons: [] }, alternate: { seasons: [] } } as unknown as SimulationResults['replicates'][number]);
    assert.equal(resultsTimeline(2025, 'CLE', result)[0].alternate, null);
    assert.equal(resultsTimeline(2025, 'KC', resultFixture())[0].baseline, null);
});
