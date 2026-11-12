import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { aliasCatalog, createScoutingPolicy, prospectViews, MEASUREMENTS, broadPosition, identityRevealed } from '../lib/scouting';
import { createGame, isPlayableProspect, projectionFor } from '../lib/engine';
import type { Dataset } from '../lib/types';
const dataset = JSON.parse(readFileSync('data/processed/scenario-2018.json', 'utf8')) as Dataset;
const models = JSON.parse(readFileSync('analytics/model.json', 'utf8'));
const policy = createScoutingPolicy(dataset, models);
const playable = dataset.prospects.filter(isPlayableProspect);
const fresh = () => createGame({ seed: 'scouting-test', now: '2026-11-02T00:00:00Z' }, dataset);
const salt = 'test-only-private-salt-000000000000000000';

test('all336 playable candidates have shared profiles of5–9; ST conceals the lone LS', () => {
    assert.equal(Object.keys(policy.profiles).length, 336);
    assert.equal(policy.audit.minimumGroupSize, 5);
    assert.ok(policy.audit.maximumGroupSize <= 9);
    assert.ok(policy.audit.initialJointProfileMinimum >= 5);
    for (const p of playable) assert.ok(policy.profiles[p.id].memberIds.length >= 5);
    for (const p of playable.filter(p => ['K', 'P', 'LS'].includes(p.position))) assert.equal(policy.profiles[p.id].position, 'ST');
});
test('every known individual measure is contained in its true shared outward-rounded range', () => {
    for (const p of playable) for (const m of MEASUREMENTS) {
        const value = p[m.field]; if (value === null) continue;
        const match = policy.profiles[p.id].displayMeasurements[m.display].match(/^([\d.]+)–([\d.]+)/);
        assert.ok(match); assert.ok(Number(match[1]) <= value && value <= Number(match[2]), `${p.id} ${m.field}`);
    }
});
test('aliases are stable, private-salt-dependent, one-to-one, and independent of reference-only membership', async () => {
    const a = await aliasCatalog(salt, dataset), b = await aliasCatalog(salt, dataset), c = await aliasCatalog(salt+'different', dataset);
    assert.deepEqual(a, b); assert.notDeepEqual(a, c); assert.equal(a.toPublic.size, dataset.prospects.length);
    const subset = await aliasCatalog(salt, { ...dataset, prospects: playable });
    for (const p of playable) { const id = a.toPublic.get(p.id)!; assert.notEqual(id, p.id); assert.equal(subset.toPublic.get(p.id), id); assert.equal(a.toCanonical.get(id), p.id); }
    await assert.rejects(aliasCatalog('public-seed', dataset), /private salt/);
});
test('full cumulative browser evidence has at least five identical profiles and no canonical fingerprints', async () => {
    const aliases = await aliasCatalog(salt, dataset), game = fresh(); game.scouted = playable.map(p => p.id);
    const views = prospectViews(game, dataset, models, policy, aliases), classes = new Map<string, number>();
    assert.equal(views.length, 336);
    for (const { id, name, blindName, scouted, ...view } of views) {
        assert.equal(name, blindName); assert.ok(id.startsWith('bp_')); assert.equal(scouted, true);
        assert.equal(view.college, 'Hidden until reveal');
        assert.ok(!('source' in view)); assert.ok(!('availableBy' in view)); assert.ok(!('missingMeasurements' in view.projection));
        for (const m of MEASUREMENTS) assert.equal(view[m.field], null);
        const key = JSON.stringify({ ...view, projection: { ...view.projection, prospectId: undefined } });
        classes.set(key, (classes.get(key) ?? 0) + 1);
    }
    assert.ok(Math.min(...classes.values()) >= 5);
    const json = JSON.stringify(views);
    for (const p of dataset.prospects) { assert.ok(!json.includes(p.id)); assert.ok(!json.includes(p.name)); }
});
test('pooling affects CPU/simulation inputs equally; specialist projection stays unavailable', () => {
    for (const p of playable) {
        const profile = policy.profiles[p.id], prediction = projectionFor(p, policy.pooledModels);
        if (broadPosition(p.position) === 'ST') { assert.equal(prediction.roleProbability, null); continue; }
        assert.equal(prediction.roleProbability, profile.pooledProbability);
        assert.ok(profile.probabilityBand!.lower <= profile.pooledProbability && profile.pooledProbability <= profile.probabilityBand!.upper);
        for (const id of profile.memberIds) assert.equal(policy.profiles[id].pooledProbability, profile.pooledProbability);
    }
});
test('future history, names, colleges, reference-only membership and source-row ordering cannot affect shared profiles', () => {
    const modified = { ...dataset, actualPicks: [], games: [], prospects: [...playable].reverse().map(p => ({ ...p, name: 'Anonymous', college: 'Suppressed' })) };
    assert.deepEqual(createScoutingPolicy(modified, models).profiles, policy.profiles);
});
test('scouting reveals only a range; end of draft reveals historical identity with stable aliases', async () => {
    const aliases = await aliasCatalog(salt, dataset), game = fresh(), p = playable.find(p => p.position === 'QB')!;
    const before = prospectViews(game, dataset, models, policy, aliases).find(x => x.id === aliases.toPublic.get(p.id))!;
    assert.equal(before.projection.roleProbability, null);
    game.scouted = [p.id]; const scouted = prospectViews(game, dataset, models, policy, aliases).find(x => x.id === before.id)!;
    assert.match(scouted.projection.roleProbabilityLabel, /^\d+–\d+%$/);
    game.status = 'ready'; const after = prospectViews(game, dataset, models, policy, aliases);
    assert.equal(after.length, 375); const reveal = after.find(x => x.id === before.id)!;
    assert.equal(reveal.name, p.name); assert.equal(reveal.college, p.college); assert.equal(reveal.heightIn, p.heightIn);
});
test('unsupported sparse position pool fails closed', () => {
    const sparse = { ...dataset, prospects: playable.filter(p => broadPosition(p.position) !== 'ST').concat(playable.filter(p => broadPosition(p.position) === 'ST').slice(0, 4)) };
    assert.throws(() => createScoutingPolicy(sparse, models), /Unsupported blind cohort/);
});

