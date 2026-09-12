import React, { useState } from 'react';
import {
  ChevronDown, FolderPlus, LoaderCircle, Plus, RefreshCw, ShieldCheck,
  Sparkles, Upload
} from 'lucide-react';
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react';

export default function KnowledgeHeader({
  workspaces = [], activeWorkspace, onSelectWorkspace, onCreateWorkspace,
  onOpenIngest, storageStats, isHealthy = true, isClerkConfigured = false, onRefresh
}) {
  const [showWorkspaceMenu, setShowWorkspaceMenu] = useState(false);
  const [showNewWorkspace, setShowNewWorkspace] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);

  const submitWorkspace = async (event) => {
    event.preventDefault();
    if (!name.trim() || saving) return;
    setSaving(true);
    try {
      await onCreateWorkspace(name.trim(), description.trim());
      setName('');
      setDescription('');
      setShowNewWorkspace(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 border-b border-white/[.075] bg-[#090a16]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-[72px] max-w-[1440px] items-center justify-between gap-3 px-4 sm:px-6">
        <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="group flex shrink-0 items-center gap-2.5 text-left">
          <span className="relative grid h-9 w-9 place-items-center rounded-xl border border-[#aa94ff]/45 bg-gradient-to-br from-[#9a79ff] to-[#6040c9] shadow-[0_10px_30px_rgba(113,77,230,.28)]">
            <ShieldCheck className="h-[18px] w-[18px] text-white" />
            <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 border-[#090a16] bg-trust-cyan" />
          </span>
          <span>
            <span className="block text-[15px] font-extrabold tracking-[-.055em] text-white">TrustLens</span>
            <span className="editorial-kicker mt-1 block text-[8px] text-[#9699b1]">evidence intelligence</span>
          </span>
        </button>

        <div className="hidden min-w-0 flex-1 justify-center md:flex">
          <div className="relative">
            <button onClick={() => setShowWorkspaceMenu((open) => !open)} className="flex max-w-[340px] items-center gap-2 rounded-full border border-white/[.09] bg-white/[.035] px-4 py-2 text-xs text-[#ced0df] transition hover:border-[#aa94ff]/45 hover:bg-white/[.065]">
              <span className="h-1.5 w-1.5 rounded-full bg-trust-green" />
              <span className="truncate font-semibold">{activeWorkspace?.name || 'Choose a workspace'}</span>
              <ChevronDown className="h-3.5 w-3.5 shrink-0 text-[#878aa4]" />
            </button>
            {showWorkspaceMenu && (
              <div className="absolute left-1/2 top-[calc(100%+10px)] z-50 w-[330px] -translate-x-1/2 overflow-hidden rounded-2xl border border-white/10 bg-[#17192d] p-2 shadow-2xl shadow-black/40">
                <div className="px-3 py-2 editorial-kicker text-[#9699b1]">Your workspaces</div>
                <div className="max-h-56 overflow-y-auto">
                  {workspaces.map((workspace) => (
                    <button key={workspace.id} onClick={() => { onSelectWorkspace(workspace); setShowWorkspaceMenu(false); }} className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-xs transition ${activeWorkspace?.id === workspace.id ? 'bg-[#8d6cff]/18 text-white' : 'text-[#c4c6d5] hover:bg-white/[.055]'}`}>
                      <span className="truncate font-semibold">{workspace.name}</span>
                      {activeWorkspace?.id === workspace.id && <span className="text-[10px] text-[#c6b7ff]">Active</span>}
                    </button>
                  ))}
                </div>
                <button onClick={() => { setShowWorkspaceMenu(false); setShowNewWorkspace(true); }} className="mt-2 flex w-full items-center gap-2 rounded-xl border border-dashed border-white/15 px-3 py-2.5 text-xs font-bold text-[#d8d0ff] transition hover:border-[#ad95ff]/60 hover:bg-[#8d6cff]/10"><Plus className="h-3.5 w-3.5" /> New workspace</button>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <span className="hidden items-center gap-1.5 text-[10px] font-mono text-[#a9abc0] lg:flex">
            <span className={`h-1.5 w-1.5 rounded-full ${isHealthy ? 'bg-trust-green shadow-[0_0_10px_#61d9a8]' : 'bg-trust-red'}`} />
            {storageStats?.durable ? 'durable' : 'connected'}
          </span>
          <button onClick={onRefresh} title="Refresh workspace" className="grid h-8 w-8 place-items-center rounded-full text-[#a9abc0] transition hover:bg-white/[.07] hover:text-white"><RefreshCw className="h-3.5 w-3.5" /></button>
          <button onClick={onOpenIngest} className="inline-flex items-center gap-2 rounded-full bg-white px-3.5 py-2 text-[11px] font-extrabold text-[#101122] shadow-lg transition hover:-translate-y-0.5 hover:bg-[#e9e5ff] sm:px-4"><Upload className="h-3.5 w-3.5" /><span className="hidden sm:inline">Add documents</span><span className="sm:hidden">Add</span></button>
          {isClerkConfigured && <><SignedIn><UserButton appearance={{ elements: { avatarBox: 'h-8 w-8' } }} /></SignedIn><SignedOut><SignInButton mode="modal"><button className="hidden rounded-full border border-white/15 px-3 py-1.5 text-[11px] font-bold text-white sm:block">Sign in</button></SignInButton></SignedOut></>}
        </div>
      </div>

      {showNewWorkspace && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-[#050610]/75 p-4 backdrop-blur-sm">
          <form onSubmit={submitWorkspace} className="w-full max-w-md rounded-[22px] border border-white/10 bg-[#17192d] p-6 shadow-2xl">
            <div className="flex items-start gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#8d6cff]/15 text-[#bbaaff]"><FolderPlus className="h-5 w-5" /></span>
              <div><p className="text-base font-extrabold tracking-[-.035em] text-white">Create an evidence workspace</p><p className="mt-1 text-xs leading-5 text-[#a7a9bd]">Keep a distinct set of source documents, evidence, and verification rules together.</p></div>
            </div>
            <label className="mt-6 block text-[10px] font-mono uppercase tracking-[.12em] text-[#a5a7bc]">Workspace name</label>
            <input autoFocus required value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Product research" className="mt-2 w-full rounded-xl border border-white/10 bg-[#0d0e1d] px-3 py-2.5 text-sm text-white outline-none placeholder:text-[#696c82] focus:border-[#a589ff]" />
            <label className="mt-4 block text-[10px] font-mono uppercase tracking-[.12em] text-[#a5a7bc]">Purpose <span className="normal-case tracking-normal text-[#70738a]">(optional)</span></label>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} placeholder="What should this workspace help you verify?" className="mt-2 w-full resize-none rounded-xl border border-white/10 bg-[#0d0e1d] px-3 py-2.5 text-sm text-white outline-none placeholder:text-[#696c82] focus:border-[#a589ff]" />
            <div className="mt-6 flex justify-end gap-2"><button type="button" onClick={() => setShowNewWorkspace(false)} className="rounded-full px-4 py-2 text-xs font-bold text-[#b5b7c8] transition hover:text-white">Cancel</button><button disabled={saving} className="inline-flex items-center gap-2 rounded-full bg-[#8d6cff] px-4 py-2 text-xs font-extrabold text-white disabled:opacity-60">{saving && <LoaderCircle className="h-3.5 w-3.5 animate-spin" />}Create workspace</button></div>
          </form>
        </div>
      )}
    </header>
  );
}
