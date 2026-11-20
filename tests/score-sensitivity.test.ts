import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionScoreSensitivity} from '../lib/score-sensitivity';

const component = (score: number, weight: number) => ({name: 'Test component', score, weight, explanation: ''});

test('decision score sensitivity uses independent normalized perturbations and whole scores', () => {
  assert.deepEqual(decisionScoreSensitivity(50, [component(0, 0.5), component(100, 0.5)]), {low: 33, high: 67});
});

test('decision score sensitivity handles tied rounded results, zero score and zero weight', () => {
  assert.deepEqual(decisionScoreSensitivity(50, [component(49.6, 0.5), component(50.4, 0.5)]), {low: 50, high: 50});
  assert.deepEqual(decisionScoreSensitivity(0, [component(0, 1), component(100, 0)]), {low: 0, high: 0});
});

test('decision score sensitivity is unavailable when a legacy rubric cannot reproduce the official score', () => {
  assert.equal(decisionScoreSensitivity(50), null);
  assert.equal(decisionScoreSensitivity(50, []), null);
  assert.equal(decisionScoreSensitivity(50, [component(100, 0.5)]), null);
  assert.equal(decisionScoreSensitivity(50, [component(51, 1)]), null);
  assert.equal(decisionScoreSensitivity(50, [component(NaN, 1)]), null);
});
