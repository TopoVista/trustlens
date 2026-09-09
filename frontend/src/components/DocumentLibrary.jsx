import React from 'react';
import { FileText, FolderOpen, ShieldCheck } from 'lucide-react';

export default function DocumentLibrary({ documents = [], activeWorkspace }) {
  return (
    <section className="w-full max-w-5xl mx-auto px-4 sm:px-6 my-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-trust-cyan" />
            Workspace Documents
          </h2>
          <p className="text-xs text-trust-muted font-mono mt-1">
            {activeWorkspace?.name || 'Current workspace'} · {documents.length} saved
          </p>
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="p-6 rounded-2xl bg-trust-card border border-trust-border text-center">
          <FileText className="w-6 h-6 text-trust-muted mx-auto mb-2" />
          <p className="text-sm text-gray-300">No documents have been ingested in this workspace yet.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {documents.map((document) => (
            <article key={document.id} className="p-4 rounded-2xl bg-trust-card border border-trust-border/80 shadow-lg">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-white truncate">{document.title}</h3>
                  <p className="text-[11px] text-trust-muted font-mono mt-1 break-all">
                    {document.filename} · {document.id}
                  </p>
                </div>
                <div className="flex items-center gap-2 text-[10px] font-mono">
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-trust-accent/15 border border-trust-accent/30 text-trust-accent">
                    <ShieldCheck className="w-3 h-3" />
                    {document.authority_level || 'MEDIUM'}
                  </span>
                  <span className="px-2 py-1 rounded-lg bg-trust-surface border border-trust-border text-gray-300">
                    {document.ingestion_status || 'READY'}
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
