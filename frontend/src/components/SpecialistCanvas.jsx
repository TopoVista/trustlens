import React from 'react';
import { 
  Network, 
  Search, 
  FileCheck2, 
  GitCompare, 
  GitBranch, 
  CalendarClock, 
  ShieldAlert, 
  Cpu, 
  Compass,
  CheckCircle2,
  Activity
} from 'lucide-react';

const SPECIALISTS = [
  {
    id: 'planner',
    name: 'Analysis Planner',
    role: 'Intent Classification & Plan Construction',
    icon: Compass,
    color: 'from-blue-500 to-indigo-600',
    borderColor: 'border-blue-500/50',
    glowColor: 'shadow-blue-500/20'
  },
  {
    id: 'claim_detective',
    name: 'Claim Detective',
    role: 'Atomic Assertion Decomposition',
    icon: FileCheck2,
    color: 'from-purple-500 to-violet-600',
    borderColor: 'border-purple-500/50',
    glowColor: 'shadow-purple-500/20'
  },
  {
    id: 'evidence_agent',
    name: 'Evidence Grounding',
    role: 'Hybrid Retrieval & NLI Verification',
    icon: Search,
    color: 'from-cyan-500 to-teal-600',
    borderColor: 'border-cyan-500/50',
    glowColor: 'shadow-cyan-500/20'
  },
  {
    id: 'contradiction_agent',
    name: 'Contradiction Hunter',
    role: 'Cross-Document Conflict & Revision Detection',
    icon: GitCompare,
    color: 'from-rose-500 to-pink-600',
    borderColor: 'border-rose-500/50',
    glowColor: 'shadow-rose-500/20'
  },
  {
    id: 'entity_agent',
    name: 'Entity & Graph Extractor',
    role: 'Co-occurrence & Semantic Graphing',
    icon: GitBranch,
    color: 'from-emerald-500 to-green-600',
    borderColor: 'border-emerald-500/50',
    glowColor: 'shadow-emerald-500/20'
  },
  {
    id: 'timeline_agent',
    name: 'Timeline Specialist',
    role: 'Temporal Anchoring & Chronology',
    icon: CalendarClock,
    color: 'from-amber-500 to-yellow-600',
    borderColor: 'border-amber-500/50',
    glowColor: 'shadow-amber-500/20'
  },
  {
    id: 'gap_agent',
    name: 'Gap & Uncertainty Agent',
    role: 'Blind Spot & Unsupported Claim Audit',
    icon: ShieldAlert,
    color: 'from-orange-500 to-amber-600',
    borderColor: 'border-orange-500/50',
    glowColor: 'shadow-orange-500/20'
  },
  {
    id: 'synthesis_agent',
    name: 'Synthesis & Explainer',
    role: 'Phase 11 Answer Contract Synthesis',
    icon: Cpu,
    color: 'from-violet-500 to-purple-700',
    borderColor: 'border-violet-500/50',
    glowColor: 'shadow-violet-500/20'
  }
];

export default function SpecialistCanvas({
  isExecuting = false,
  activePlanTrace = [],
  intent = null,
  latencyMs = null
}) {
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 my-6">
      <div className="p-5 rounded-2xl bg-trust-surface/60 border border-trust-border/80 shadow-xl backdrop-blur-sm">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-trust-border/50">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-trust-accent/20 border border-trust-accent/40 text-trust-accent">
              <Network className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide">
                Specialized Reasoning Capabilities
              </h3>
              <p className="text-[11px] text-trust-muted font-mono">
                Autonomous specialists deployed over your workspace data
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono">
            {intent && (
              <span className="px-2.5 py-1 rounded-lg bg-trust-card border border-trust-border text-trust-cyan">
                Intent: <strong className="text-white">{intent}</strong>
              </span>
            )}
            {latencyMs && (
              <span className="px-2.5 py-1 rounded-lg bg-trust-card border border-trust-border text-trust-green">
                Resolution: <strong className="text-white">{latencyMs}ms</strong>
              </span>
            )}
            {isExecuting && (
              <span className="flex items-center gap-1.5 text-trust-amber animate-pulse">
                <Activity className="w-3.5 h-3.5" />
                <span>Executing Plan...</span>
              </span>
            )}
          </div>
        </div>

        {/* 8-Agent Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {SPECIALISTS.map((agent) => {
            const Icon = agent.icon;
            // Check if this specialist was active in the plan trace
            const wasActive = activePlanTrace.length > 0;
            return (
              <div
                key={agent.id}
                className={`relative flex flex-col items-center text-center p-3 rounded-xl bg-trust-card/90 border transition-all duration-200 ${
                  isExecuting
                    ? 'border-trust-accent animate-pulse shadow-lg shadow-trust-accent/20'
                    : wasActive
                    ? `${agent.borderColor} shadow-md ${agent.glowColor}`
                    : 'border-trust-border/60 opacity-80 hover:opacity-100 hover:border-trust-border'
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center text-white shadow-md mb-2`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <h4 className="text-[11px] font-bold text-white leading-tight mb-0.5">
                  {agent.name}
                </h4>
                <p className="text-[9px] text-trust-muted font-mono leading-tight">
                  {agent.role}
                </p>

                {wasActive && (
                  <div className="absolute top-1.5 right-1.5">
                    <CheckCircle2 className="w-3 h-3 text-trust-green" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Dynamic Plan Execution Trace */}
        {activePlanTrace && activePlanTrace.length > 0 && (
          <div className="mt-4 pt-3 border-t border-trust-border/40">
            <span className="text-[10px] font-mono text-trust-muted uppercase tracking-wider block mb-2">
              Multi-Agent Execution Pipeline Trace
            </span>
            <div className="flex flex-wrap items-center gap-2">
              {activePlanTrace.map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1 rounded-lg bg-trust-card border border-trust-border text-gray-300"
                >
                  <span className="w-4 h-4 rounded-full bg-trust-accent/30 text-trust-accent text-[9px] flex items-center justify-center font-bold">
                    {idx + 1}
                  </span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
