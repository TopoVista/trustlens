import React from 'react';
import { AlertTriangle, Bell, FileText, GitCompare, HelpCircle, Layers, ShieldCheck, Timer } from 'lucide-react';

const METRICS = [
  ['documents', 'Sources', FileText, 'text-trust-cyan', 'Documents retained in this workspace'],
  ['claims', 'Claims', ShieldCheck, 'text-trust-green', 'Assertions extracted for review'],
  ['entities', 'Entities', Layers, 'text-[#c7b7ff]', 'People, concepts, and organizations'],
  ['events', 'Events', Timer, 'text-trust-amber', 'Dates and milestones found']
];

export default function HealthAuditDashboard({ healthData, discoveries = [], activeWorkspace }) {
  if (!healthData) return <section className="border-x border-b border-white/[.09] bg-[#0c0d1b] px-5 py-12 text-center text-xs text-[#989bb0]">Health data will appear after the workspace is ready.</section>;
  const { documents = 0, claims = 0, entities = 0, events = 0, breakdown = {}, major_contradictions: conflicts = 0, knowledge_gaps: gaps = 0 } = healthData;
  const supported = breakdown.supported_pct || 0;
  const contradicted = breakdown.contradicted_pct || 0;
  const unresolved = breakdown.unresolved_unsupported_pct || 0;
  const values = { documents, claims, entities, events };

  return <section className="border-x border-b border-white/[.09] bg-[#0c0d1b] px-5 py-7 sm:px-7 sm:py-8"><div className="mx-auto max-w-5xl"><div className="flex flex-wrap items-end justify-between gap-4"><div><div className="editorial-kicker text-[#999cb3]">Evidence health</div><h3 className="mt-2 text-xl font-extrabold tracking-[-.045em] text-white">See where your record is strong—and where it is thin.</h3><p className="mt-2 text-xs text-[#a1a4ba]">Verification overview for {activeWorkspace?.name || 'this workspace'}.</p></div><div className="flex gap-2"><span className="rounded-full border border-trust-red/25 bg-trust-red-bg px-2.5 py-1 text-[10px] font-mono text-[#ffc1c7]">{conflicts} conflicts</span><span className="rounded-full border border-trust-amber/25 bg-trust-amber-bg px-2.5 py-1 text-[10px] font-mono text-[#f8d890]">{gaps} gaps</span></div></div>
    <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">{METRICS.map(([key, title, Icon, color, copy]) => <article key={key} className="rounded-[18px] border border-white/[.09] bg-[#15172a] p-4"><Icon className={`h-4 w-4 ${color}`} /><p className="mt-5 text-3xl font-extrabold tracking-[-.06em] text-white">{values[key]}</p><p className="mt-1 text-xs font-bold text-[#e4e4ee]">{title}</p><p className="mt-1 text-[10px] leading-4 text-[#8d90a6]">{copy}</p></article>)}</div>
    <article className="mt-4 overflow-hidden rounded-[20px] border border-white/[.09] bg-[#15172a]"><div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-end sm:justify-between"><div><p className="editorial-kicker text-[#999cb3]">Claim distribution</p><h4 className="mt-2 text-sm font-extrabold text-white">How the available evidence treats extracted claims</h4></div><div className="flex flex-wrap gap-3 text-[10px] font-mono"><span className="text-trust-green">{supported}% supported</span><span className="text-trust-red">{contradicted}% contradicted</span><span className="text-trust-amber">{unresolved}% unresolved</span></div></div><div className="flex h-3 bg-black/20"><span className="bg-trust-green" style={{ width: `${supported}%` }} /><span className="bg-trust-red" style={{ width: `${contradicted}%` }} /><span className="bg-trust-amber" style={{ width: `${unresolved}%` }} /></div></article>
    {discoveries.length > 0 && <article className="mt-4 rounded-[20px] border border-white/[.09] bg-[#15172a] p-5"><div className="flex items-center gap-2"><Bell className="h-4 w-4 text-trust-amber" /><div><p className="text-sm font-extrabold text-white">Review queue</p><p className="mt-1 text-[10px] font-mono text-[#9497ae]">Cross-document signals worth looking at</p></div></div><div className="mt-4 grid gap-3">{discoveries.map((item, index) => { const conflict = item.type === 'contradiction'; const Icon = conflict ? GitCompare : HelpCircle; return <div key={item.id || index} className={`rounded-xl border p-3.5 ${conflict ? 'border-trust-red/25 bg-trust-red-bg' : 'border-trust-amber/25 bg-trust-amber-bg'}`}><div className="flex items-start gap-2"><Icon className={`mt-0.5 h-4 w-4 shrink-0 ${conflict ? 'text-trust-red' : 'text-trust-amber'}`} /><div><p className="text-xs font-extrabold text-white">{item.title || 'Review item'}</p><p className="mt-1 text-xs leading-5 text-[#d3c6af]">{item.summary || item.detail}</p></div></div></div>; })}</div></article>}
  </div></section>;
}
