import test from 'node:test';
import assert from 'node:assert/strict';
import { guideReply, resolveGuideTarget } from './uiManifest.js';

test('guide manifest only resolves declared, safe UI targets', () => {
  assert.equal(resolveGuideTarget('knowledge_map').action, 'navigateGraph');
  assert.equal(resolveGuideTarget('invented-control'), null);
});

test('guide returns a safe unknown-target fallback', () => {
  const reply = guideReply('Where is the imaginary delete everything action?', { documents: 1 });
  assert.equal(reply.target, null);
  assert.match(reply.text, /only point to controls/i);
});
