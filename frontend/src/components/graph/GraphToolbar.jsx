import React, { useMemo, useState } from 'react';
import { Filter, Search, SlidersHorizontal } from 'lucide-react';

const NODE_TYPES = ['CLAIM', 'ENTITY', 'VARIABLE', 'VALUE', 'EVENT', 'DOCUMENT', 'EVIDENCE', 'DATASET'];
const RELATIONS = ['SUPPORTED_BY', 'CONTRADICTS', 'DEPENDS_ON', 'MENTIONS', 'PRECEDES', 'CORRELATED_WITH', 'HAS_VALUE'];

export default function GraphToolbar({ graph, filters, onChange, onPickNode }) {
  const [search, setSearch] = useState('');
  const matches = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return [];
    return graph.nodes.filter((node) => `${node.label} ${(node.metadata?.aliases || []).join(' ')}`.toLowerCase().includes(term)).slice(0, 6);
  }, [graph.nodes, search]);
  const toggle = (key, value) => onChange({ ...filters, [key]: filters[key].includes(value) ? filters[key].filter((item) => item !== value) : [...filters[key], value] });
  return <div className="tl-graph-toolbar"><div className="tl-graph-search"><Search className="h-4 w-4" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search claims, entities, variables, documents…" aria-label="Search graph" />{matches.length > 0 && <div className="tl-graph-search-results">{matches.map((node) => <button key={node.id} onClick={() => { onPickNode(node.id); setSearch(''); }}><span>{node.type}</span>{node.label}</button>)}</div>}</div><div className="tl-graph-control"><Filter className="h-3.5 w-3.5" /><span>Nodes</span>{NODE_TYPES.map((type) => <label key={type}><input type="checkbox" checked={filters.types.includes(type)} onChange={() => toggle('types', type)} />{type.toLowerCase()}</label>)}</div><div className="tl-graph-control"><SlidersHorizontal className="h-3.5 w-3.5" /><span>Relations</span>{RELATIONS.map((relation) => <label key={relation}><input type="checkbox" checked={filters.relations.includes(relation)} onChange={() => toggle('relations', relation)} />{relation.toLowerCase().replace('_', ' ')}</label>)}</div><label className="tl-graph-range">Evidence confidence ≥ {Math.round(filters.minConfidence * 100)}<input type="range" min="0" max="100" value={Math.round(filters.minConfidence * 100)} onChange={(event) => onChange({ ...filters, minConfidence: Number(event.target.value) / 100 })} /></label></div>;
}
