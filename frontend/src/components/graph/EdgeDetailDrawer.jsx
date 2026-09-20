import React from 'react';
import { Link2, X } from 'lucide-react';

export default function EdgeDetailDrawer({ edge, nodes, onClose }) {
  if (!edge) return null;
  const source = nodes.find((node) => node.id === edge.source);
  const target = nodes.find((node) => node.id === edge.target);
  return <aside className="tl-edge-drawer"><button className="tl-drawer-close" onClick={onClose} aria-label="Close edge details"><X className="h-4 w-4" /></button><p className="editorial-kicker tl-status"><Link2 className="mr-1 inline h-3 w-3" />Relationship</p><h4>{edge.relation.replaceAll('_', ' ')}</h4><p className="tl-edge-route">{source?.label || 'Source'} <span>→</span> {target?.label || 'Target'}</p><dl><div><dt>Confidence</dt><dd>{Math.round(edge.confidence * 100)}%</dd></div><div><dt>Method</dt><dd>{edge.provenance?.method || 'HEURISTIC'}</dd></div>{edge.provenance?.document_id && <div><dt>Source document</dt><dd>{edge.provenance.document_id}</dd></div>}{edge.provenance?.chunk_id && <div><dt>Passage</dt><dd>{edge.provenance.chunk_id}</dd></div>}</dl><p className="tl-edge-explanation">{edge.explanation || 'No explanatory note is available for this relationship.'}</p>{edge.provenance?.metadata?.coefficient !== undefined && <p className="tl-correlation-note">Pearson r = {edge.provenance.metadata.coefficient}; association does not establish causation.</p>}</aside>;
}
