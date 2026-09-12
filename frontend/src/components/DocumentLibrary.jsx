import React from 'react';
import { FileText, FolderOpen, Fingerprint, ShieldCheck } from 'lucide-react';

const authorityTone = (authority = 'MEDIUM') => {
  if (authority === 'OFFICIAL' || authority === 'HIGH') return 'border-trust-green/30 bg-trust-green-bg text-trust-green';
  if (authority === 'UNVERIFIED') return 'border-trust-amber/30 bg-trust-amber-bg text-trust-amber';
  return 'border-[#a889ff]/30 bg-[#8d6cff]/12 text-[#c9bcff]';
};

export default function DocumentLibrary({ documents = [], activeWorkspace }) {
  return (
    <section className="border-x border-b border-white/[.09] bg-[#0c0d1b] px-5 py-7 sm:px-7 sm:py-8">
      <div className="mx-auto max-w-5xl">
        <div className="flex flex-wrap items-end justify-between gap-4"><div><div className="editorial-kicker flex items-center gap-2 text-[#999cb3]"><FolderOpen className="h-3.5 w-3.5 text-trust-cyan" />Source register</div><h3 className="mt-2 text-xl font-extrabold tracking-[-.045em] text-white">Your documents, with their authority intact.</h3><p className="mt-2 text-xs leading-5 text-[#a2a5bb]">Every source below belongs to <span className="font-semibold text-[#d9d9e6]">{activeWorkspace?.name || 'this workspace'}</span>.</p></div><span className="rounded-full border border-white/[.1] bg-white/[.035] px-3 py-1.5 text-[10px] font-mono text-[#b9bbcc]">{documents.length} retained source{documents.length === 1 ? '' : 's'}</span></div>
        {documents.length === 0 ? <div className="mt-6 rounded-[20px] border border-dashed border-white/[.13] bg-white/[.02] px-5 py-14 text-center"><FileText className="mx-auto h-7 w-7 text-[#777b94]" /><p className="mt-3 text-sm font-bold text-white">No documents yet</p><p className="mx-auto mt-2 max-w-sm text-xs leading-5 text-[#989bb1]">Add a note, markdown file, CSV, or plain-text document to start building a reviewable evidence record.</p></div> : <div className="mt-6 grid gap-3">{documents.map((document, index) => <article key={document.id} className="group relative overflow-hidden rounded-[18px] border border-white/[.09] bg-[#141628] p-4 transition hover:-translate-y-0.5 hover:border-[#a889ff]/34 hover:bg-[#17192f] sm:p-5"><span className="absolute bottom-0 left-0 top-0 w-1 bg-gradient-to-b from-[#9b7cff] via-[#7ee8ef] to-transparent opacity-70" /><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div className="flex min-w-0 gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-white/[.08] bg-white/[.035] text-[#c8bbff]"><FileText className="h-4.5 w-4.5" /></span><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h4 className="truncate text-sm font-extrabold text-white">{document.title || 'Untitled source'}</h4><span className="text-[10px] font-mono text-[#777b94]">#{String(index + 1).padStart(2, '0')}</span></div><p className="mt-1 truncate text-[11px] text-[#9c9eb3]">{document.filename || 'Uploaded document'}</p><p className="mt-3 flex items-center gap-1.5 break-all text-[10px] font-mono text-[#73768e]"><Fingerprint className="h-3 w-3 text-[#989bb1]" />{document.id}</p></div></div><div className="flex flex-wrap items-center gap-2"><span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-mono font-bold ${authorityTone(document.authority_level)}`}><ShieldCheck className="h-3 w-3" />{document.authority_level || 'MEDIUM'}</span><span className="rounded-full border border-white/[.09] bg-black/[.12] px-2.5 py-1 text-[10px] font-mono text-[#b6b8c8]">{document.ingestion_status || 'READY'}</span></div></div></article>)}</div>}
      </div>
    </section>
  );
}
