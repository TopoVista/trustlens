import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, ShieldCheck, Sparkles, Layers } from 'lucide-react';

export default function Hero() {
  return (
    <div className="relative pt-8 pb-4 text-center max-w-4xl mx-auto px-4">
      {/* Subtle background gradient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-48 bg-trust-accent/10 rounded-full blur-3xl pointer-events-none -z-10" />

      {/* Pill badge */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-trust-surface border border-trust-border text-xs text-trust-muted mb-4 shadow-sm"
      >
        <Sparkles className="w-3.5 h-3.5 text-trust-accent" />
        <span className="font-medium text-gray-300">Generation is not verification.</span>
      </motion.div>

      {/* Main heading */}
      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white"
      >
        AI answers shouldn't be{' '}
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-trust-accent via-indigo-400 to-trust-cyan">
          trusted blindly.
        </span>
      </motion.h1>

      {/* Subheading */}
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="mt-3 text-sm sm:text-base text-gray-400 max-w-2xl mx-auto leading-relaxed"
      >
        RAG retrieves evidence for generation; <span className="text-white font-medium">TrustLens</span> independently decomposes the answer into claims and verifies what the model actually asserted.
      </motion.p>

      {/* Tri-step pill badges */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="flex items-center justify-center space-x-3 sm:space-x-6 mt-5 text-xs text-gray-400 font-mono"
      >
        <span className="flex items-center space-x-1.5 bg-trust-card/80 px-2.5 py-1 rounded-md border border-trust-border">
          <span className="w-1.5 h-1.5 rounded-full bg-trust-cyan"></span>
          <span>1. Retrieve</span>
        </span>
        <span className="text-trust-border">→</span>
        <span className="flex items-center space-x-1.5 bg-trust-card/80 px-2.5 py-1 rounded-md border border-trust-border">
          <span className="w-1.5 h-1.5 rounded-full bg-trust-accent"></span>
          <span>2. Generate</span>
        </span>
        <span className="text-trust-border">→</span>
        <span className="flex items-center space-x-1.5 bg-trust-card/80 px-2.5 py-1 rounded-md border border-trust-border">
          <span className="w-1.5 h-1.5 rounded-full bg-trust-green"></span>
          <span>3. Verify</span>
        </span>
      </motion.div>
    </div>
  );
}