test('one scouting action reveals the entire shared profile without additional individual evidence', async () => {
    const aliases = await aliasCatalog(salt, dataset), game = fresh(), p = playable.find(p => p.position === 'QB')!;
    game.scouted = [p.id];
    const views = prospectViews(game, dataset, models, policy, aliases), members = policy.profiles[p.id].memberIds;
    for (const id of members) { const view = views.find(p => p.id === aliases.toPublic.get(id))!; assert.equal(view.scouted, true); assert.notEqual(view.projection.roleProbability, null); }
    assert.equal(game.scouted.length, 1);
});
test('daily identities remain sealed in ready, simulating and complete states until UTC rollover', async () => {
    const aliases = await aliasCatalog(salt, dataset), game = { ...fresh(), mode: 'daily' as const, createdAt: '2026-11-02T23:59:30Z' };
    for (const status of ['ready', 'simulating', 'complete'] as const) {
        game.status = status;
        for (const date of ['2026-11-02T00:00:00Z', '2026-11-02T23:59:59.999Z']) {
            assert.equal(identityRevealed(game, new Date(date)), false);
            const views = prospectViews(game, dataset, models, policy, aliases, new Date(date));
            assert.equal(views.length, 336); assert.ok(views.every(p => !p.identityRevealed && p.college === 'Hidden until reveal'));
            const json = JSON.stringify(views); for (const p of dataset.prospects) assert.ok(!json.includes(p.name));
        }
        const views = prospectViews(game, dataset, models, policy, aliases, new Date('2026-11-03T00:00:00Z'));
        assert.equal(identityRevealed(game, new Date('2026-11-03T00:00:00Z')), true);
        assert.equal(views.length, 375); assert.ok(views.every(p => p.identityRevealed));
    }
    game.status = 'drafting'; assert.equal(identityRevealed(game, new Date('2026-11-03T12:00:00Z')), false);
    game.status = 'complete'; game.createdAt = 'invalid'; assert.equal(identityRevealed(game, new Date('2026-11-03T12:00:00Z')), false);
});
