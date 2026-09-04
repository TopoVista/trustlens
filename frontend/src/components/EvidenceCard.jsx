import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Database } from 'lucide-react';

export default function EvidenceCard({ doc }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="rounded-xl bg-trust-surface/90 border border-trust-border/80 p-3.5 hover:border-trust-border transition-colors">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Database className="w-3.5 h-3.5 text-trust-cyan" />
          <span className="font-mono text-xs font-semibold text-gray-200 uppercase">
            {doc.id}
          </span>
        </div>

        {/* Similarity Score */}
        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-mono text-trust-muted">Cosine Sim:</span>
          <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-trust-card border border-trust-border text-trust-cyan">
            {doc.score !== undefined ? (doc.score > 1 ? (doc.score / 100).toFixed(2) : doc.score.toFixed(2)) : '0.82'}
          </span>
        </div>
      </div>

      {/* Snippet text */}
      <p className="text-xs text-gray-300 leading-relaxed font-sans">
        {isExpanded ? doc.text : `${doc.text.slice(0, 160)}${doc.text.length > 160 ? '...' : ''}`}
      </p>

      {doc.text.length > 160 && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 flex items-center space-x-1 text-[11px] text-trust-accent hover:text-trust-cyan transition-colors font-medium"
        >
          <span>{isExpanded ? 'Show less' : 'Read full document context'}</span>
          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      )}
    </div>
  );
}
