import React, { useState } from 'react';
import { ArrowUpRight, GitCompare, Search, ShieldAlert, Sparkles, TimerReset } from 'lucide-react';

const PROMPTS = [
  { label: 'Find a contradiction', query: 'Are there any conflicting dates or budget numbers across documents?', icon: GitCompare },
  { label: 'Check a claim', query: 'Which statements in this workspace have the strongest supporting evidence?', icon: Sparkles },
  { label: 'Find gaps', query: 'Audit this workspace for blind spots and unsupported assertions.', icon: ShieldAlert },
  { label: 'Build a timeline', query: 'What is the chronological timeline of key events and milestones?', icon: TimerReset }
];

export default function QueryConsole({ onRunQuery, isLoading = false, activeWorkspace }) {
  const [query, setQuery] = useState('');
  const canQuery = Boolean(activeWorkspace?.id) && !isLoading;

  const submit = (event) => {
    event?.preventDefault();
    if (!query.trim() || !canQuery) return;
    onRunQuery(query.trim());
  };

  const usePrompt = (prompt) => {
    setQuery(prompt);
    if (canQuery) onRunQuery(prompt);
  };

  return (
    <section className="border-x border-b border-white/[.09] bg-[#111225]/78 px-5 py-7 backdrop-blur-xl sm:px-7 sm:py-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div><div className="editorial-kicker text-[#999bb2]">Ask the record</div><p className="mt-1 text-sm font-bold tracking-[-.02em] text-white">Get a synthesis with the evidence beside it.</p></div>
          <span className="hidden rounded-full border border-white/[.09] bg-white/[.035] px-3 py-1.5 text-[10px] font-mono text-[#a9abc0] sm:block">{activeWorkspace?.name || 'No workspace selected'}</span>
        </div>
        <form onSubmit={submit} className="group relative rounded-[18px] border border-white/[.13] bg-[#0b0c1a] p-1.5 shadow-[0_20px_50px_rgba(0,0,0,.18)] transition focus-within:border-[#a889ff]/65 focus-within:shadow-[0_20px_55px_rgba(91,64,190,.18)]">
          <div className="flex items-center gap-2 sm:gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#8d6cff]/15 text-[#c6b7ff]"><Search className="h-4.5 w-4.5" /></span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} disabled={isLoading || !activeWorkspace?.id} placeholder={activeWorkspace ? `Ask about ${activeWorkspace.name}…` : 'Choose a workspace to ask a question'} className="min-w-0 flex-1 bg-transparent py-3 text-sm text-white outline-none placeholder:text-[#6f7188] disabled:cursor-not-allowed" />
            <button disabled={!query.trim() || !canQuery} className="inline-flex h-10 shrink-0 items-center gap-2 rounded-xl bg-[#9b7cff] px-3 text-[11px] font-extrabold text-white transition hover:bg-[#ac91ff] disabled:cursor-not-allowed disabled:opacity-40 sm:px-4">
              {isLoading ? <><span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/25 border-t-white" /><span className="hidden sm:inline">Verifying</span></> : <><span className="hidden sm:inline">Verify</span><ArrowUpRight className="h-4 w-4" /></>}
            </button>
          </div>
        </form>
        <div className="mt-4 flex flex-wrap gap-2">
          {PROMPTS.map(({ label, query: prompt, icon: Icon }) => <button key={label} onClick={() => usePrompt(prompt)} disabled={!canQuery} className="inline-flex items-center gap-1.5 rounded-full border border-white/[.09] bg-white/[.025] px-3 py-1.5 text-[10px] font-semibold text-[#b9bbcf] transition hover:border-[#a889ff]/45 hover:bg-[#8d6cff]/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-45"><Icon className="h-3 w-3 text-[#a889ff]" />{label}</button>)}
        </div>
      </div>
    </section>
  );
}
