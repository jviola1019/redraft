import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createGame } from '../lib/engine';
import { aliasCatalog, createScoutingPolicy, MEASUREMENTS, prospectDisclosure } from '../lib/scouting';
import type { Dataset } from '../lib/types';
const dataset = JSON.parse(readFileSync('data/processed/scenario-2018.json', 'utf8')) as Dataset;
const models = JSON.parse(readFileSync('analytics/model.json', 'utf8'));
const policy = createScoutingPolicy(dataset, models);
const game = { ...createGame({ mode: 'daily', now: '2026-11-02T23:59:59Z', seed: 'boundary-test' }, dataset), status: 'complete' as const };
const aliases = aliasCatalog('boundary-contract-private-fixture', dataset);

test('one disclosure snapshot seals every identifying field before midnight and reveals at midnight', async () => {
  const catalog = await aliases;
  const before = prospectDisclosure(game, dataset, models, policy, catalog, new Date('2026-11-02T23:59:59.999Z'));
  assert.equal(before.revealed, false);
  for (const prospect of before.prospects) {
    assert.equal(prospect.identityRevealed, before.revealed);
    assert.equal(prospect.name, prospect.blindName);
    assert.equal(prospect.college, 'Hidden until reveal');
    assert.equal('source' in prospect, false);
    assert.equal('availableBy' in prospect, false);
    for (const measurement of MEASUREMENTS) assert.equal(prospect[measurement.field], null);
    assert.match(prospect.id, /^bp_[a-f0-9]{32}$/);
  }
  const at = prospectDisclosure(game, dataset, models, policy, catalog, new Date('2026-11-03T00:00:00.000Z'));
  assert.equal(at.revealed, true);
  for (const prospect of at.prospects) {
    assert.equal(prospect.identityRevealed, at.revealed);
    const canonical = catalog.toCanonical.get(prospect.id);
    const source = dataset.prospects.find(row => row.id === canonical)!;
    assert.equal(prospect.name, source.name);
    assert.equal(prospect.college, source.college);
    assert.equal(prospect.source, source.source);
    for (const measurement of MEASUREMENTS) assert.equal(prospect[measurement.field], source[measurement.field]);
  }
});
test('reconnecting reconstructs the same disclosure and aliases without mutating saved state', async () => {
  const saved = JSON.stringify(game), catalog = await aliases;
  const now = new Date('2026-11-03T12:00:00Z');
  const original = prospectDisclosure(game, dataset, models, policy, catalog, now);
  const reconnected = prospectDisclosure(JSON.parse(saved), dataset, models, policy, await aliasCatalog('boundary-contract-private-fixture', dataset), now);
  assert.deepEqual(reconnected, original);
  assert.equal(JSON.stringify(game), saved);
});
test('UTC-normalized timestamps and incomplete runs fail closed consistently', async () => {
  const catalog = await aliases;
  for (const createdAt of ['invalid', '2026-11-03T01:00:00+01:00', '2026-11-04T00:00:00Z']) {
    const disclosure = prospectDisclosure({ ...game, createdAt }, dataset, models, policy, catalog, new Date('2026-11-03T00:00:00Z'));
    assert.equal(disclosure.revealed, false);
    assert.ok(disclosure.prospects.every(prospect => !prospect.identityRevealed));
  }
  const unfinished = prospectDisclosure({ ...game, status: 'drafting' }, dataset, models, policy, catalog, new Date('2026-11-03T12:00:00Z'));
  assert.equal(unfinished.revealed, false);
});
test('a projection reads the clock once even when successive clock reads cross midnight', async () => {
  const catalog = await aliases, NativeDate = Date;
  let clockReads = 0;
  class BoundaryDate extends NativeDate {
    constructor(value?: string | number) {
      super(value === undefined ? NativeDate.parse('2026-11-02T23:59:59.999Z') + clockReads++ : value);
    }
  }
  try {
    globalThis.Date = BoundaryDate as DateConstructor;
    const disclosure = prospectDisclosure(game, dataset, models, policy, catalog);
    assert.equal(clockReads, 1);
    assert.equal(disclosure.revealed, false);
    assert.ok(disclosure.prospects.every(prospect => !prospect.identityRevealed));
  } finally { globalThis.Date = NativeDate; }
});
