import React from 'react';
import { FileText, CheckCircle } from 'lucide-react';

export default function ViewToggle({ mode, setMode }) {
  return (
    <div className="flex items-center justify-between border-b border-trust-border pb-4 mb-4">
      <div className="flex items-center space-x-2">
        <h2 className="text-lg font-bold text-white">Answer Analysis</h2>
        <span className="text-xs text-trust-muted hidden sm:inline font-mono">
          {mode === 'verified' ? 'Deconstructed & Verified' : 'Unfiltered LLM Generation'}
        </span>
      </div>

      {/* Segmented button toggle */}
      <div className="p-1 rounded-xl bg-trust-surface border border-trust-border flex items-center space-x-1">
        <button
          onClick={() => setMode('baseline')}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            mode === 'baseline'
              ? 'bg-trust-card text-white shadow-md border border-trust-border'
              : 'text-trust-muted hover:text-gray-200'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Baseline (Raw LLM)</span>
        </button>

        <button
          onClick={() => setMode('verified')}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            mode === 'verified'
              ? 'bg-gradient-to-r from-trust-accent to-trust-cyan text-white shadow-md'
              : 'text-trust-muted hover:text-gray-200'
          }`}
        >
          <CheckCircle className="w-3.5 h-3.5" />
          <span>Verified Grounding</span>
        </button>
      </div>
    </div>
  );
}
