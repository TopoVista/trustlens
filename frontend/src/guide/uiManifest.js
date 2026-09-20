export const GUIDE_TARGETS = Object.freeze({
  add_source: { id: 'add_source', selector: '[data-guide-id="add-source"]', label: 'Add source material', action: 'openIngest' },
  verify: { id: 'verify', selector: '[data-guide-id="nav-query"]', label: 'Verify an answer', action: 'navigateQuery' },
  documents: { id: 'documents', selector: '[data-guide-id="nav-documents"]', label: 'Documents', action: 'navigateDocuments' },
  knowledge_map: { id: 'knowledge_map', selector: '[data-guide-id="nav-graph"]', label: 'Knowledge map', action: 'navigateGraph' },
  evidence_health: { id: 'evidence_health', selector: '[data-guide-id="nav-health"]', label: 'Evidence health', action: 'navigateHealth' },
});

export function resolveGuideTarget(targetId) {
  return GUIDE_TARGETS[targetId] || null;
}

export function guideReply(question, context = {}) {
  const text = (question || '').toLowerCase();
  if (/(upload|add|ingest|source)/.test(text)) return { text: 'Add a note, Markdown file, CSV, or text document here. Choose its authority level so retrieval can weight the source transparently.', target: 'add_source' };
  if (/(verify|claim|evidence|support)/.test(text)) return { text: context.documents > 0 ? 'Ask a focused question in the evidence desk. TrustLens retrieves relevant passages, checks atomic claims, and keeps the evidence beside the answer.' : 'First add source material. Verification needs a workspace record to retrieve and inspect.', target: context.documents > 0 ? 'verify' : 'add_source' };
  if (/(graph|map|connect|relationship|contradict)/.test(text)) return { text: context.documents > 0 ? 'Open Knowledge map to inspect the curated evidence view. Select any node to open its provenance and immediate evidence neighborhood; use search or Show all when you need the full record.' : 'The map becomes useful after documents provide claims, entities, events, or structured variables.', target: 'knowledge_map' };
  if (/(document|authority|id|source register)/.test(text)) return { text: 'Documents keeps the persistent source register, including document ID, declared authority, and ingestion status.', target: 'documents' };
  if (/(health|gap|unknown)/.test(text)) return { text: 'Evidence health summarizes support, unresolved claims, contradictions, and gaps in the active workspace.', target: 'evidence_health' };
  return { text: 'I can guide you to add source material, verify a claim, inspect evidence health, or explore the knowledge map. I only point to controls that exist in this workspace.', target: null };
}
