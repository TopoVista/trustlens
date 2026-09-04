import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, HelpCircle, XCircle, ShieldCheck, AlertCircle } from 'lucide-react';

export default function ScoreCard({ stats }) {
  const faithfulness = stats?.faithfulness !== undefined ? Math.round(stats.faithfulness * 100) : 0;
  const hallucinationRate = stats?.hallucination_rate !== undefined ? Math.round(stats.hallucination_rate * 100) : 0;

  // Determine badge color based on faithfulness score
  let scoreColor = 'text-trust-green';
  let ringColor = '#10B981';
  let statusText = 'Strongly Grounded';
  if (faithfulness < 70 && faithfulness >= 40) {
    scoreColor = 'text-trust-amber';
    ringColor = '#F59E0B';
    statusText = 'Partially Supported';
  } else if (faithfulness < 40) {
    scoreColor = 'text-trust-red';
    ringColor = '#EF4444';
    statusText = 'Low Grounding';
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Primary Faithfulness Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="glass-panel rounded-2xl p-5 md:col-span-1 flex flex-col justify-between relative overflow-hidden"
      >
        <div className="flex items-center justify-between text-xs text-trust-muted font-mono uppercase tracking-wider">
          <span>Faithfulness Score</span>
          <ShieldCheck className="w-4 h-4 text-trust-accent" />
        </div>

        <div className="my-4 flex items-baseline space-x-3">
          <span className={`text-5xl font-black tracking-tight ${scoreColor}`}>
            {faithfulness}%
          </span>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-white">{statusText}</span>
            <span className="text-[11px] text-trust-muted">
              {100 - faithfulness}% ungrounded
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-trust-surface h-2 rounded-full overflow-hidden border border-trust-border/50">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${faithfulness}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="h-full rounded-full"
            style={{ backgroundColor: ringColor }}
          />
        </div>

        <p className="mt-3 text-[11px] text-trust-muted leading-tight">
          Confidence-weighted entailment calculated against independent FAISS evidence.
        </p>
      </motion.div>

      {/* Breakdown Metrics Grid */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="glass-panel rounded-2xl p-5 md:col-span-2 flex flex-col justify-between"
      >
        <div className="flex items-center justify-between text-xs text-trust-muted font-mono uppercase tracking-wider mb-3">
          <span>Claim Verification Breakdown</span>
          <span className="text-gray-400">Total: {stats?.claim_count || 0} claims</span>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {/* Supported Pill */}
          <div className="rounded-xl p-3.5 bg-trust-green-bg border border-trust-green/20">
            <div className="flex items-center space-x-1.5 text-trust-green text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>SUPPORTED</span>
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {stats?.supported || 0}
            </div>
            <div className="text-[10px] text-trust-green/80 mt-0.5">
              Strictly entailed by corpus
            </div>
          </div>

          {/* Not Supported Pill */}
          <div className="rounded-xl p-3.5 bg-trust-amber-bg border border-trust-amber/20 relative group">
            <div className="flex items-center space-x-1.5 text-trust-amber text-xs font-semibold">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>UNSUPPORTED</span>
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {stats?.not_supported || 0}
            </div>
            <div className="text-[10px] text-trust-amber/80 mt-0.5 flex items-center gap-1">
              <span>Insufficient evidence</span>
              <AlertCircle className="w-3 h-3 cursor-help" />
            </div>

            {/* Crucial distinction tooltip */}
            <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 rounded-lg bg-trust-card border border-trust-border text-[10px] text-gray-200 z-30 shadow-xl pointer-events-none">
              Does not mean false; indicates retrieved evidence was insufficient to verify.
            </div>
          </div>

          {/* Contradicted Pill */}
          <div className="rounded-xl p-3.5 bg-trust-red-bg border border-trust-red/20">
            <div className="flex items-center space-x-1.5 text-trust-red text-xs font-semibold">
              <XCircle className="w-3.5 h-3.5" />
              <span>CONTRADICTED</span>
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {stats?.contradicted || 0}
            </div>
            <div className="text-[10px] text-trust-red/80 mt-0.5">
              Directly refuted by corpus
            </div>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-trust-border/50 flex items-center justify-between text-xs text-trust-muted font-mono">
          <span>Hallucination Rate: <strong className="text-gray-200">{hallucinationRate}%</strong></span>
          <span>Decision threshold: <strong className="text-gray-200">0.70</strong></span>
        </div>
      </motion.div>
    </div>
  );
}
