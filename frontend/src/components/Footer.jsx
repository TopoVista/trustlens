import React from 'react';
import { ArrowUpRight, ShieldCheck } from 'lucide-react';

export default function Footer() {
  return <footer className="mt-auto border-t border-[var(--tl-line-300)] px-5 py-7"><div className="tl-shell flex flex-col gap-3 text-[10px] font-mono text-[#6d665d] sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5 tl-status" /><span>TrustLens · evidence-first workspace intelligence</span></div><div className="flex items-center gap-4"><span>Keep your sources reviewable.</span><a href="https://github.com/TopoVista/trustlens" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[#28251f] hover:text-[var(--tl-clay-700)]">Project source <ArrowUpRight className="h-3 w-3" /></a></div></div></footer>;
}
