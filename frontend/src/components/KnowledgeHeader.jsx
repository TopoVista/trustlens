import React, { useState } from 'react';
import { 
  BrainCircuit, 
  Database, 
  PlusCircle, 
  ShieldCheck, 
  Sparkles, 
  FileText, 
  Sliders, 
  FolderPlus,
  RefreshCw,
  Layers,
  HardDrive,
  User,
  Key,
  LogIn
} from 'lucide-react';
import { 
  SignedIn, 
  SignedOut, 
  SignInButton, 
  UserButton, 
  useUser 
} from '@clerk/clerk-react';

export default function KnowledgeHeader({
  workspaces = [],
  activeWorkspace = null,
  onSelectWorkspace,
  onCreateWorkspace,
  onOpenIngest,
  healthData = null,
  storageStats = null,
  isHealthy = true,
  isClerkConfigured = false,
  onRefresh
}) {
  const [showNewWsModal, setShowNewWsModal] = useState(false);
  const [showStorageModal, setShowStorageModal] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [newWsDesc, setNewWsDesc] = useState('');

  let user = null;
  if (isClerkConfigured) {
    try {
      const clerk = useUser();
      user = clerk.user;
    } catch {}
  }

  const handleCreate = (e) => {
    e.preventDefault();
    if (!newWsName.trim()) return;
    onCreateWorkspace(newWsName.trim(), newWsDesc.trim());
    setNewWsName('');
    setNewWsDesc('');
    setShowNewWsModal(false);
  };

  return (
    <header className="sticky top-0 z-40 border-b border-trust-border/80 bg-trust-bg/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
        {/* Logo & Product Brand */}
        <div className="flex items-center space-x-3 shrink-0">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-trust-accent to-trust-cyan shadow-lg shadow-trust-accent/25">
            <BrainCircuit className="w-5 h-5 text-white" />
            <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-trust-green ring-2 ring-trust-bg" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-base sm:text-lg font-bold tracking-tight bg-gradient-to-r from-white via-gray-100 to-gray-400 bg-clip-text text-transparent">
                TrustLens
              </span>
              <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-trust-accent/20 border border-trust-accent/40 text-trust-accent">
                Knowledge
              </span>
            </div>
            <p className="text-[10px] text-trust-muted font-mono hidden md:block">
              Per-User Local Disk Isolation
            </p>
          </div>
        </div>

        {/* Center: Workspace Selector */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-trust-surface/90 border border-trust-border rounded-xl px-2.5 py-1.5 shadow-inner">
            <Database className="w-3.5 h-3.5 text-trust-cyan mr-2 shrink-0" />
            <select
              aria-label="Select Knowledge Workspace"
              value={activeWorkspace?.id || ''}
              onChange={(e) => {
                const found = workspaces.find((w) => w.id === e.target.value);
                if (found) onSelectWorkspace(found);
              }}
              className="bg-transparent text-xs text-white font-medium focus:outline-none cursor-pointer pr-4 max-w-[140px] sm:max-w-[200px] truncate"
            >
              {workspaces.map((ws) => (
                <option key={ws.id} value={ws.id} className="bg-trust-card text-white">
                  {ws.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setShowNewWsModal(true)}
            title="Create New Workspace"
            className="p-1.5 text-trust-muted hover:text-white rounded-lg bg-trust-surface border border-trust-border hover:border-trust-accent/50 transition-colors"
          >
            <FolderPlus className="w-4 h-4" />
          </button>
        </div>

        {/* Right Action Hub: Storage, Auth & Primary Actions */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          {/* Hard Disk Storage Badge */}
          <button
            onClick={() => setShowStorageModal(true)}
            title="Inspect Hard Disk Partition"
            className="flex items-center space-x-1.5 text-[11px] font-mono px-2.5 py-1.5 rounded-xl bg-trust-surface border border-trust-border hover:border-trust-accent/50 text-gray-300 hover:text-white transition-all shadow-sm"
          >
            <HardDrive className="w-3.5 h-3.5 text-trust-accent" />
            <span className="hidden lg:inline">Disk:</span>
            <span className="text-trust-cyan font-semibold">
              {storageStats ? `${storageStats.total_kb} KB` : 'Local'}
            </span>
          </button>

          {/* Quick Refresh */}
          <button
            onClick={onRefresh}
            title="Refresh Workspace State"
            className="p-2 text-trust-muted hover:text-white rounded-xl bg-trust-surface border border-trust-border hover:border-trust-border/80 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          {/* Primary Ingestion Trigger */}
          <button
            onClick={onOpenIngest}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-trust-accent to-purple-600 hover:from-trust-accent-hover hover:to-purple-500 text-white text-xs font-semibold shadow-md shadow-trust-accent/25 transition-all transform active:scale-95"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Ingest</span>
          </button>

          {/* Clerk Auth / User Badge */}
          <div className="border-l border-trust-border pl-2 sm:pl-3 flex items-center">
            {isClerkConfigured ? (
              <>
                <SignedIn>
                  <div className="flex items-center gap-2">
                    <UserButton
                      appearance={{
                        elements: {
                          avatarBox: "w-8 h-8 rounded-xl border border-trust-border"
                        }
                      }}
                      afterSignOutUrl="/"
                    />
                  </div>
                </SignedIn>
                <SignedOut>
                  <SignInButton mode="modal">
                    <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-trust-surface border border-trust-accent/40 hover:border-trust-accent text-xs font-semibold text-white transition-all">
                      <LogIn className="w-3.5 h-3.5 text-trust-accent" />
                      <span>Sign In</span>
                    </button>
                  </SignInButton>
                </SignedOut>
              </>
            ) : (
              <button
                onClick={() => setShowStorageModal(true)}
                title="Local Hard Disk Mode (Click to configure Clerk)"
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-trust-surface border border-trust-border hover:border-trust-accent/50 text-[11px] font-mono text-gray-300"
              >
                <User className="w-3.5 h-3.5 text-trust-cyan" />
                <span className="hidden sm:inline">Local User</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Hard Disk Storage Inspector Modal */}
      {showStorageModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg p-6 rounded-2xl bg-trust-card border border-trust-border shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-trust-border/80">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-trust-accent/20 border border-trust-accent/40 text-trust-accent">
                  <HardDrive className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Personal Hard Disk Storage
                  </h3>
                  <p className="text-xs text-trust-muted font-mono">
                    Strict multi-tenant disk isolation on host machine
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowStorageModal(false)}
                className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded bg-trust-surface"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 rounded-xl bg-trust-surface border border-trust-border space-y-1.5">
                <span className="text-[10px] text-trust-muted uppercase block">
                  Isolated Hard Disk Path
                </span>
                <span className="text-trust-cyan break-all text-[11px]">
                  {storageStats?.storage_path || 'backend/data/users/default_user'}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-3 rounded-xl bg-trust-surface border border-trust-border">
                  <span className="text-[10px] text-trust-muted block mb-0.5">Disk Usage</span>
                  <span className="text-sm font-bold text-white">
                    {storageStats ? `${storageStats.total_kb} KB` : '0 KB'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-trust-surface border border-trust-border">
                  <span className="text-[10px] text-trust-muted block mb-0.5">Database Size</span>
                  <span className="text-sm font-bold text-trust-green">
                    {storageStats ? `${Math.round(storageStats.db_bytes / 1024)} KB` : '0 KB'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-trust-surface border border-trust-border">
                  <span className="text-[10px] text-trust-muted block mb-0.5">Files Count</span>
                  <span className="text-sm font-bold text-trust-accent">
                    {storageStats?.files_count || 0}
                  </span>
                </div>
              </div>

              {!isClerkConfigured && (
                <div className="p-3.5 rounded-xl bg-trust-accent/10 border border-trust-accent/30 space-y-1.5 font-sans">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-white">
                    <Key className="w-3.5 h-3.5 text-trust-accent" />
                    <span>Enable Clerk Multi-User Authentication</span>
                  </div>
                  <p className="text-[11px] text-gray-300 leading-relaxed">
                    To connect to your Clerk account, add your publishable key to <code className="text-trust-cyan font-mono">frontend/.env</code>:
                  </p>
                  <pre className="p-2 rounded bg-trust-bg/80 text-[10px] font-mono text-trust-accent overflow-x-auto">
                    VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
                  </pre>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowStorageModal(false)}
                className="px-4 py-2 text-xs font-semibold text-white rounded-xl bg-trust-accent hover:bg-trust-accent-hover"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Workspace Modal */}
      {showNewWsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md p-6 rounded-2xl bg-trust-card border border-trust-border shadow-2xl">
            <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2">
              <FolderPlus className="w-5 h-5 text-trust-accent" />
              Create Knowledge Workspace
            </h3>
            <p className="text-xs text-trust-muted mb-4">
              Workspaces isolate documents, extracted claims, entity graphs, and verification policies.
            </p>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1">Workspace Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q4 Executive Strategy, Medical Dossier"
                  value={newWsName}
                  onChange={(e) => setNewWsName(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-trust-surface border border-trust-border text-white focus:outline-none focus:border-trust-accent"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1">Description (Optional)</label>
                <input
                  type="text"
                  placeholder="Scope or objectives of this knowledge base"
                  value={newWsDesc}
                  onChange={(e) => setNewWsDesc(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-trust-surface border border-trust-border text-white focus:outline-none focus:border-trust-accent"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowNewWsModal(false)}
                  className="px-3.5 py-1.5 text-xs text-gray-400 hover:text-white rounded-xl bg-trust-surface border border-trust-border"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-semibold text-white rounded-xl bg-trust-accent hover:bg-trust-accent-hover shadow-md shadow-trust-accent/30"
                >
                  Create Workspace
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
}
