import React from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  FileText, 
  Layers, 
  Activity, 
  Sparkles, 
  GitCompare, 
  Calendar, 
  Bell, 
  CheckCircle2, 
  XCircle,
  HelpCircle
} from 'lucide-react';

export default function HealthAuditDashboard({
  healthData,
  discoveries = [],
  activeWorkspace
}) {
  if (!healthData) return null;

  const {
    documents = 0,
    claims = 0,
    entities = 0,
    events = 0,
    breakdown = {},
    major_contradictions = 0,
    knowledge_gaps = 0
  } = healthData;

  const supportedPct = breakdown.supported_pct || 0;
  const contradictedPct = breakdown.contradicted_pct || 0;
  const unresolvedPct = breakdown.unresolved_unsupported_pct || 0;

  return (
    <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 my-6 space-y-6">
      {/* 1. Header & Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-trust-card border border-trust-border/80 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-trust-muted uppercase tracking-wider">
              Documents
            </span>
            <FileText className="w-4 h-4 text-trust-cyan" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">{documents}</div>
          <p className="text-[10px] font-mono text-gray-400 mt-1">Ingested in workspace</p>
        </div>

        <div className="p-4 rounded-2xl bg-trust-card border border-trust-border/80 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-trust-muted uppercase tracking-wider">
              Atomic Claims
            </span>
            <ShieldCheck className="w-4 h-4 text-trust-green" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">{claims}</div>
          <p className="text-[10px] font-mono text-gray-400 mt-1">Decomposed assertions</p>
        </div>

        <div className="p-4 rounded-2xl bg-trust-card border border-trust-border/80 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-trust-muted uppercase tracking-wider">
              Named Entities
            </span>
            <Layers className="w-4 h-4 text-trust-accent" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">{entities}</div>
          <p className="text-[10px] font-mono text-gray-400 mt-1">Knowledge graph nodes</p>
        </div>

        <div className="p-4 rounded-2xl bg-trust-card border border-trust-border/80 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-trust-muted uppercase tracking-wider">
              Temporal Events
            </span>
            <Calendar className="w-4 h-4 text-trust-amber" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">{events}</div>
          <p className="text-[10px] font-mono text-gray-400 mt-1">Anchored milestones</p>
        </div>
      </div>

      {/* 2. Verification Health Integrity Bar */}
      <div className="p-5 rounded-2xl bg-trust-card border border-trust-border/80 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-trust-accent" />
              Evidence Verification Distribution
            </h3>
            <p className="text-xs text-trust-muted font-mono">
              Integrity audit across all decomposed claims in this workspace
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-trust-green">
              <span className="w-2.5 h-2.5 rounded-full bg-trust-green" />
              Supported: {supportedPct}%
            </span>
            <span className="flex items-center gap-1.5 text-trust-red">
              <span className="w-2.5 h-2.5 rounded-full bg-trust-red" />
              Contradicted: {contradictedPct}%
            </span>
            <span className="flex items-center gap-1.5 text-trust-amber">
              <span className="w-2.5 h-2.5 rounded-full bg-trust-amber" />
              Unresolved: {unresolvedPct}%
            </span>
          </div>
        </div>

        {/* Multi-segment Progress Bar */}
        <div className="w-full h-3 bg-trust-surface rounded-full overflow-hidden flex shadow-inner">
          <div
            style={{ width: `${supportedPct}%` }}
            className="bg-trust-green h-full transition-all duration-500"
            title={`Supported: ${supportedPct}%`}
          />
          <div
            style={{ width: `${contradictedPct}%` }}
            className="bg-trust-red h-full transition-all duration-500"
            title={`Contradicted: ${contradictedPct}%`}
          />
          <div
            style={{ width: `${unresolvedPct}%` }}
            className="bg-trust-amber h-full transition-all duration-500"
            title={`Unresolved: ${unresolvedPct}%`}
          />
        </div>
      </div>

      {/* 3. Proactive "Things You Should Know" Discoveries Feed */}
      {discoveries && discoveries.length > 0 && (
        <div className="p-5 rounded-2xl bg-trust-card border border-trust-border/80 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 rounded-lg bg-trust-amber/20 border border-trust-amber/40 text-trust-amber">
                <Bell className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">
                  Proactive Intelligence: Things You Should Know
                </h3>
                <p className="text-xs text-trust-muted font-mono">
                  Autonomous pattern hunter discoveries surfaced from workspace cross-referencing
                </p>
              </div>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded-xl bg-trust-surface border border-trust-border text-gray-300">
              {discoveries.length} Discovered
            </span>
          </div>

          <div className="grid gap-3">
            {discoveries.map((item, idx) => {
              const isContradiction = item.type === 'contradiction';
              const isGap = item.type === 'gap';
              const borderColor = isContradiction
                ? 'border-trust-red/40 bg-trust-red-bg/50'
                : 'border-trust-amber/40 bg-trust-amber-bg/50';
              const iconColor = isContradiction ? 'text-trust-red' : 'text-trust-amber';
              const Icon = isContradiction ? GitCompare : HelpCircle;

              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border ${borderColor} space-y-2`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <Icon className={`w-4 h-4 ${iconColor} shrink-0`} />
                      <h4 className="text-xs font-bold text-white">{item.title}</h4>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-trust-card border border-trust-border text-gray-300">
                      {item.severity || 'NOTICE'}
                    </span>
                  </div>

                  <p className="text-xs text-gray-200">{item.summary}</p>

                  {item.detail && (
                    <p className="text-[11px] font-mono text-gray-400 bg-trust-card/60 p-2.5 rounded-lg border border-trust-border/40">
                      💡 {item.detail}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
