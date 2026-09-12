import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, FileText, GitCompare, HelpCircle, Layers, Quote, ShieldCheck, Sparkles, XCircle } from 'lucide-react';
import { toConfidencePercent } from '../utils/confidence';

const verdictStyle = (status = '') => {
  const normalized = status.toUpperCase();
  if (normalized === 'SUPPORTED') return { label: 'Supported', dot: 'bg-trust-green', color: 'text-trust-green', panel: 'border-trust-green/30 bg-trust-green-bg' };
  if (normalized === 'CONTRADICTED') return { label: 'Contradicted', dot: 'bg-trust-red', color: 'text-trust-red', panel: 'border-trust-red/30 bg-trust-red-bg' };
  return { label: normalized.replace(/_/g, ' ') || 'Unresolved', dot: 'bg-trust-amber', color: 'text-trust-amber', panel: 'border-trust-amber/30 bg-trust-amber-bg' };
};

export default function AnswerContractPanel({ data }) {
  const [tab, setTab] = useState('answer');
  const [expanded, setExpanded] = useState(null);
  if (!data) return null;

  const { query, intent, answer, confidence = 0, claims = [], evidence = [], contradictions = [], unknowns = [], latency_ms: latencyMs } = data;
  const confidencePercent = toConfidencePercent(confidence);
  const confidenceTone = confidencePercent >= 80 ? 'text-trust-green border-trust-green/30 bg-trust-green-bg' : confidencePercent >= 60 ? 'text-trust-amber border-trust-amber/30 bg-trust-amber-bg' : 'text-trust-red border-trust-red/30 bg-trust-red-bg';
  const supportedClaims = claims.filter((claim) => claim.status?.toUpperCase() === 'SUPPORTED').length;

  return (
    <section className="border-x border-b border-white/[.09] bg-[#0c0d1b] px-5 pb-8 sm:px-7">
      <div className="mx-auto max-w-5xl overflow-hidden rounded-b-[22px] border border-t-0 border-white/[.09] bg-[#121426] shadow-[0_24px_70px_rgba(0,0,0,.22)]">
        <header className="flex flex-col gap-4 border-b border-white/[.08] bg-gradient-to-r from-white/[.035] to-transparent px-5 py-5 sm:flex-row sm:items-start sm:justify-between sm:px-7">
          <div className="min-w-0"><div className="editorial-kicker flex items-center gap-2 text-[#a7a9c0]"><Sparkles className="h-3.5 w-3.5 text-[#c7b7ff]" />Grounded synthesis</div><h3 className="mt-2 truncate text-sm font-extrabold tracking-[-.025em] text-white sm:text-base">{query}</h3>{intent && <p className="mt-1 text-[10px] font-mono text-[#8e91aa]">analysis intent: {intent}</p>}</div>
          <div className="flex shrink-0 items-center gap-2"><span className={`rounded-full border px-3 py-1.5 text-[11px] font-mono font-bold ${confidenceTone}`}>{confidencePercent}% confidence</span>{latencyMs !== undefined && latencyMs !== null && <span className="rounded-full border border-white/[.09] bg-black/[.13] px-3 py-1.5 text-[10px] font-mono text-[#a5a8bd]">{latencyMs}ms</span>}</div>
        </header>

        <div className="px-5 pt-5 sm:px-7">
          <div className="flex flex-wrap gap-2 border-b border-white/[.08] pb-4">
            {[['answer', 'Synthesis', FileText, null], ['claims', `Claims ${claims.length}`, ShieldCheck, null], ['evidence', `Evidence ${evidence.length}`, Layers, null], ...(contradictions.length ? [['contradictions', `Conflicts ${contradictions.length}`, GitCompare, 'danger']] : [])].map(([id, label, Icon, variant]) => <button key={id} onClick={() => setTab(id)} className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[10px] font-bold transition ${tab === id ? variant === 'danger' ? 'border-trust-red/40 bg-trust-red-bg text-[#ffd3d7]' : 'border-[#a889ff]/45 bg-[#8d6cff]/18 text-white' : 'border-white/[.08] bg-white/[.025] text-[#a9abc0] hover:text-white'}`}><Icon className="h-3.5 w-3.5" />{label}</button>)}
          </div>
        </div>

        {tab === 'answer' && <div className="px-5 py-6 sm:px-7"><div className="grid gap-5 md:grid-cols-[1fr_185px]"><div className="min-w-0"><p className="text-[10px] font-mono uppercase tracking-[.15em] text-[#9497ae]">What the evidence supports</p><div className="mt-3 whitespace-pre-line text-sm leading-7 text-[#ececf5] sm:text-[15px]">{answer || 'No grounded conclusion could be synthesized from the available evidence.'}</div></div><aside className="rounded-2xl border border-white/[.08] bg-black/[.13] p-4"><p className="text-[10px] font-mono uppercase tracking-[.12em] text-[#9194ab]">Review summary</p><p className="mt-3 text-2xl font-extrabold tracking-[-.05em] text-white">{supportedClaims}<span className="text-sm text-[#777b93]">/{claims.length}</span></p><p className="mt-1 text-[11px] leading-5 text-[#a5a8bb]">claims currently linked to supporting evidence</p><div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/[.07]"><div className="h-full rounded-full bg-trust-green" style={{ width: `${claims.length ? (supportedClaims / claims.length) * 100 : 0}%` }} /></div></aside></div></div>}

        {tab === 'claims' && <div className="space-y-3 px-5 py-6 sm:px-7">{claims.length === 0 ? <EmptyState text="This answer did not produce any atomic claims to inspect." /> : claims.map((claim, index) => { const style = verdictStyle(claim.status); const isOpen = expanded === index; const claimConfidence = toConfidencePercent(claim.confidence); return <article key={claim.id || index} className="overflow-hidden rounded-2xl border border-white/[.09] bg-white/[.025]"><button onClick={() => setExpanded(isOpen ? null : index)} className="flex w-full items-start gap-3 p-4 text-left"><span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${style.dot}`} /><span className="min-w-0 flex-1"><span className="block text-xs font-bold leading-5 text-white">{claim.claim_text || claim.statement || 'Untitled claim'}</span><span className="mt-1 block text-[10px] font-mono text-[#9295ac]">{claim.source_document || 'Workspace source'}{claim.authority ? ` · ${claim.authority}` : ''}</span></span><span className="flex shrink-0 items-center gap-2"><span className={`hidden rounded-full border px-2 py-1 text-[9px] font-mono font-bold sm:block ${style.panel} ${style.color}`}>{style.label}</span>{isOpen ? <ChevronUp className="h-4 w-4 text-[#a7a9bd]" /> : <ChevronDown className="h-4 w-4 text-[#a7a9bd]" />}</span></button>{isOpen && <div className="border-t border-white/[.075] bg-black/[.12] p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div className="max-w-2xl"><p className="text-[9px] font-mono uppercase tracking-[.13em] text-[#898ca4]">Linked evidence</p><p className="mt-2 text-xs leading-6 text-[#cdcfdd]">{claim.cited_passage || claim.supporting_evidence || 'No evidence passage is available for this claim.'}</p></div><span className="rounded-full border border-white/[.1] bg-white/[.035] px-2.5 py-1 text-[10px] font-mono text-[#c1c3d1]">{claimConfidence}% match</span></div></div>}</article>; })}</div>}

        {tab === 'evidence' && <div className="grid gap-3 px-5 py-6 sm:px-7">{evidence.length === 0 ? <EmptyState text="No source passages were returned for this answer." /> : evidence.map((item, index) => <article key={item.id || index} className="rounded-2xl border border-white/[.09] bg-white/[.025] p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-start gap-3"><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#7ee8ef]/10 text-trust-cyan"><Quote className="h-4 w-4" /></span><div><h4 className="text-xs font-extrabold text-white">{item.document_title || item.title || 'Document excerpt'}</h4><p className="mt-1 text-[10px] font-mono text-[#9295ab]">evidence {String(index + 1).padStart(2, '0')}{item.authority ? ` · ${item.authority}` : ''}</p></div></div>{item.similarity !== undefined && <span className="rounded-full border border-white/[.1] bg-black/[.14] px-2.5 py-1 text-[10px] font-mono text-[#bfc2d2]">{toConfidencePercent(item.similarity)}% relevance</span>}</div><p className="mt-4 rounded-xl border border-white/[.06] bg-black/[.12] p-3 text-xs leading-6 text-[#d1d2df]">{item.snippet || item.passage || item.text || 'No passage preview available.'}</p></article>)}</div>}

        {tab === 'contradictions' && <div className="grid gap-3 px-5 py-6 sm:px-7">{contradictions.map((item, index) => <article key={item.id || index} className="rounded-2xl border border-trust-red/30 bg-trust-red-bg p-4"><div className="flex items-start gap-3"><XCircle className="mt-0.5 h-4 w-4 shrink-0 text-trust-red" /><div><p className="text-xs font-extrabold text-[#ffd8dc]">{item.statement || item.title || 'Potential conflict'}</p><p className="mt-2 text-xs leading-6 text-[#eab9c0]">{item.detail || item.conflict_description || item.summary}</p></div></div></article>)}</div>}

        {(unknowns.length > 0 && tab === 'answer') && <div className="mx-5 mb-6 flex items-start gap-3 rounded-2xl border border-trust-amber/25 bg-trust-amber-bg p-4 sm:mx-7"><HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-trust-amber" /><div><p className="text-xs font-extrabold text-[#ffe0a0]">What remains uncertain</p><ul className="mt-2 space-y-1 text-xs leading-5 text-[#e1c58d]">{unknowns.slice(0, 3).map((item, index) => <li key={index}>• {typeof item === 'string' ? item : item.summary || item.question}</li>)}</ul></div></div>}
      </div>
    </section>
  );
}

function EmptyState({ text }) {
  return <div className="rounded-2xl border border-dashed border-white/[.12] bg-white/[.02] px-5 py-10 text-center text-xs text-[#9a9db3]"><AlertTriangle className="mx-auto mb-3 h-5 w-5 text-[#85889f]" />{text}</div>;
}
