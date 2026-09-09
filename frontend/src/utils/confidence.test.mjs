import assert from 'node:assert/strict';
import test from 'node:test';

import { toConfidencePercent } from './confidence.js';

test('formats ratio and percentage confidence values without double-scaling', () => {
  assert.equal(toConfidencePercent(0.941), 94);
  assert.equal(toConfidencePercent(94.1), 94);
  assert.equal(toConfidencePercent(100), 100);
});

test('clamps malformed confidence values to a safe display range', () => {
  assert.equal(toConfidencePercent(-5), 0);
  assert.equal(toConfidencePercent(150), 100);
  assert.equal(toConfidencePercent('not-a-number'), 0);
});
