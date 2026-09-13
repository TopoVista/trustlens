import React, { useState } from 'react';
import { Activity, ArrowUpRight, GitCompare, Search, ShieldAlert, Sparkles, TimerReset } from 'lucide-react';

const PROMPTS = [
  { label: 'Find a contradiction', query: 'Are there any conflicting dates or budget numbers across documents?', icon: GitCompare },
  { label: 'Check a claim', query: 'Which statements in this workspace have the strongest supporting evidence?', icon: Sparkles },
  { label: 'Find gaps', query: 'Audit this workspace for blind spots and unsupported assertions.', icon: ShieldAlert },
  { label: 'Build a timeline', query: 'What is the chronological timeline of key events and milestones?', icon: TimerReset }
];

export default function QueryConsole({ onRunQuery, isLoading = false, progressMessage = null, activeWorkspace }) {
  const [query, setQuery] = useState('');
  const canQuery = Boolean(activeWorkspace?.id) && !isLoading;
  const submit = (event) => { event?.preventDefault(); if (query.trim() && canQuery) onRunQuery(query.trim()); };
  const usePrompt = (prompt) => { setQuery(prompt); if (canQuery) onRunQuery(prompt); };

  return <section className="tl-query"><div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><div className="editorial-kicker tl-status">Ask the record</div><p className="mt-1 text-sm font-semibold tracking-[-.025em] text-[#28251f]">A grounded answer begins with the right question.</p></div><span className="tl-pill hidden px-3 py-1.5 text-[10px] font-mono sm:block">{activeWorkspace?.name || 'No workspace selected'}</span></div><form onSubmit={submit} className="tl-query-form"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-[10px] bg-[var(--tl-paper-200)] tl-status"><Search className="h-4.5 w-4.5" /></span><input value={query} onChange={(event) => setQuery(event.target.value)} disabled={isLoading || !activeWorkspace?.id} placeholder={activeWorkspace ? `Ask about ${activeWorkspace.name}…` : 'Choose a workspace to ask a question'} className="tl-query-input" /><button disabled={!query.trim() || !canQuery} className="tl-primary inline-flex h-10 shrink-0 items-center gap-2 px-3 text-[11px] font-bold disabled:cursor-not-allowed disabled:opacity-40 sm:px-4">{isLoading ? <><span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" /><span className="hidden sm:inline">Verifying</span></> : <><span className="hidden sm:inline">Verify</span><ArrowUpRight className="h-4 w-4" /></>}</button></form>{isLoading && <p aria-live="polite" className="tl-progress"><Activity className="h-3.5 w-3.5 shrink-0 animate-pulse" /><span className="truncate">{progressMessage || 'Preparing the verification path.'}</span></p>}<div className="mt-4 flex flex-wrap gap-2">{PROMPTS.map(({ label, query: prompt, icon: Icon }) => <button key={label} onClick={() => usePrompt(prompt)} disabled={!canQuery} className="tl-secondary inline-flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-semibold disabled:cursor-not-allowed disabled:opacity-45"><Icon className="h-3 w-3 tl-status" />{label}</button>)}</div></section>;
}
