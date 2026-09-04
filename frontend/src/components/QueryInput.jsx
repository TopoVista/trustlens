import React from 'react';
import { Sparkles, ArrowRight, CornerDownLeft, Database } from 'lucide-react';

const EXAMPLE_QUERIES = [
  "What is MVCC and how does it prevent concurrency conflicts?",
  "Why do B-tree indexes improve query performance?",
  "What is the difference between database sharding and replication?",
  "What does ACID guarantee in relational transactions?"
];

export default function QueryInput({ query, setQuery, onAnalyze, isLoading }) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (query.trim() && !isLoading) {
        onAnalyze();
      }
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 mt-6">
      {/* Search card */}
      <div className="relative rounded-2xl glass-panel p-2 shadow-2xl shadow-black/60 focus-within:border-trust-accent/60 transition-colors">
        <div className="relative flex flex-col">
          <textarea
            id="query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask TrustLens anything about the database systems corpus..."
            rows={3}
            className="w-full bg-transparent px-4 py-3 text-sm sm:text-base text-gray-100 placeholder-gray-500 focus:outline-none resize-none"
          />

          {/* Bottom toolbar inside input card */}
          <div className="flex items-center justify-between px-3 py-2 border-t border-trust-border/50 bg-trust-surface/40 rounded-b-xl mt-1">
            <div className="flex items-center space-x-2 text-[11px] text-trust-muted font-mono">
              <Database className="w-3.5 h-3.5 text-trust-cyan" />
              <span>450 technical database documents indexed</span>
            </div>

            <button
              id="analyze-button"
              onClick={onAnalyze}
              disabled={isLoading || !query.trim()}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-trust-accent to-trust-cyan text-white text-xs sm:text-sm font-medium hover:opacity-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-trust-accent/20"
            >
              <span>{isLoading ? 'Verifying...' : 'Verify Grounding'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Suggested corpus query chips */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-xs text-trust-muted flex items-center gap-1 font-mono">
          <Sparkles className="w-3 h-3 text-trust-accent" />
          <span>Try:</span>
        </span>
        {EXAMPLE_QUERIES.map((example, i) => (
          <button
            key={i}
            onClick={() => setQuery(example)}
            disabled={isLoading}
            className="text-xs px-2.5 py-1 rounded-lg bg-trust-card/70 hover:bg-trust-border/80 border border-trust-border/80 text-gray-300 hover:text-white transition-all text-left truncate max-w-xs"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}
