import React, { useState } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  FileText, 
  ShieldCheck, 
  ExternalLink, 
  Sparkles, 
  GitCompare, 
  HelpCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Bookmark,
  Layers
} from 'lucide-react';

export default function AnswerContractPanel({ data }) {
  if (!data) return null;

  const {
    query,
    intent,
    answer,
    confidence = 0.85,
    claims = [],
    evidence = [],
    contradictions = [],
    assumptions = [],
    unknowns = [],
    related_knowledge = [],
    plan_trace = [],
    latency_ms
  } = data;

  const [expandedClaim, setExpandedClaim] = useState(null);
  const [activeTab, setActiveTab] = useState('answer'); // 'answer' | 'claims' | 'evidence' | 'contradictions'

  // Confidence color
  const confPct = Math.round(confidence * 100);
  const confColor = confPct >= 80 ? 'text-trust-green' : confPct >= 60 ? 'text-trust-amber' : 'text-trust-red';
  const confBg = confPct >= 80 ? 'bg-trust-green/20 border-trust-green/40' : confPct >= 60 ? 'bg-trust-amber/20 border-trust-amber/40' : 'bg-trust-red/20 border-trust-red/40';

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 my-6 space-y-6">
      {/* 1. Main Answer Card */}
      <div className="rounded-2xl bg-trust-card border border-trust-border shadow-2xl overflow-hidden">
        {/* Answer Header */}
        <div className="px-6 py-4 border-b border-trust-border/80 bg-trust-surface/60 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-trust-accent/20 border border-trust-accent/40 text-trust-accent">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-trust-muted block">
                Evidence-Grounded Synthesis
              </span>
              <h3 className="text-sm font-bold text-white line-clamp-1">{query}</h3>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1 rounded-xl text-xs font-mono font-bold border ${confBg} ${confColor}`}>
              {confPct}% Confidence
            </span>
            {latency_ms && (
              <span className="px-2.5 py-1 rounded-xl text-xs font-mono text-gray-400 bg-trust-surface border border-trust-border">
                {latency_ms}ms
              </span>
            )}
          </div>
        </div>

        {/* Answer Narrative */}
        <div className="p-6">
          <div className="text-sm text-gray-100 leading-relaxed space-y-3 font-sans">
            {answer ? (
              <p className="whitespace-pre-line text-sm sm:text-base leading-relaxed">
                {answer}
              </p>
            ) : (
              <p className="text-trust-muted italic">
                No grounded conclusion could be synthesized with sufficient evidence.
              </p>
            )}
          </div>

          {/* Inline Navigation Pills */}
          <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t border-trust-border/50">
            <button
              onClick={() => setActiveTab('answer')}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'answer'
                  ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                  : 'bg-trust-surface text-gray-400 hover:text-white'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Synthesis Overview</span>
            </button>

            <button
              onClick={() => setActiveTab('claims')}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'claims'
                  ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                  : 'bg-trust-surface text-gray-400 hover:text-white'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Atomic Claims ({claims.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('evidence')}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'evidence'
                  ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                  : 'bg-trust-surface text-gray-400 hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Evidence Sources ({evidence.length})</span>
            </button>

            {contradictions.length > 0 && (
              <button
                onClick={() => setActiveTab('contradictions')}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
                  activeTab === 'contradictions'
                    ? 'bg-trust-red text-white shadow-md shadow-trust-red/20'
                    : 'bg-trust-red-bg text-trust-red border border-trust-red/30'
                }`}
              >
                <GitCompare className="w-3.5 h-3.5" />
                <span>Contradictions ({contradictions.length})</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 2. TAB: ATOMIC CLAIM DECOMPOSITION */}
      {activeTab === 'claims' && (
        <div className="space-y-3 animate-in fade-in">
          <div className="flex items-center justify-between pb-1">
            <h4 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-trust-accent" />
              Atomic Claim Verification Breakdown
            </h4>
            <span className="text-xs font-mono text-trust-muted">
              {claims.filter((c) => c.status === 'SUPPORTED').length}/{claims.length} Supported
            </span>
          </div>

          <div className="space-y-2.5">
            {claims.map((claim, idx) => {
              const isSupported = claim.status === 'SUPPORTED';
              const isContradicted = claim.status === 'CONTRADICTED';
              const isUnresolved = claim.status === 'UNRESOLVED' || claim.status === 'UNRESOLVED_UNSUPPORTED';

              const badgeColor = isSupported
                ? 'bg-trust-green-bg border-trust-green/40 text-trust-green'
                : isContradicted
                ? 'bg-trust-red-bg border-trust-red/40 text-trust-red'
                : 'bg-trust-amber-bg border-trust-amber/40 text-trust-amber';

              const StatusIcon = isSupported ? CheckCircle2 : isContradicted ? XCircle : AlertTriangle;

              return (
                <div
                  key={claim.id || idx}
                  className="rounded-xl bg-trust-card border border-trust-border/80 overflow-hidden hover:border-trust-accent/40 transition-colors"
                >
                  <div
                    onClick={() => setExpandedClaim(expandedClaim === idx ? null : idx)}
                    className="p-4 flex items-start justify-between gap-3 cursor-pointer"
                  >
                    <div className="flex items-start space-x-3">
                      <div className="mt-0.5">
                        <StatusIcon
                          className={`w-4 h-4 ${
                            isSupported
                              ? 'text-trust-green'
                              : isContradicted
                              ? 'text-trust-red'
                              : 'text-trust-amber'
                          }`}
                        />
                      </div>
                      <div>
                        <p className="text-xs font-medium text-white leading-snug">
                          {claim.claim_text || claim.statement}
                        </p>
                        <div className="flex items-center gap-3 mt-1 text-[11px] font-mono text-trust-muted">
                          <span>Source: {claim.source_document || 'Workspace Document'}</span>
                          {claim.authority && <span>• Authority: {claim.authority}</span>}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${badgeColor}`}>
                        {claim.status || 'SUPPORTED'}
                      </span>
                      {expandedClaim === idx ? (
                        <ChevronUp className="w-4 h-4 text-trust-muted" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-trust-muted" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Evidence Details */}
                  {expandedClaim === idx && (
                    <div className="px-4 pb-4 pt-2 border-t border-trust-border/40 bg-trust-surface/40 space-y-2">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-trust-muted block">
                        Linked Evidence Passage & Citation:
                      </span>
                      <blockquote className="p-3 rounded-lg bg-trust-card border border-trust-border text-xs font-mono text-gray-300 italic">
                        "{claim.cited_passage || claim.supporting_evidence || 'Direct evidence passage matching semantic embedding.'}"
                      </blockquote>
                      {claim.confidence && (
                        <div className="flex items-center gap-2 text-[11px] font-mono text-gray-400">
                          <span>Verification Confidence:</span>
                          <div className="w-24 h-1.5 bg-trust-surface rounded-full overflow-hidden">
                            <div
                              className="h-full bg-trust-accent"
                              style={{ width: `${Math.round(claim.confidence * 100)}%` }}
                            />
                          </div>
                          <span className="text-white font-bold">
                            {Math.round(claim.confidence * 100)}%
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 3. TAB: EVIDENCE SOURCES */}
      {activeTab === 'evidence' && (
        <div className="space-y-3 animate-in fade-in">
          <h4 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2 pb-1">
            <Layers className="w-4 h-4 text-trust-cyan" />
            Retrieved Evidence Passages
          </h4>

          <div className="grid gap-3">
            {evidence.map((item, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-trust-card border border-trust-border/80 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-white">
                      [E{idx + 1}] {item.document_title || item.title || 'Document Excerpt'}
                    </span>
                    {item.authority && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-trust-accent/20 border border-trust-accent/30 text-trust-accent">
                        {item.authority}
                      </span>
                    )}
                  </div>
                  {item.similarity && (
                    <span className="text-[10px] font-mono text-trust-green bg-trust-green-bg px-2 py-0.5 rounded border border-trust-green/30">
                      Sim: {(item.similarity * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <p className="text-xs font-mono text-gray-300 leading-relaxed bg-trust-surface/60 p-3 rounded-lg border border-trust-border/40">
                  {item.snippet || item.passage || item.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. CONTRADICTIONS & UNKNOWNS */}
      {(contradictions.length > 0 || unknowns.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Contradictions Panel */}
          {contradictions.length > 0 && (
            <div className="p-4 rounded-xl bg-trust-card border border-trust-red/40 space-y-2">
              <div className="flex items-center space-x-2 text-trust-red">
                <GitCompare className="w-4 h-4" />
                <h4 className="text-xs font-bold uppercase tracking-wider font-mono">
                  Contradictions & Evolution ({contradictions.length})
                </h4>
              </div>
              <div className="space-y-2">
                {contradictions.map((c, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-trust-red-bg text-xs space-y-1">
                    <p className="font-semibold text-trust-red">{c.statement || c.title}</p>
                    <p className="text-gray-300 text-[11px] font-mono">
                      {c.detail || c.conflict_description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unknowns & Uncertainty Panel */}
          {unknowns.length > 0 && (
            <div className="p-4 rounded-xl bg-trust-card border border-trust-amber/40 space-y-2">
              <div className="flex items-center space-x-2 text-trust-amber">
                <HelpCircle className="w-4 h-4" />
                <h4 className="text-xs font-bold uppercase tracking-wider font-mono">
                  Uncertainties & Knowledge Gaps ({unknowns.length})
                </h4>
              </div>
              <div className="space-y-1.5">
                {unknowns.map((u, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-trust-amber-bg text-xs text-gray-200 font-mono"
                  >
                    • {typeof u === 'string' ? u : u.summary || u.question}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
