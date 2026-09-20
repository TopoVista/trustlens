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
