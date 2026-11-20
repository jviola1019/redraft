import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { after, test } from 'node:test';
import { cleanup } from '../runtime_loader.mjs';
import { aggregate, perturbations, rankings, validateFixtures } from './audit.mjs';
import { generateFixtures, verifyProtocol } from './runtime.mjs';

after(cleanup);

test('frozen fixture frame is reproducible through the authoritative route', async () => {
  const snapshot = JSON.parse(readFileSync(new URL('./fixtures.json', import.meta.url)));
  const recorded = validateFixtures(snapshot);
  const rerun = await generateFixtures();
  const pins = contests => contests.map(({ seed, blindSalt, ...day }) => day);
  assert.deepEqual(pins(recorded), pins(rerun));
  assert.notDeepEqual(recorded.map(row => row.seed), rerun.map(row => row.seed));
  assert.notDeepEqual(recorded.map(row => row.blindSalt), rerun.map(row => row.blindSalt));
  assert.equal(new Set(rerun.flatMap(row => [row.seed, row.blindSalt])).size, 12);
});

test('weight perturbation renormalizes the changed and unchanged inputs', () => {
  const variants = perturbations([{ name: 'A', weight: 0.4 }, { name: 'B', weight: 0.6 }]);
  assert.equal(variants.length, 5);
  assert.deepEqual(variants[0].weights, [0.4, 0.6]);
  for (const row of variants) assert.ok(Math.abs(row.weights.reduce((a, b) => a + b, 0) - 1) < 1e-10);
  assert.ok(Math.abs(variants[1].weights[0] - 0.25) < 1e-10);
});

test('rounding and tied leaderboard metrics reconcile with the engine', () => {
  const build = (name, first, second, decisionScore) => ({
    name, decisionScore,
    scoreComponents: [{ name: 'A', weight: 0.5, score: first }, { name: 'B', weight: 0.5, score: second }],
  });
  const rows = [build('Alpha', 54, 46, 50), build('Beta', 43, 58.2, 51), build('Gamma', 49, 52, 51)];
  const scored = rankings(rows);
  assert.deepEqual(scored[0].official.topPolicySet, ['Beta', 'Gamma']);
  assert.equal(scored[0].ranking.find(row => row.name === 'Alpha').sharedRank, 3);
  assert.deepEqual(scored[1].official.topPolicySet, ['Beta']);
  assert.equal(scored[1].official.topPolicyChanged, true);
  assert.equal(scored[1].raw.topPolicyChanged, false);
  const constant = rankings(rows.map(row => build(row.name, 50, 50, 50)));
  assert.equal(constant[0].official.spearmanToDefault, null);
  assert.equal(constant[1].official.topPolicyChanged, false);
  assert.throws(() => rankings([build('Wrong score', 50, 50, 49)]), /Wrong score/);
});

test('published audit has complete draws, comparisons and consistent aggregate counts', () => {
  const { days, summary, fixtureSha256, protocolSha256 } = JSON.parse(readFileSync(new URL('./results.json', import.meta.url)));
  const fixtures = readFileSync(new URL('./fixtures.json', import.meta.url));
  assert.equal(fixtureSha256, createHash('sha256').update(fixtures).digest('hex'));
  assert.equal(protocolSha256, verifyProtocol());
  assert.deepEqual(aggregate(days), summary);
  assert.equal(summary.perturbationComparisons, 60);
  for (const day of days) {
    for (const [slice, records] of Object.entries(day.summaries)) {
      assert.equal(records.length, 4);
      assert.ok(records.every(row => row.pairedWins.samples === (slice === 'full' ? 256 : 128)));
      assert.deepEqual(rankings(records), day.rankings[slice]);
      for (const [index, row] of records.entries()) {
        const full = day.summaries.full[index];
        assert.equal(row.name, full.name);
        assert.deepEqual(row.selections, full.selections);
        assert.equal(row.reportsUnlocked, index === 0 ? 0 : 12);
        assert.deepEqual(row.scoreComponents.filter(c => c.name !== 'Paired five-year difference'),
          full.scoreComponents.filter(c => c.name !== 'Paired five-year difference'));
      }
    }
  }
});
