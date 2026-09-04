import React, { useState } from 'react';
import { motion } from 'framer-motion';
import ScoreCard from './ScoreCard.jsx';
import ViewToggle from './ViewToggle.jsx';
import ClaimCard from './ClaimCard.jsx';
import TelemetryBar from './TelemetryBar.jsx';
import { FileText, Sparkles, AlertTriangle } from 'lucide-react';

export default function ResultsPanel({ data }) {
  const [mode, setMode] = useState('verified');

  if (!data) return null;

  const { answer, verified_claims, stats } = data;

  return (
    <div className="max-w-4xl mx-auto px-4 mt-8 space-y-6">
      {/* 1. Overall Faithfulness Score & Breakdown */}
      <ScoreCard stats={stats} />

      {/* 2. Baseline vs. Verified Section */}
      <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-trust-border shadow-2xl">
        <ViewToggle mode={mode} setMode={setMode} />

        {/* Baseline View */}
        {mode === 'baseline' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            <div className="p-3 rounded-xl bg-trust-surface border border-trust-border text-xs text-trust-muted flex items-start space-x-2">
              <FileText className="w-4 h-4 text-trust-accent mt-0.5 shrink-0" />
              <span>
                Below is the raw generated output from the OpenAI model before TrustLens decomposed and verified individual claims against retrieved evidence.
              </span>
            </div>

            <div className="p-5 rounded-xl bg-trust-card/80 border border-trust-border/80 text-sm sm:text-base text-gray-200 leading-relaxed font-sans whitespace-pre-line">
              {answer}
            </div>
          </motion.div>
        )}

        {/* Verified View */}
        {mode === 'verified' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between text-xs text-trust-muted mb-2 font-mono">
              <span>Claims Decomposed: {verified_claims?.length || 0}</span>
              <span>Click any claim to inspect its grounding evidence</span>
            </div>

            {verified_claims && verified_claims.length > 0 ? (
              verified_claims.map((claim, idx) => (
                <ClaimCard key={idx} claim={claim} index={idx} />
              ))
            ) : (
              <div className="p-8 text-center text-trust-muted text-sm rounded-xl bg-trust-surface border border-trust-border">
                No verifiable claims could be decomposed from this response.
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* 3. Execution Timings & Telemetry */}
      <TelemetryBar stats={stats} />
    </div>
  );
}
