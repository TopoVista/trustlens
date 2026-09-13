import React from 'react';
import { Check, CircleDot, FileSearch, GitCompare, Network, Timer, WandSparkles } from 'lucide-react';

const STAGES = [
  ['Read', 'Retrieve passages', FileSearch],
  ['Test', 'Compare claims', GitCompare],
  ['Connect', 'Map dates & entities', Network],
  ['Explain', 'Show support & gaps', WandSparkles]
];

export default function SpecialistCanvas({ isExecuting = false, activePlanTrace = [], intent, latencyMs }) {
  return <section className="border-t border-[var(--tl-line-300)] px-[clamp(1.2rem,3vw,2.15rem)] py-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><div className="editorial-kicker tl-status">Verification path</div><p className="mt-1 text-xs font-semibold text-[#28251f]">Only the checks a question needs are activated.</p></div><div className="flex items-center gap-2 text-[10px] font-mono text-[#6d665d]">{intent && <span className="tl-pill px-2.5 py-1">{intent}</span>}{latencyMs !== undefined && latencyMs !== null && <span className="tl-pill inline-flex items-center gap-1 px-2.5 py-1"><Timer className="h-3 w-3" />{latencyMs}ms</span>}{isExecuting && <span className="inline-flex items-center gap-1 rounded-full bg-[var(--tl-sage-100)] px-2.5 py-1 text-[var(--tl-sage-600)]"><CircleDot className="h-3 w-3 animate-pulse" />working</span>}</div></div><div className="tl-path">{STAGES.map(([title, copy, Icon]) => <div className="tl-path-step" key={title}><Icon className="h-3.5 w-3.5 tl-status" /><span><b className="text-[#28251f]">{title}</b> <span className="hidden sm:inline">· {copy}</span></span></div>)}</div>{activePlanTrace.length > 0 && <div className="mt-3 flex flex-wrap items-center gap-2 text-[10px] font-mono text-[#6d665d]"><span className="editorial-kicker">Last route</span>{activePlanTrace.map((step, index) => <span key={`${step}-${index}`} className="tl-pill inline-flex items-center gap-1 px-2 py-1"><Check className="h-3 w-3 tl-status" />{step}</span>)}</div>}</section>;
}
