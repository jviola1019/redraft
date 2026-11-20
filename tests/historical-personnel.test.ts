import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { getHistoricalPersonnel } from '../lib/historical-personnel';

test('pre-draft personnel is available only for its verified team and year', () => {
  assert.ok(getHistoricalPersonnel(2025, 'CLE'));
  assert.equal(getHistoricalPersonnel(2018, 'CLE'), undefined);
  assert.equal(getHistoricalPersonnel(2024, 'CLE'), undefined);
  assert.equal(getHistoricalPersonnel(2025, 'NYG'), undefined);
});

test('each Cleveland pre-draft fact has a dated primary source through the cutoff', () => {
  const snapshot = getHistoricalPersonnel(2025, 'CLE')!;
  assert.equal(snapshot.through, '2025-04-23');
  for (const group of snapshot.groups) {
    assert.ok(group.facts.length > 0);
    for (const fact of group.facts) {
      assert.match(fact.publishedOn, /^2025-\d{2}-\d{2}$/);
      assert.ok(fact.publishedOn <= snapshot.through, fact.label);
      const url = new URL(fact.url);
      assert.equal(url.protocol, 'https:');
      assert.ok(['www.clevelandbrowns.com', 'www.giants.com'].includes(url.hostname), fact.label);
    }
  }
});
