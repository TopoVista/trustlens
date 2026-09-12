import React from 'react';
import { ArrowUpRight, ShieldCheck } from 'lucide-react';

export default function Footer() {
  return <footer className="border-t border-white/[.075] bg-[#090a16]/70 px-5 py-7"><div className="mx-auto flex max-w-[1440px] flex-col gap-3 text-[10px] font-mono text-[#85899f] sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5 text-[#b9a5ff]" /><span>TrustLens · evidence-first workspace intelligence</span></div><div className="flex items-center gap-4"><span>Keep your sources reviewable.</span><a href="https://github.com/TopoVista/trustlens" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[#c1c3d4] transition hover:text-white">Project source <ArrowUpRight className="h-3 w-3" /></a></div></div></footer>;
}
