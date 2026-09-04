import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ShieldCheck, Cpu, Layers, Sparkles, Scissors, CheckCheck, FileText } from 'lucide-react';

export default function ArchitectureModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const steps = [
    {
      num: '01',
      title: 'Semantic Vector Retrieval',
      tech: 'all-MiniLM-L6-v2 + FAISS IndexFlatIP',
      desc: 'Retrieves top-k evidence documents from a 450-document database systems corpus using normalized inner-product cosine similarity.',
      icon: Layers,
      color: 'text-trust-cyan'
    },
    {
      num: '02',
      title: 'Grounded LLM Generation',
      tech: 'OpenAI API (gpt-5.6-luna / configurable)',
      desc: 'Prompts OpenAI with strictly bounded instructions forbidding hallucinations or external knowledge beyond the retrieved context.',
      icon: Sparkles,
      color: 'text-trust-accent'
    },
    {
      num: '03',
      title: 'Claim Decomposition',
      tech: 'spaCy NLP Sentence Segmentation',
      desc: 'Breaks down the generated answer into isolated, testable atomic claims while conservatively preserving modal hedges.',
      icon: Scissors,
      color: 'text-pink-400'
    },
    {
      num: '04',
      title: 'Independent Claim Retrieval',
      tech: 'FAISS Top-3 Claim Search',
      desc: 'Independently retrieves evidence for each individual claim rather than relying solely on the original prompt context.',
      icon: Cpu,
      color: 'text-amber-400'
    },
    {
      num: '05',
      title: 'Natural Language Inference (NLI)',
      tech: 'cross-encoder/nli-MiniLM2-L6-H768',
      desc: 'Evaluates (premise, hypothesis) pairs to strictly classify each claim as SUPPORTED (entailment), CONTRADICTED, or NOT_SUPPORTED.',
      icon: CheckCheck,
      color: 'text-trust-green'
    },
    {
      num: '06',
      title: 'Faithfulness Scoring & Observability',
      tech: 'Confidence-Weighted Grounding Metrics',
      desc: 'Calculates overall answer faithfulness, flags unsupported hallucinations, and renders claim-level visual grounding.',
      icon: ShieldCheck,
      color: 'text-emerald-400'
    }
  ];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.2 }}
          className="glass-panel w-full max-w-3xl rounded-2xl p-6 sm:p-8 border border-trust-border shadow-2xl relative max-h-[90vh] overflow-y-auto"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-lg bg-trust-surface hover:bg-trust-border text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Modal header */}
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-trust-accent/20 border border-trust-accent/30 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-trust-accent" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">How TrustLens Works</h2>
          </div>
          <p className="text-xs text-trust-muted mb-6">
            The core principle: <strong className="text-gray-200">Generation is not verification.</strong> TrustLens decouples answer synthesis from independent claim grounding.
          </p>

          {/* Steps list */}
          <div className="space-y-4">
            {steps.map((s, idx) => {
              const Icon = s.icon;
              return (
                <div
                  key={idx}
                  className="flex items-start space-x-4 p-3.5 rounded-xl bg-trust-surface/60 border border-trust-border/60 hover:border-trust-border transition-colors"
                >
                  <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-trust-card border border-trust-border font-mono text-xs font-bold text-gray-400 shrink-0">
                    {s.num}
                  </div>

                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-white flex items-center space-x-2">
                        <Icon className={`w-4 h-4 ${s.color}`} />
                        <span>{s.title}</span>
                      </h4>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-trust-card text-trust-muted border border-trust-border/50">
                        {s.tech}
                      </span>
                    </div>
                    <p className="text-xs text-gray-300 leading-relaxed">
                      {s.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Semantic distinction note */}
          <div className="mt-6 p-4 rounded-xl bg-trust-amber-bg border border-trust-amber/30 text-xs text-trust-amber/90 leading-relaxed">
            <strong className="text-trust-amber font-semibold block mb-1">Important Semantic Note:</strong>
            A label of <code className="px-1 py-0.5 rounded bg-trust-amber/20 font-mono text-white">NOT_SUPPORTED</code> does not imply the model made a false statement; rather, it guarantees that the retrieved corpus evidence was insufficient to formally entail the claim.
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
