import React, { useState } from 'react';
import { ChevronDown, FolderPlus, LoaderCircle, Plus, RefreshCw, ShieldCheck, Upload } from 'lucide-react';
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react';

const PRIMARY_PAGES = [
  ['query', 'Verify'],
  ['documents', 'Documents'],
  ['health', 'Health']
];

export default function KnowledgeHeader({
  workspaces = [], activeWorkspace, onSelectWorkspace, onCreateWorkspace,
  onOpenIngest, storageStats, isHealthy = true, isClerkConfigured = false, onRefresh,
  activeView = 'query', onNavigate = () => {}
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
    <header className="tl-header">
      <div className="tl-shell flex h-16 items-center justify-between gap-3">
        <button onClick={() => onNavigate('query')} className="flex shrink-0 items-center gap-2.5 text-left" aria-label="Go to TrustLens evidence desk">
          <span className="tl-brand-mark"><ShieldCheck className="h-[18px] w-[18px]" /></span>
          <span><span className="block text-[15px] font-extrabold tracking-[-.055em] text-[#28251f]">TrustLens</span><span className="editorial-kicker mt-0.5 block text-[8px] text-[#6d665d]">Evidence intelligence</span></span>
        </button>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
          {PRIMARY_PAGES.map(([id, label]) => <button key={id} onClick={() => onNavigate(id)} className={`tl-nav-link ${activeView === id ? 'is-active' : ''}`}>{label}</button>)}
        </nav>

        <div className="flex min-w-0 items-center justify-end gap-1.5 sm:gap-2">
          <div className="relative hidden md:block">
            <button onClick={() => setShowWorkspaceMenu((open) => !open)} className="tl-pill flex max-w-[240px] items-center gap-2 px-3 py-1.5 text-xs">
              <span className="h-1.5 w-1.5 rounded-full bg-trust-green" />
              <span className="truncate font-semibold">{activeWorkspace?.name || 'Choose workspace'}</span>
              <ChevronDown className="h-3.5 w-3.5 shrink-0" />
            </button>
            {showWorkspaceMenu && <div className="absolute right-0 top-[calc(100%+9px)] z-50 w-[310px] overflow-hidden rounded-[16px] border border-[var(--tl-line-300)] bg-[var(--tl-paper-100)] p-2 shadow-[0_14px_30px_rgba(59,47,32,.12)]"><div className="px-3 py-2 editorial-kicker text-[#6d665d]">Your workspaces</div><div className="max-h-56 overflow-y-auto">{workspaces.map((workspace) => <button key={workspace.id} onClick={() => { onSelectWorkspace(workspace); setShowWorkspaceMenu(false); }} className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-xs ${activeWorkspace?.id === workspace.id ? 'bg-[var(--tl-paper-200)] text-[#28251f]' : 'text-[#6d665d] hover:bg-[var(--tl-paper-200)]'}`}><span className="truncate font-semibold">{workspace.name}</span>{activeWorkspace?.id === workspace.id && <span className="text-[10px] tl-status">Active</span>}</button>)}</div><button onClick={() => { setShowWorkspaceMenu(false); setShowNewWorkspace(true); }} className="mt-2 flex w-full items-center gap-2 rounded-xl border border-dashed border-[var(--tl-line-300)] px-3 py-2.5 text-xs font-bold text-[#6d665d] hover:bg-[var(--tl-paper-200)]"><Plus className="h-3.5 w-3.5" />New workspace</button></div>}
          </div>
          <span className="hidden items-center gap-1.5 px-2 text-[10px] font-mono text-[#6d665d] xl:flex"><span className={`h-1.5 w-1.5 rounded-full ${isHealthy ? 'bg-trust-green' : 'bg-trust-red'}`} />{storageStats?.durable ? 'durable' : 'connected'}</span>
          <button onClick={onRefresh} title="Refresh workspace" className="grid h-8 w-8 place-items-center rounded-full text-[#6d665d] hover:bg-[var(--tl-paper-200)] hover:text-[#28251f]"><RefreshCw className="h-3.5 w-3.5" /></button>
          <button onClick={onOpenIngest} className="tl-primary inline-flex items-center gap-2 px-3 py-2 text-[11px] font-bold"><Upload className="h-3.5 w-3.5" /><span className="hidden sm:inline">Add documents</span><span className="sm:hidden">Add</span></button>
          {isClerkConfigured && <><SignedIn><UserButton appearance={{ elements: { avatarBox: 'h-8 w-8' } }} /></SignedIn><SignedOut><SignInButton mode="modal"><button className="hidden rounded-full border border-[var(--tl-line-300)] px-3 py-1.5 text-[11px] font-bold text-[#28251f] sm:block">Sign in</button></SignInButton></SignedOut></>}
        </div>
      </div>

      {showNewWorkspace && <div className="fixed inset-0 z-50 grid place-items-center bg-[#28251f]/25 p-4 backdrop-blur-sm"><form onSubmit={submitWorkspace} className="w-full max-w-md rounded-[20px] border border-[var(--tl-line-300)] bg-[var(--tl-paper-100)] p-6 shadow-[0_22px_60px_rgba(59,47,32,.18)]"><div className="flex items-start gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--tl-paper-200)] tl-status"><FolderPlus className="h-5 w-5" /></span><div><p className="text-base font-extrabold tracking-[-.035em] text-[#28251f]">Create an evidence workspace</p><p className="mt-1 text-xs leading-5 text-[#6d665d]">Keep a distinct, reviewable evidence record for every project.</p></div></div><label className="mt-6 block text-[10px] font-mono uppercase tracking-[.12em] text-[#6d665d]">Workspace name</label><input autoFocus required value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Product research" className="mt-2 w-full rounded-xl border border-[var(--tl-line-300)] bg-[#fffdf9] px-3 py-2.5 text-sm text-[#28251f] outline-none focus:border-[#ad856f]" /><label className="mt-4 block text-[10px] font-mono uppercase tracking-[.12em] text-[#6d665d]">Purpose <span className="normal-case tracking-normal">(optional)</span></label><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} placeholder="What should this workspace help you verify?" className="mt-2 w-full resize-none rounded-xl border border-[var(--tl-line-300)] bg-[#fffdf9] px-3 py-2.5 text-sm text-[#28251f] outline-none focus:border-[#ad856f]" /><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={() => setShowNewWorkspace(false)} className="tl-secondary px-4 py-2 text-xs font-bold">Cancel</button><button disabled={saving} className="tl-primary inline-flex items-center gap-2 px-4 py-2 text-xs font-bold disabled:opacity-60">{saving && <LoaderCircle className="h-3.5 w-3.5 animate-spin" />}Create workspace</button></div></form></div>}
    </header>
  );
}
