import test from 'node:test';
import assert from 'node:assert/strict';
import { filterGraph, normalizeGraphPayload } from './filters.js';

const filters = { types: ['CLAIM', 'EVIDENCE', 'DOCUMENT'], relations: ['SUPPORTED_BY'], minConfidence: 0.7, status: 'ALL' };

test('graph payload normalization and filtering retain only connected, allowed evidence', () => {
  const graph = normalizeGraphPayload({ nodes: [{ id: 'claim', type: 'CLAIM' }, { id: 'evidence', type: 'EVIDENCE' }, { id: 'entity', type: 'ENTITY' }], edges: [{ id: 'support', source: 'claim', target: 'evidence', relation: 'SUPPORTED_BY', confidence: 0.9 }, { id: 'mention', source: 'claim', target: 'entity', relation: 'MENTIONS', confidence: 0.9 }] });
  const result = filterGraph(graph, filters);
  assert.deepEqual(result.nodes.map((node) => node.id).sort(), ['claim', 'evidence']);
  assert.deepEqual(result.edges.map((edge) => edge.id), ['support']);
});
