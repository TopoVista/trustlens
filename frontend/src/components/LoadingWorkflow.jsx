import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Server, CheckCircle2 } from 'lucide-react';

const STEPS = [
  { label: 'Embedding user query with MiniLM...', duration: 600 },
  { label: 'Retrieving top-k evidence from FAISS vector index...', duration: 900 },
  { label: 'Prompting OpenAI with grounded context...', duration: 1800 },
  { label: 'Decomposing generated answer into claims via spaCy...', duration: 800 },
  { label: 'Retrieving independent evidence for each claim...', duration: 900 },
  { label: 'Running cross-encoder NLI inference & building trust report...', duration: 1500 },
];

export default function LoadingWorkflow({ isColdStarting }) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 1200);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 mt-10">
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-trust-border shadow-2xl relative overflow-hidden">
        {/* Subtle accent gradient bar on top */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-trust-accent via-trust-cyan to-trust-green animate-pulse" />

        {/* Cold-start notification */}
        {isColdStarting && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-3.5 rounded-xl bg-trust-surface/80 border border-trust-accent/40 flex items-start space-x-3"
          >
            <Server className="w-4 h-4 text-trust-cyan mt-0.5 animate-pulse" />
            <div className="text-xs">
              <span className="font-semibold text-white">Connecting to TrustLens...</span>
              <p className="text-gray-400 mt-0.5">
                The verification engine and embedding models may take a moment to initialize on first launch.
              </p>
            </div>
          </motion.div>
        )}

        <div className="flex items-center space-x-3 mb-6">
          <Loader2 className="w-5 h-5 text-trust-accent animate-spin" />
          <h3 className="font-semibold text-white text-base">Evaluating Response Grounding</h3>
        </div>

        {/* Staged pipeline checkpoints */}
        <div className="space-y-3">
          {STEPS.map((step, idx) => {
            const isDone = idx < currentStep;
            const isCurrent = idx === currentStep;

            return (
              <div
                key={idx}
                className={`flex items-center space-x-3 text-xs sm:text-sm transition-opacity duration-300 ${
                  isDone
                    ? 'text-gray-300'
                    : isCurrent
                    ? 'text-white font-medium'
                    : 'text-gray-600 opacity-50'
                }`}
              >
                <div className="w-4 h-4 flex items-center justify-center">
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-trust-green" />
                  ) : isCurrent ? (
                    <span className="w-2 h-2 rounded-full bg-trust-accent animate-ping" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-600" />
                  )}
                </div>
                <span>{step.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
