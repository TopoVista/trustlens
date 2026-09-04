import React from 'react';
import { motion } from 'framer-motion';
import {
  Building2,
  FileCode2,
  Database,
  ShieldAlert,
  BarChart3,
  Sparkles,
  Award
} from 'lucide-react';

export default function WorkflowPipeline({ activeStage, isRunning, hasResult }) {
  const agents = [
    {
      id: 'ingestion',
      name: 'Ingestion Agent',
      category: 'Worker',
      tech: 'Vendor Tiering & Signals',
      metric: hasResult ? 'Ingested' : isRunning ? 'Active' : 'Standby',
      icon: Building2,
      color: 'from-blue-500 to-indigo-500'
    },
    {
      id: 'parsing',
      name: 'Parsing Agent',
      category: 'Worker',
      tech: 'Policy & Questionnaire',
      metric: hasResult ? 'Extracted' : isRunning ? 'Parsing' : 'Standby',
      icon: FileCode2,
      color: 'from-cyan-500 to-blue-500'
    },
    {
      id: 'retrieval',
      name: 'Retrieval Agent',
      category: 'Worker',
      tech: 'FAISS Dense Vectors',
      metric: hasResult ? 'Evidence Linked' : isRunning ? 'Searching' : 'Standby',
      icon: Database,
      color: 'from-teal-500 to-emerald-500'
    },
    {
      id: 'compliance',
      name: 'Compliance Agent',
      category: 'Worker',
      tech: 'SOC 2 / ISO / NIST',
      metric: hasResult ? 'Mapped' : isRunning ? 'Evaluating' : 'Standby',
      icon: ShieldAlert,
      color: 'from-purple-500 to-violet-500'
    },
    {
      id: 'scoring',
      name: 'Scoring Agent',
      category: 'Worker',
      tech: 'Quantitative Risk Engine',
      metric: hasResult ? 'Scored' : isRunning ? 'Calculating' : 'Standby',
      icon: BarChart3,
      color: 'from-pink-500 to-rose-500'
    },
    {
      id: 'report',
      name: 'Findings Agent',
      category: 'Worker',
      tech: 'OpenAI Assessment',
      metric: hasResult ? 'Generated' : isRunning ? 'Drafting' : 'Standby',
      icon: Sparkles,
      color: 'from-amber-500 to-orange-500'
    },
    {
      id: 'qa_verifier',
      name: 'QA Truth Guard',
      category: 'Service',
      tech: 'NLI Claim Verifier',
      metric: hasResult ? 'Certified' : isRunning ? 'Verifying' : 'Standby',
      icon: Award,
      color: 'from-emerald-500 to-green-500'
    }
  ];

  const getStageIndex = (stage) => {
    const order = ['idle', 'ingestion', 'parsing', 'retrieval', 'compliance', 'scoring', 'report', 'qa_verifier'];
    return order.indexOf(stage);
  };

  const currentIdx = getStageIndex(activeStage);

  return (
    <div className="w-full max-w-6xl mx-auto px-4 mt-8 mb-8">
      {/* Header telemetry */}
      <div className="flex items-center justify-between mb-3 text-xs">
        <div className="flex items-center space-x-2 text-trust-muted font-mono">
          <span className="w-2 h-2 rounded-full bg-trust-accent animate-ping" />
          <span className="uppercase tracking-wider font-semibold text-gray-300">
            Multi-Agent Autonomous Collaboration Canvas
          </span>
        </div>
        <span className="text-trust-muted text-[11px] font-mono">
          {isRunning ? 'Subagent Swarm Orchestration in Progress...' : hasResult ? 'All Agents Completed & Verified' : 'Awaiting Vendor Assessment Target'}
        </span>
      </div>

      {/* Pipeline nodes */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[760px] gap-2">
          {agents.map((agent, index) => {
            const Icon = agent.icon;
            const isNodeActive = isRunning && currentIdx >= index + 1;
            const isNodeCurrent = isRunning && currentIdx === index + 1;
            const isFinished = hasResult || (isRunning && currentIdx > index + 1);

            return (
              <React.Fragment key={agent.id}>
                <motion.div
                  className={`relative flex-1 rounded-xl p-3 border transition-all duration-300 ${
                    isNodeCurrent
                      ? 'bg-trust-surface/90 border-trust-accent shadow-lg shadow-trust-accent/30 ring-1 ring-trust-accent scale-105'
                      : isFinished
                      ? 'bg-trust-surface/70 border-trust-border text-gray-200'
                      : 'bg-trust-surface/30 border-trust-border/40 text-gray-500 opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                        isNodeCurrent
                          ? `bg-gradient-to-tr ${agent.color} text-white`
                          : isFinished
                          ? 'bg-trust-card text-trust-cyan'
                          : 'bg-trust-card text-gray-500'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-trust-card text-trust-muted border border-trust-border/50">
                      {agent.category}
                    </span>
                  </div>

                  <div className="font-semibold text-xs tracking-tight truncate text-gray-200">
                    {agent.name}
                  </div>
                  <div className="text-[10px] text-trust-muted truncate font-mono">
                    {agent.tech}
                  </div>

                  <div className="mt-2 pt-2 border-t border-trust-border/40 flex items-center justify-between text-[10px] font-mono">
                    <span className={isNodeCurrent ? 'text-trust-accent font-semibold animate-pulse' : 'text-gray-400'}>
                      {agent.metric}
                    </span>
                    {isFinished && <span className="text-emerald-400 text-xs font-bold">✓</span>}
                  </div>
                </motion.div>

                {index < agents.length - 1 && (
                  <div className="flex items-center px-1">
                    <div className="w-3 h-0.5 bg-trust-border relative overflow-hidden">
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
