import React, { useState } from 'react';
import { 
  Search, 
  Sparkles, 
  ArrowRight, 
  HelpCircle, 
  GitCompare, 
  Clock, 
  ShieldAlert,
  Terminal
} from 'lucide-react';

const SUGGESTIONS = [
  {
    icon: Search,
    label: 'Factual Grounding',
    query: 'What was our Q3 revenue and who leads engineering?'
  },
  {
    icon: GitCompare,
    label: 'Contradiction & Evolution',
    query: 'Are there any conflicting dates or budget numbers across documents?'
  },
  {
    icon: Clock,
    label: 'Timeline Reconstruction',
    query: 'What is the chronological timeline of all key events and milestones?'
  },
  {
    icon: ShieldAlert,
    label: 'Blind Spot Audit',
    query: 'Audit our workspace blind spots and unsupported assertions.'
  }
];

export default function QueryConsole({
  onRunQuery,
  isLoading = false,
  activeWorkspace
}) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim() || isLoading) return;
    onRunQuery(query.trim());
  };

  const handleSuggestionClick = (suggestedQuery) => {
    setQuery(suggestedQuery);
    onRunQuery(suggestedQuery);
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 my-6">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center rounded-2xl bg-trust-surface/90 border border-trust-border shadow-2xl focus-within:border-trust-accent focus-within:ring-2 focus-within:ring-trust-accent/20 transition-all">
          <div className="pl-4 pr-2 text-trust-muted">
            <Search className="w-5 h-5 text-trust-cyan" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Ask anything grounded in "${activeWorkspace?.name || 'your workspace'}"...`}
            disabled={isLoading}
            className="w-full py-4 pr-32 bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none font-sans"
          />
          <div className="absolute right-2.5 flex items-center gap-2">
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-trust-accent to-purple-600 hover:from-trust-accent-hover hover:to-purple-500 text-xs font-semibold text-white shadow-md shadow-trust-accent/25 transition-all disabled:opacity-50 active:scale-95"
            >
              {isLoading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span className="hidden sm:inline">Reasoning...</span>
                </>
              ) : (
                <>
                  <span>Query</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Suggested Inquiries */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-mono text-trust-muted uppercase tracking-wider mr-1">
          Explore:
        </span>
        {SUGGESTIONS.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              onClick={() => handleSuggestionClick(item.query)}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-trust-card/80 border border-trust-border/70 hover:border-trust-accent/60 hover:bg-trust-card text-gray-300 hover:text-white text-[11px] transition-all disabled:opacity-50"
            >
              <Icon className="w-3 h-3 text-trust-accent" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
