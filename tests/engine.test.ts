import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createGame, advance, select, scout, setBoard, isPlayableProspect, autoComplete, applyTrade, proposeTrade, validateGame, projectionFor, probability, RULE_VERSION } from '../lib/engine';
import { generateSchedule, scoreGame, simulateReplicate, compactReplicate, summarizeResults, timelineState } from '../lib/simulation';
import type { Dataset, TeamSeason } from '../lib/types';
const dataset = JSON.parse(readFileSync('data/clean/scenario_2018.json', 'utf8')) as Dataset;
const models = JSON.parse(readFileSync('analytics/model.json', 'utf8'));
const game = () => createGame({ id: 'test-run', team: 'CLE', seed: '2018-QA', now: '2026-11-02T00:00:00Z' }, dataset);
const standings: TeamSeason[] = dataset.teams.map(t => ({ team: t.id, wins: t.priorWins, losses: t.priorLosses, ties: t.priorTies, pointsFor: t.priorPointsFor, pointsAgainst: t.priorPointsAgainst, playoff: false, seed: null, conferenceChampion: false, champion: false }));
const complete = autoComplete(game(), dataset, models), replicate = simulateReplicate(complete, 0, dataset, models);
test('real scenario has32 teams, seven rounds and256 unique selections', () => { assert.equal(dataset.teams.length, 32); assert.equal(dataset.picks.length, 256); assert.equal(new Set(dataset.picks.map(p => p.round)).size, 7); assert.equal(new Set(dataset.prospects.map(p => p.id)).size, dataset.prospects.length); });
test('seven rounds finish with unique players, ownership and budget invariants', () => { assert.equal(complete.status, 'ready'); assert.equal(complete.selections.length, 256); assert.equal(new Set(complete.selections.map(p => p.prospectId)).size, 256); assert.equal(validateGame(complete, dataset), true); assert.equal(complete.ensembleSize, 256); assert.equal(complete.engineVersion, RULE_VERSION); });
test('identical config repeats the same draft', () => assert.deepEqual(autoComplete(game(), dataset, models), complete));
test('different seeds produce different choices', () => { const other = autoComplete(createGame({ team: 'CLE', seed: 'different', now: '2026-11-02T00:00:00Z' }, dataset), dataset, models); assert.notDeepEqual(other.selections, complete.selections); });
test('future and invalid availability timestamps are rejected', () => { for (const availableBy of ['2018-04-27T00:00:00Z', 'invalid']) {
    const changed = { ...dataset, prospects: dataset.prospects.map((p, i) => i === 0 ? { ...p, availableBy } : p) };
    assert.throws(() => select(game(), changed.prospects[0].id, changed), /cutoff/);
} });
test('future actual selections and scores cannot enter CPU choices', () => { const changed = { ...dataset, actualPicks: [...dataset.actualPicks].reverse(), games: dataset.games.map(g => ({ ...g, homeScore: 99, awayScore: 0 })) }; assert.deepEqual(autoComplete(game(), changed, models).selections, complete.selections); });
test('only336 combine participants can be selected, scouted or shortlisted', () => { const playable = dataset.prospects.filter(isPlayableProspect), baselineOnly = dataset.prospects.filter(p => !isPlayableProspect(p)); assert.equal(playable.length, 336); assert.equal(baselineOnly.length, 39); for (const p of baselineOnly) {
    assert.throws(() => select(game(), p.id, dataset), /playable/);
    assert.throws(() => scout(game(), p.id, dataset), /playable/);
    assert.throws(() => setBoard(game(), [p.id], dataset), /Invalid board/);
} assert.ok(complete.selections.every(s => playable.some(p => p.id === s.prospectId))); });
test('retrospective prospect membership cannot influence CPU policy', () => { const clean = { ...dataset, prospects: dataset.prospects.filter(isPlayableProspect) }, g = createGame({ id: 'test-run', team: 'CLE', seed: '2018-QA', now: '2026-11-02T00:00:00Z' }, clean); assert.deepEqual(autoComplete(g, clean, models).selections, complete.selections); });
test('duplicate player selections fail', () => { const first = select(game(), dataset.prospects[0].id, dataset), next = advance(first, dataset, models); assert.throws(() => select(next, dataset.prospects[0].id, dataset), /already/); });
test('scouting is charged once and never changes prospect talent or RNG', () => { const g = game(), p = dataset.prospects.find(isPlayableProspect)!, original = JSON.stringify(p); let a = scout(g, p.id, dataset); a = scout(a, p.id, dataset); assert.equal(a.scoutingPoints, 11); assert.equal(JSON.stringify(p), original); assert.deepEqual(autoComplete(a, dataset, models).selections, complete.selections); });
test('scouting budget cannot be negative', () => { let a = game(); const pool = dataset.prospects.filter(isPlayableProspect); for (const p of pool.slice(0, 12))
    a = scout(a, p.id, dataset); assert.throws(() => scout(a, pool[12].id, dataset), /credits/); });
