import React from 'react';
import { Route, X } from 'lucide-react';

export default function ReasoningPathPanel({ path, onClose }) {
  if (!path) return null;

  return (
    <section className="tl-path-panel">
      <button className="tl-drawer-close" onClick={onClose} aria-label="Close reasoning path"><X className="h-4 w-4" /></button>
      <p className="editorial-kicker tl-status"><Route className="mr-1 inline h-3 w-3" />Reasoning path</p>
      <h4>{path.explanation}</h4>
      {path.hops?.length ? <>
        <p className="tl-path-quality">Route quality: {Math.round((path.path_confidence || 0) * 100)}% · strongest available evidence route</p>
        <ol>{path.hops.map((hop) => <li key={hop.id}>
          <strong>{hop.relation.replaceAll('_', ' ')}</strong>
          <span>{Math.round(hop.confidence * 100)}% · {hop.provenance?.method || 'HEURISTIC'}</span>
          <p>{hop.explanation}</p>
        </li>)}</ol>
      </> : <p>No path is shown because the current graph does not have an evidence-backed connection between those nodes.</p>}
    </section>
  );
}
