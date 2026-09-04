import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, HelpCircle, XCircle, ChevronDown, ChevronUp, Layers } from 'lucide-react';
import EvidenceCard from './EvidenceCard.jsx';

export default function ClaimCard({ claim, index }) {
  const [isOpen, setIsOpen] = useState(false);

  const labelConfig = {
    SUPPORTED: {
      color: 'text-trust-green',
      bg: 'bg-trust-green-bg',
      border: 'border-trust-green/30',
      icon: CheckCircle2,
      badgeText: 'SUPPORTED',
      desc: 'Affirmed by retrieved evidence'
    },
    NOT_SUPPORTED: {
      color: 'text-trust-amber',
      bg: 'bg-trust-amber-bg',
      border: 'border-trust-amber/30',
      icon: HelpCircle,
      badgeText: 'NOT SUPPORTED',
      desc: 'Insufficient evidence to substantiate'
    },
    CONTRADICTED: {
      color: 'text-trust-red',
      bg: 'bg-trust-red-bg',
      border: 'border-trust-red/30',
      icon: XCircle,
      badgeText: 'CONTRADICTED',
      desc: 'Refuted by retrieved evidence'
    }
  };

  const config = labelConfig[claim.label] || labelConfig.NOT_SUPPORTED;
  const Icon = config.icon;
  const confidence = Math.round((claim.score || 0) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`rounded-2xl border transition-all ${config.border} ${isOpen ? 'bg-trust-card/90 shadow-xl' : 'bg-trust-card/50 hover:bg-trust-card/80'}`}
    >
      {/* Top Clickable Bar */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="p-4 sm:p-5 flex items-start justify-between cursor-pointer select-none gap-4"
      >
        <div className="flex items-start space-x-3.5 flex-1">
          <div className={`mt-0.5 p-1 rounded-lg ${config.bg} ${config.color} shrink-0`}>
            <Icon className="w-4 h-4" />
          </div>

          <div className="space-y-1 flex-1">
            <p className="text-sm sm:text-base font-normal text-gray-100 leading-snug">
              {claim.claim}
            </p>
            <div className="flex items-center space-x-2 text-[11px] text-trust-muted font-mono">
              <span className={`font-semibold ${config.color}`}>{config.badgeText}</span>
              <span>•</span>
              <span>Confidence: {confidence}%</span>
              <span>•</span>
              <span className="hidden sm:inline text-gray-400">{claim.evidence?.length || 0} evidence docs</span>
            </div>
          </div>
        </div>

        {/* Expand button */}
        <div className="flex items-center space-x-2 shrink-0 pt-1">
          <span className="text-[11px] font-mono text-trust-muted hidden sm:inline">
            {isOpen ? 'Hide Evidence' : 'Inspect Evidence'}
          </span>
          <div className="p-1 rounded-md bg-trust-surface border border-trust-border text-gray-400">
            {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </div>
        </div>
      </div>

      {/* Expandable Evidence Drawer */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden border-t border-trust-border/60 bg-trust-bg/50 px-4 sm:px-6 py-4 rounded-b-2xl"
          >
            <div className="flex items-center justify-between mb-3 text-xs">
              <div className="flex items-center space-x-1.5 text-gray-300 font-medium">
                <Layers className="w-3.5 h-3.5 text-trust-cyan" />
                <span>Retrieved Evidence for this Claim</span>
              </div>
              <span className="text-[11px] font-mono text-trust-muted">
                {config.desc}
              </span>
            </div>

            {claim.evidence && claim.evidence.length > 0 ? (
              <div className="space-y-2.5">
                {claim.evidence.map((doc, docIdx) => (
                  <EvidenceCard key={docIdx} doc={doc} />
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-trust-surface/60 border border-trust-border/50 text-xs text-trust-muted text-center">
                No matching evidence documents retrieved above the relevance threshold.
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