test('accepted trades conserve assets atomically and leave input unchanged', () => { const g = game(), offer = { target: 'NYG', give: [1], receive: [2] }; assert.equal(proposeTrade(g, offer, dataset).accepted, true); const a = applyTrade(g, offer, dataset); assert.equal(a.picks[0].owner, 'NYG'); assert.equal(a.picks[1].owner, 'CLE'); assert.equal(validateGame(a, dataset), true); assert.equal(g.picks[0].owner, 'CLE'); assert.throws(() => applyTrade(a, offer, dataset), /own/); });
test('duplicate trade assets and invalid future selections fail', () => { assert.throws(() => proposeTrade(game(), { target: 'NYG', give: [1, 1], receive: [2] }, dataset), /Duplicate/); assert.throws(() => proposeTrade(game(), { target: 'NYG', give: [999], receive: [2] }, dataset), /own/); });
test('corrupted persisted eligibility, dates, board and status fail invariants', () => { const forbidden = dataset.prospects.find(p => !isPlayableProspect(p))!, first = complete.selections[0]; assert.throws(() => validateGame({ ...complete, selections: [{ ...first, prospectId: forbidden.id }, ...complete.selections.slice(1)] }, dataset), /eligibility/); assert.throws(() => validateGame({ ...game(), status: 'ready' }, dataset), /status/); assert.throws(() => validateGame({ ...complete, status: 'drafting' }, dataset), /status/); assert.throws(() => validateGame({ ...game(), cutoff: '2030-01-01' }, dataset), /cutoff/); assert.throws(() => validateGame({ ...game(), board: [forbidden.id] }, dataset), /board/); assert.throws(() => validateGame({ ...game(), scouted: [forbidden.id], scoutingPoints: 11 }, dataset), /budget/); });
test('five schedules preserve team counts, divisional opponents and one game/week', () => { for (let year = 2018; year <= 2022; year++) {
    const s = generateSchedule(year, dataset, standings), n = year < 2021 ? 16 : 17;
    assert.equal(s.length, 32 * n / 2);
    for (const t of dataset.teams) {
        const own = s.filter(g => g.home === t.id || g.away === t.id);
        assert.equal(own.length, n);
        assert.equal(new Set(own.map(g => g.week)).size, n);
        assert.ok(own.every(g => g.home !== g.away));
        for (const rival of dataset.teams.filter(p => p.conference === t.conference && p.division === t.division && p.id !== t.id))
            assert.equal(own.filter(g => g.home === rival.id || g.away === rival.id).length, 2);
    }
} });
test('five-season worlds reproduce and league/playoff invariants reconcile', () => { assert.deepEqual(simulateReplicate(complete, 0, dataset, models), replicate); for (const world of [replicate.baseline, replicate.alternate]) {
    assert.equal(world.seasons.length, 5);
    for (const s of world.seasons) {
        assert.equal(s.teams.reduce((n, t) => n + t.wins, 0), s.teams.reduce((n, t) => n + t.losses, 0));
        assert.equal(s.teams.filter(t => t.champion).length, 1);
        assert.equal(s.teams.filter(t => t.playoff).length, s.year >= 2020 ? 14 : 12);
        assert.equal(s.teams.filter(t => t.conferenceChampion).length, 2);
        assert.ok(s.players.every(p => p.starts <= p.games && p.games <= (s.year >= 2021 ? 17 : 16) && p.contribution >= 0));
        for (const t of s.teams)
            assert.equal(t.wins + t.losses + t.ties, s.year >= 2021 ? 17 : 16);
        assert.ok(s.games.every(g => g.homeScore >= 0 && g.awayScore >= 0 && g.homeScore !== 1 && g.awayScore !== 1));
    }
} });
// Explicit test-only eligibility fixture isolates common-random-number identity from production pool restrictions.
test('identical baseline allocations have zero paired effect', () => { const actual = { ...complete, selections: dataset.actualPicks.map(p => ({ ...p })), picks: dataset.actualPicks.map(p => ({ overall: p.overall, round: p.round, owner: p.team })), trades: [] }, start = { ...dataset, picks: actual.picks, prospects: dataset.prospects.map(p => ({ ...p, eligibilitySource: 'combine-participant' })) }, r = simulateReplicate(actual, 0, start, models); assert.deepEqual(r.baseline.seasons.map(s => s.teams), r.alternate.seasons.map(s => s.teams)); assert.equal(r.baseline.totalWins, r.alternate.totalWins); });
test('opposite venue games have independent score shocks', () => { const model = { initial: { CLE: 0, PIT: 0 }, home: 2.1, coefficient: .4, total: 44, marginSd: 14, totalSd: 10, rho: 0, persistence: .4, innovation: 4.7 }; let different = 0; for (let i = 0; i < 20; i++) {
    const a = scoreGame('CLE', 'PIT', 2018, 1, 'REG', { CLE: 0, PIT: 0 }, 'qa-' + i, model), b = scoreGame('PIT', 'CLE', 2018, 2, 'REG', { CLE: 0, PIT: 0 }, 'qa-' + i, model);
    if (a.homeScore !== b.homeScore || a.awayScore !== b.awayScore)
        different++;
} assert.ok(different > 15); });
test('256 compact replicates fit authoritative storage budget', () => { const reps = [replicate, ...Array.from({ length: 255 }, (_, i) => compactReplicate({ ...replicate, index: i + 1 }, complete.team))], results = summarizeResults(complete, reps, dataset, models); assert.equal(results.summary.samples, 256); const size = JSON.stringify({ ...complete, results }).length; assert.ok(size < 1800000, `State has ${size} bytes`); assert.ok(reps[1].alternate.seasons.every(s => s.games.length === 0 && s.teams.length === 1)); assert.throws(() => summarizeResults(complete, [replicate, replicate], dataset, models), /Duplicate/); });
test('timeline identifies incomplete and future seasons', () => { const now = new Date('2026-11-02T00:00:00Z'); assert.equal(timelineState(2026, now), 'incomplete'); assert.equal(timelineState(2027, now), 'future'); assert.equal(timelineState(2025, now), 'recorded'); });
test('supported probabilities are bounded; specialists remain unavailable', () => { for (const p of dataset.prospects) {
    const pred = projectionFor(p, models);
    if (pred.roleProbability !== null)
        assert.ok(pred.roleProbability > 0 && pred.roleProbability < 1);
    if (['K', 'P', 'LS'].includes(p.position))
        assert.equal(pred.roleProbability, null);
    assert.equal(pred.uncertainty, null);
    assert.ok(probability(p, models) > 0 && probability(p, models) < 1);
} });
console.log('BENCHMARK', JSON.stringify({ node: process.version, engine: RULE_VERSION, draftSelections: complete.selections.length, replicateSerializedBytes: JSON.stringify(replicate).length }));
