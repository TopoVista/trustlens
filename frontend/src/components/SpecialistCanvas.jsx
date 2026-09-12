import React from 'react';
import { BrainCircuit, Check, CircleDot, FileSearch, GitCompare, Network, Timer, WandSparkles } from 'lucide-react';

const STAGES = [
  { title: 'Read', copy: 'Retrieve relevant passages', icon: FileSearch },
  { title: 'Test', copy: 'Compare claims to evidence', icon: GitCompare },
  { title: 'Connect', copy: 'Map entities and dates', icon: Network },
  { title: 'Explain', copy: 'Surface the answer and gaps', icon: WandSparkles }
];

export default function SpecialistCanvas({ isExecuting = false, activePlanTrace = [], intent, latencyMs }) {
  return (
    <section className="border-x border-b border-white/[.09] bg-[#0c0d1b] px-5 py-6 sm:px-7">
      <div className="mx-auto max-w-5xl assurance-card overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-white/[.08] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#7ee8ef]/10 text-trust-cyan"><BrainCircuit className="h-[18px] w-[18px]" /></span><div><div className="editorial-kicker text-[#9d9fb5]">Verification path</div><p className="mt-1 text-xs font-bold text-white">Specialists activate only when the question needs them.</p></div></div>
          <div className="flex items-center gap-2 text-[10px] font-mono">
            {intent && <span className="rounded-full border border-white/[.1] bg-white/[.035] px-2.5 py-1.5 text-[#c1c3d4]">intent: <b className="text-white">{intent}</b></span>}
            {latencyMs && <span className="inline-flex items-center gap-1 rounded-full border border-white/[.1] bg-white/[.035] px-2.5 py-1.5 text-[#c1c3d4]"><Timer className="h-3 w-3 text-trust-cyan" />{latencyMs}ms</span>}
            {isExecuting && <span className="inline-flex items-center gap-1 rounded-full bg-[#8d6cff]/15 px-2.5 py-1.5 text-[#cfC2ff]"><CircleDot className="h-3 w-3 animate-pulse" />working</span>}
          </div>
        </div>
        <div className="grid grid-cols-2 divide-x divide-y divide-white/[.07] sm:grid-cols-4 sm:divide-y-0">
          {STAGES.map(({ title, copy, icon: Icon }, index) => <div key={title} className="relative p-4 sm:p-5"><span className="absolute right-3 top-3 text-[9px] font-mono text-[#666a82]">0{index + 1}</span><span className="grid h-8 w-8 place-items-center rounded-lg bg-white/[.045] text-[#c7b7ff]"><Icon className="h-4 w-4" /></span><p className="mt-3 text-xs font-extrabold text-white">{title}</p><p className="mt-1 text-[10px] leading-4 text-[#9699b1]">{copy}</p></div>)}
        </div>
        {activePlanTrace.length > 0 && <div className="flex flex-wrap items-center gap-2 border-t border-white/[.07] bg-black/10 px-5 py-3"><span className="editorial-kicker mr-1 text-[#8f92aa]">last route</span>{activePlanTrace.map((step, index) => <span key={`${step}-${index}`} className="inline-flex items-center gap-1.5 rounded-full border border-white/[.09] bg-white/[.035] px-2 py-1 text-[10px] font-mono text-[#c7c9d9]"><Check className="h-3 w-3 text-trust-green" />{step}</span>)}</div>}
      </div>
    </section>
  );
}
