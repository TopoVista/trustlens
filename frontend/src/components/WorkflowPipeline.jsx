import React from 'react';
import { motion } from 'framer-motion';
import {
  Search,
  Cpu,
  Layers,
  Sparkles,
  Scissors,
  CheckCheck,
  ShieldCheck
} from 'lucide-react';

export default function WorkflowPipeline({ activeStage, stats, isRunning, hasResult }) {
  const nodes = [
    {
      id: 'query',
      name: 'Query',
      badge: 'Input',
      tech: 'User Prompt',
      metric: isRunning || hasResult ? '1 query' : 'Idle',
      icon: Search,
      color: 'from-blue-500 to-indigo-500'
    },
    {
      id: 'embed',
      name: 'Embedding',
      badge: 'MiniLM-L6',
      tech: 'SentenceTransformer',
      metric: hasResult ? '384 dims' : isRunning ? 'Encoding' : 'Standby',
      icon: Cpu,
      color: 'from-cyan-500 to-blue-500'
    },
    {
      id: 'retrieve',
      name: 'FAISS Retrieval',
      badge: 'IndexFlatIP',
      tech: 'Vector Similarity',
      metric: hasResult ? `${stats?.documents_retrieved || 5} docs` : isRunning ? 'Searching' : 'Standby',
      icon: Layers,
      color: 'from-teal-500 to-emerald-500'
    },
    {
      id: 'generate',
      name: 'OpenAI LLM',
      badge: 'Grounded API',
      tech: 'Strict Evidence Context',
      metric: hasResult ? `${stats?.generation_ms || '1.2'}s` : isRunning ? 'Generating' : 'Standby',
      icon: Sparkles,
      color: 'from-purple-500 to-violet-500'
    },
    {
      id: 'claims',
      name: 'Claim Splitting',
      badge: 'spaCy NLP',
      tech: 'Sentence Segmentation',
      metric: hasResult ? `${stats?.claim_count || 4} claims` : isRunning ? 'Extracting' : 'Standby',
      icon: Scissors,
      color: 'from-pink-500 to-rose-500'
    },
    {
      id: 'nli',
      name: 'NLI Inference',
      badge: 'MiniLM2-L6',
      tech: 'Premise-Hypothesis NLI',
      metric: hasResult ? `${(stats?.claim_count || 4) * 3} pairs` : isRunning ? 'Classifying' : 'Standby',
      icon: CheckCheck,
      color: 'from-amber-500 to-orange-500'
    },
    {
      id: 'result',
      name: 'Trust Report',
      badge: 'Faithfulness',
      tech: 'Multi-Evidence Verdicts',
      metric: hasResult ? `${Math.round((stats?.faithfulness || 0) * 100)}% grounded` : isRunning ? 'Compiling' : 'Ready',
      icon: ShieldCheck,
      color: 'from-emerald-500 to-green-500'
    }
  ];

  const getStageIndex = (stage) => {
    const order = ['idle', 'query', 'embed', 'retrieve', 'generate', 'claims', 'nli', 'result'];
    return order.indexOf(stage);
  };

  const currentIdx = getStageIndex(activeStage);

  return (
    <div className="w-full max-w-6xl mx-auto px-4 mt-8">
      {/* Header telemetry text */}
      <div className="flex items-center justify-between mb-3 text-xs">
        <div className="flex items-center space-x-2 text-trust-muted font-mono">
          <span className="w-2 h-2 rounded-full bg-trust-accent animate-ping" />
          <span className="uppercase tracking-wider font-semibold text-gray-300">
            TrustLens Dual-Stage Pipeline
          </span>
        </div>
        <span className="text-trust-muted text-[11px] font-mono">
          {isRunning ? 'Pipeline Execution in Progress...' : hasResult ? 'Verification Complete' : 'Awaiting Input'}
        </span>
      </div>

      {/* Responsive pipeline container */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[760px] gap-2">
          {nodes.map((node, index) => {
            const Icon = node.icon;
            const isNodeActive = isRunning && currentIdx >= index + 1;
            const isNodeCurrent = isRunning && currentIdx === index + 1;
            const isFinished = hasResult || (isRunning && currentIdx > index + 1);

            return (
              <React.Fragment key={node.id}>
                {/* Workflow Node */}
                <motion.div
                  className={`relative flex-1 rounded-xl p-3 border transition-all duration-300 ${
                    isNodeCurrent
                      ? 'bg-trust-surface/90 border-trust-accent shadow-lg shadow-trust-accent/30 ring-1 ring-trust-accent scale-105'
                      : isFinished
                      ? 'bg-trust-surface/70 border-trust-border text-gray-200'
                      : 'bg-trust-surface/30 border-trust-border/40 text-gray-500 opacity-60'
                  }`}
                >
                  {/* Top row: icon + tech badge */}
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                        isNodeCurrent
                          ? `bg-gradient-to-tr ${node.color} text-white`
                          : isFinished
                          ? 'bg-trust-card text-trust-cyan'
                          : 'bg-trust-card text-gray-500'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-trust-card text-trust-muted border border-trust-border/50">
                      {node.badge}
                    </span>
                  </div>

                  {/* Title & subtitle */}
                  <div className="font-semibold text-xs tracking-tight truncate text-gray-200">
                    {node.name}
                  </div>
                  <div className="text-[10px] text-trust-muted truncate font-mono">
                    {node.tech}
                  </div>

                  {/* Metric status bottom pill */}
                  <div className="mt-2 pt-2 border-t border-trust-border/40 flex items-center justify-between text-[10px] font-mono">
                    <span className={isNodeCurrent ? 'text-trust-accent font-semibold animate-pulse' : 'text-gray-400'}>
                      {node.metric}
                    </span>
                    {isFinished && <span className="text-trust-green text-xs">✓</span>}
                  </div>
                </motion.div>

                {/* Animated connector arrow */}
                {index < nodes.length - 1 && (
                  <div className="flex items-center px-1">
                    <div className="w-4 h-0.5 bg-trust-border relative overflow-hidden">
                      {isRunning && currentIdx >= index + 1 && (
                        <motion.div
                          className="absolute inset-0 bg-trust-accent"
                          initial={{ x: '-100%' }}
                          animate={{ x: '100%' }}
                          transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                        />
                      )}
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
