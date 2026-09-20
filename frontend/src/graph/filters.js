export function normalizeGraphPayload(payload = {}) {
  return {
    nodes: Array.isArray(payload.nodes) ? payload.nodes : [],
    edges: Array.isArray(payload.edges) ? payload.edges : [],
    stats: payload.stats && typeof payload.stats === 'object' ? payload.stats : {},
  };
}

export function filterGraph(graph, filters) {
  const normalized = normalizeGraphPayload(graph);
  const nodes = normalized.nodes.filter((node) => filters.types.includes(node.type) && (filters.status === 'ALL' || node.status === filters.status));
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = normalized.edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target) && filters.relations.includes(edge.relation) && edge.confidence >= filters.minConfidence);
  const connected = new Set(edges.flatMap((edge) => [edge.source, edge.target]));
  return { nodes: nodes.filter((node) => connected.has(node.id) || node.type === 'DOCUMENT'), edges };
}

const RELATION_PRIORITY = {
  CONTRADICTS: 8,
  SUPPORTED_BY: 5,
  DEPENDS_ON: 3,
  PRECEDES: 2.5,
  MENTIONS: 2,
  HAS_VALUE: 1.8,
  CORRELATED_WITH: 1.4,
};

const NODE_PRIORITY = {
  CLAIM: 4,
  ENTITY: 2.5,
  DOCUMENT: 2.2,
  EVIDENCE: 2,
  EVENT: 1.8,
  VARIABLE: 1.5,
  VALUE: 1.2,
  DATASET: 1.2,
};

function components(nodes, edges) {
  const adjacency = new Map(nodes.map((node) => [node.id, new Set()]));
  edges.forEach((edge) => {
    adjacency.get(edge.source)?.add(edge.target);
    adjacency.get(edge.target)?.add(edge.source);
  });
  const seen = new Set();
  return nodes.reduce((groups, node) => {
    if (seen.has(node.id)) return groups;
    const group = [];
    const pending = [node.id];
    seen.add(node.id);
    while (pending.length) {
      const current = pending.pop();
      group.push(current);
      adjacency.get(current)?.forEach((next) => {
        if (!seen.has(next)) { seen.add(next); pending.push(next); }
      });
    }
    groups.push(group);
    return groups;
  }, []);
}

/**
 * Produce an evidence-first overview, not an indiscriminate node dump.
 * It keeps contradiction paths, high-confidence claim/evidence paths, and a
 * representative high-value node from every connected evidence cluster.
 */
export function curateGraph(graph, { maxNodes = 52, focusNodeId = null } = {}) {
  const normalized = normalizeGraphPayload(graph);
  if (normalized.nodes.length <= maxNodes || maxNodes < 1) return { ...normalized, hiddenNodes: 0, curated: false };

  const edgeScore = (edge) => (RELATION_PRIORITY[edge.relation] || 1) * (Number(edge.confidence) || 0);
  const rankedEdges = [...normalized.edges].sort((a, b) => edgeScore(b) - edgeScore(a));
  const score = new Map(normalized.nodes.map((node) => [node.id, NODE_PRIORITY[node.type] || 1]));
  rankedEdges.forEach((edge) => {
    const weight = edgeScore(edge);
    score.set(edge.source, (score.get(edge.source) || 0) + weight);
    score.set(edge.target, (score.get(edge.target) || 0) + weight);
  });
  normalized.nodes.forEach((node) => {
    if (node.status === 'CONTRADICTED') score.set(node.id, (score.get(node.id) || 0) + 10);
    if (node.status === 'SUPPORTED') score.set(node.id, (score.get(node.id) || 0) + 2);
  });

  const selected = new Set();
  const include = (id) => { if (id && selected.size < maxNodes) selected.add(id); };
  if (focusNodeId) {
    include(focusNodeId);
    rankedEdges.filter((edge) => edge.source === focusNodeId || edge.target === focusNodeId).slice(0, 14)
      .forEach((edge) => { include(edge.source); include(edge.target); });
  }

  // Contradictions are never hidden by the overview budget.
  rankedEdges.filter((edge) => edge.relation === 'CONTRADICTS').forEach((edge) => { include(edge.source); include(edge.target); });
  // Preserve the best representative from every evidence community before
  // filling the remaining budget with globally important nodes.
  const byId = new Map(normalized.nodes.map((node) => [node.id, node]));
  components(normalized.nodes, normalized.edges)
    .sort((a, b) => b.length - a.length)
    .forEach((group) => include([...group].sort((a, b) => (score.get(b) || 0) - (score.get(a) || 0))[0]));

  [...normalized.nodes].sort((a, b) => (score.get(b.id) || 0) - (score.get(a.id) || 0)).forEach((node) => include(node.id));

  // An edge only appears when both endpoints remain, so every visible line has
  // a readable semantic relationship rather than a dangling visual fragment.
  const nodes = normalized.nodes.filter((node) => selected.has(node.id));
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = rankedEdges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target));
  return { nodes, edges, stats: normalized.stats, hiddenNodes: normalized.nodes.length - nodes.length, curated: true, nodeScores: score, byId };
}
