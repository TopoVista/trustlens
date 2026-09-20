import test from 'node:test';
import assert from 'node:assert/strict';
import { curateGraph, filterGraph, normalizeGraphPayload } from './filters.js';

const filters = { types: ['CLAIM', 'EVIDENCE', 'DOCUMENT'], relations: ['SUPPORTED_BY'], minConfidence: 0.7, status: 'ALL' };

test('graph payload normalization and filtering retain only connected, allowed evidence', () => {
  const graph = normalizeGraphPayload({ nodes: [{ id: 'claim', type: 'CLAIM' }, { id: 'evidence', type: 'EVIDENCE' }, { id: 'entity', type: 'ENTITY' }], edges: [{ id: 'support', source: 'claim', target: 'evidence', relation: 'SUPPORTED_BY', confidence: 0.9 }, { id: 'mention', source: 'claim', target: 'entity', relation: 'MENTIONS', confidence: 0.9 }] });
  const result = filterGraph(graph, filters);
  assert.deepEqual(result.nodes.map((node) => node.id).sort(), ['claim', 'evidence']);
  assert.deepEqual(result.edges.map((edge) => edge.id), ['support']);
});

test('curated graph preserves high-priority contradiction paths within a node budget', () => {
  const nodes = Array.from({ length: 60 }, (_, index) => ({ id: `n${index}`, type: index < 2 ? 'CLAIM' : 'ENTITY', label: `Node ${index}` }));
  const edges = nodes.slice(2).map((node, index) => ({ id: `e${index}`, source: 'n0', target: node.id, relation: 'MENTIONS', confidence: 0.55 }));
  edges.push({ id: 'contradiction', source: 'n0', target: 'n1', relation: 'CONTRADICTS', confidence: 0.95 });
  const curated = curateGraph({ nodes, edges, stats: {} }, { maxNodes: 12 });
  assert.equal(curated.curated, true);
  assert.ok(curated.nodes.length <= 12);
  assert.ok(curated.edges.some((edge) => edge.id === 'contradiction'));
});
