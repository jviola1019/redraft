import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { after, test } from 'node:test';
import { aggregate, pairedSummary } from './audit.mjs';
import { cleanup, engine } from '../runtime_loader.mjs';

after(cleanup);

const read = path => readFileSync(new URL(path, import.meta.url));
const digest = path => createHash('sha256').update(read(path)).digest('hex');
const json = path => JSON.parse(read(path));

test('frozen feasibility artifact reconciles offer counts and price/position constraints', () => {
  const { days, summary, fixtureSha256, protocolSha256 } = json('./feasibility.json');
  const { fixtures } = json('../rubric_multiday/fixtures.json');
  assert.equal(fixtureSha256, digest('../rubric_multiday/fixtures.json'));
  assert.equal(protocolSha256, digest('./PROTOCOL.md'));
  assert.deepEqual(days.map(day => day.date), fixtures.map(row => row.date));
  assert.deepEqual(aggregate(days), summary);
  for (const day of days) {
    for (const [direction, market] of Object.entries(day.markets)) {
      const { counts, chosen, declinesByReason } = market;
      assert.equal(counts.structural, counts.aboveRatioCap + counts.withinRatioCap);
      assert.equal(counts.withinRatioCap, counts.approved + counts.declined);
      assert.equal(counts.declined, Object.values(declinesByReason).reduce((sum, value) => sum + value, 0));
      assert.equal(!!chosen, counts.approved > 0);
      if (!chosen) continue;
      assert.ok(chosen.move > 0 && chosen.move <= 32);
      assert.equal(chosen.evaluation.accepted, true);
      assert.ok(chosen.evaluation.ratio <= 1.35);
      const { give, receive } = chosen.offer;
      const capitalize = picks => picks.reduce((sum, slot) => sum + engine.pickValue(slot), 0);
      assert.equal(chosen.evaluation.giveValue, capitalize(give));
      assert.equal(chosen.evaluation.receiveValue, capitalize(receive));
      assert.ok(capitalize(give) > capitalize(receive));
      if (direction === 'up') {
        assert.equal(market.selectionCount, 0);
        assert.ok(give.length === 2 || give.length === 3);
        assert.equal(receive.length, 1);
        assert.equal(give[0] - receive[0], chosen.move);
      } else {
        assert.equal(give[0], market.atPick);
        assert.equal(give.length, 1);
        assert.ok(receive.length === 2 || receive.length === 3);
        assert.equal(receive[0] - give[0], chosen.move);
      }
    }
  }
});

test('paired path summary uses sample standard error and interpolated quantiles', () => {
  const summary = pairedSummary([5, -2, 0, 1, -4]);
  assert.equal(summary.mean, 0);
  assert.ok(Math.abs(summary.p10 - (-3.2)) < 1e-12);
  assert.ok(Math.abs(summary.p90 - 3.4) < 1e-12);
  assert.ok(Math.abs(summary.standardError - Math.sqrt(46 / 20)) < 1e-12);
  assert.deepEqual([summary.positive, summary.zero, summary.negative], [2, 1, 2]);
});

test('published score and win contrasts reconcile to the official components and paired paths', () => {
  const { days, summary, sourceHashes } = json('./results.json');
  const feasibility = json('./feasibility.json');
  assert.equal(sourceHashes['./audit.mjs'], digest('./audit.mjs'));
  assert.deepEqual(days.map(({ date, team, year, markets }) => ({ date, team, year, markets })), feasibility.days);
  assert.deepEqual(aggregate(days), summary);
  for (const day of days) {
    for (const [direction, row] of Object.entries(day.comparisons)) {
      const paths = row.pairedDeltasVsNoTrade;
      assert.equal(paths.length, 256);
      for (const [slice, subset] of Object.entries({ full: paths, first: paths.slice(0, 128), second: paths.slice(128) })) {
        const reference = day.noTrade[slice];
        const candidate = row[slice];
        assert.equal(candidate.pairedWinsVsHistory.samples, subset.length);
        for (const arm of [reference, candidate]) {
          assert.equal(arm.decisionScore, Math.round(arm.scoreComponents.reduce(
            (total, component) => total + component.score * component.weight, 0,
          )));
        }
        assert.equal(candidate.difference.decisionScore, candidate.decisionScore - reference.decisionScore);
        assert.deepEqual(candidate.difference.pairedWinsVsNoTrade, pairedSummary(subset));
        if (!day.markets[direction].chosen) assert.ok(subset.every(value => value === 0));
      }
    }
  }
});
