import React, { useEffect, useState } from 'react';
import { useAuth, useUser } from '@clerk/clerk-react';
import {
  Activity, AlertCircle, ArrowUpRight, Compass, FileText, GitBranch,
  HardDrive, Layers, ShieldCheck, Sliders, Sparkles
} from 'lucide-react';
import heroArtwork from './assets/trustlens-verification-hero.png';
import KnowledgeHeader from './components/KnowledgeHeader.jsx';
import QueryConsole from './components/QueryConsole.jsx';
import SpecialistCanvas from './components/SpecialistCanvas.jsx';
import AnswerContractPanel from './components/AnswerContractPanel.jsx';
import HealthAuditDashboard from './components/HealthAuditDashboard.jsx';
import KnowledgeGraphTimeline from './components/KnowledgeGraphTimeline.jsx';
import DocumentLibrary from './components/DocumentLibrary.jsx';
import SemanticRulesManager from './components/SemanticRulesManager.jsx';
import IngestionModal from './components/IngestionModal.jsx';
import ArchitectureModal from './components/ArchitectureModal.jsx';
import Footer from './components/Footer.jsx';
import {
  addWorkspaceRule, checkHealth, createWorkspace, getUserStorageInfo,
  getWorkspaceDiscoveries, getWorkspaceDocuments, getWorkspaceEntities,
  getWorkspaceHealth, getWorkspaceRules, getWorkspaceTimeline, listWorkspaces,
  queryKnowledge, setAuthContext, uploadDocument
} from './api.js';

const VIEWS = [
  { id: 'query', label: 'Verify an answer', icon: Sparkles },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'health', label: 'Evidence health', icon: ShieldCheck },
  { id: 'graph', label: 'Knowledge map', icon: GitBranch },
  { id: 'rules', label: 'Verification rules', icon: Sliders }
];

function AppContent({ isClerkConfigured = false, clerkUser = null, getToken = null, isAuthReady = true }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  const [discoveries, setDiscoveries] = useState([]);
  const [entitiesData, setEntitiesData] = useState(null);
  const [timelineData, setTimelineData] = useState([]);
  const [rules, setRules] = useState([]);
  const [workspaceDocuments, setWorkspaceDocuments] = useState([]);
  const [activeView, setActiveView] = useState('query');
  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isArchitectureOpen, setIsArchitectureOpen] = useState(false);
  const [isHealthy, setIsHealthy] = useState(true);
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    if (isClerkConfigured && !isAuthReady) return undefined;
    if (isClerkConfigured && !clerkUser?.id) {
      setWorkspaces([]);
      setActiveWorkspace(null);
      setWorkspaceDocuments([]);
      setStorageStats(null);
      return undefined;
    }

    let cancelled = false;
    const isCurrent = () => !cancelled;
    setAuthContext(clerkUser?.id || 'default_user', getToken);
    checkHealth().then((ok) => isCurrent() && setIsHealthy(ok));
    refreshStorageStats(isCurrent);
    loadWorkspaces(isCurrent);
    return () => { cancelled = true; };
  }, [clerkUser?.id, isClerkConfigured, isAuthReady]);

  const refreshStorageStats = async (isCurrent = () => true) => {
    try {
      const stats = await getUserStorageInfo();
      if (isCurrent()) setStorageStats(stats);
    } catch (err) {
      console.error('Failed to load user storage stats:', err);
    }
  };

  const loadWorkspaces = async (isCurrent = () => true) => {
    try {
      const list = await listWorkspaces();
      if (!isCurrent()) return;
      setWorkspaces(list);
      setActiveWorkspace(list[0] || null);
    } catch (err) {
      console.error('Failed to load workspaces:', err);
      if (isCurrent()) {
        setErrorMessage(`Unable to connect to the TrustLens backend. The production server may be starting; please retry in a moment. (${err.message})`);
      }
    }
  };

  useEffect(() => {
    if (activeWorkspace?.id) refreshWorkspaceData(activeWorkspace.id);
  }, [activeWorkspace?.id]);

  const refreshWorkspaceData = async (workspaceId) => {
    try {
      const [health, discoveryResult, entities, timeline, workspaceRules, documents] = await Promise.all([
        getWorkspaceHealth(workspaceId).catch(() => null),
        getWorkspaceDiscoveries(workspaceId).catch(() => ({ discoveries: [] })),
        getWorkspaceEntities(workspaceId).catch(() => null),
        getWorkspaceTimeline(workspaceId).catch(() => []),
        getWorkspaceRules(workspaceId).catch(() => []),
        getWorkspaceDocuments(workspaceId).catch(() => [])
      ]);
      setHealthData(health);
      setDiscoveries(discoveryResult?.discoveries || []);
      setEntitiesData(entities);
      setTimelineData(timeline || []);
      setRules(workspaceRules || []);
      setWorkspaceDocuments(documents || []);
      refreshStorageStats();
    } catch (err) {
      console.error('Error refreshing workspace data:', err);
    }
  };

  const handleCreateWorkspace = async (name, description) => {
    try {
      const workspace = await createWorkspace(name, description);
      setWorkspaces((current) => [...current, workspace]);
      setActiveWorkspace(workspace);
      refreshStorageStats();
    } catch (err) {
      console.error('Failed to create workspace:', err);
      setErrorMessage(`Could not create the workspace: ${err.message}`);
    }
  };

  const handleIngestDocument = async (document) => {
    if (!activeWorkspace?.id) return;
    setErrorMessage(null);
    try {
      const result = await uploadDocument(activeWorkspace.id, document);
      await refreshWorkspaceData(activeWorkspace.id);
      return result;
    } catch (err) {
      console.error('Ingestion failed:', err);
      const hint = /failed to fetch|networkerror/i.test(err.message) ? ' The backend may be waking up; retry shortly.' : '';
      setErrorMessage(`Document ingestion failed: ${err.message}.${hint}`);
      throw err;
    }
  };

  const handleAddRule = async (rule) => {
    if (!activeWorkspace?.id) return;
    const result = await addWorkspaceRule(activeWorkspace.id, rule);
    await refreshWorkspaceData(activeWorkspace.id);
    return result;
  };

  const handleRunQuery = async (queryText) => {
    if (!activeWorkspace?.id || isQuerying) return;
    setErrorMessage(null);
    setIsQuerying(true);
    try {
      const result = await queryKnowledge(activeWorkspace.id, queryText);
      setQueryResult(result);
      setActiveView('query');
    } catch (err) {
      console.error('Knowledge query failed:', err);
      setErrorMessage(err.message || 'Execution error during multi-agent analysis.');
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="app-shell flex flex-col bg-trust-bg selection:bg-trust-accent/30 selection:text-white">
      <KnowledgeHeader
        workspaces={workspaces}
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={setActiveWorkspace}
        onCreateWorkspace={handleCreateWorkspace}
        onOpenIngest={() => setIsIngestOpen(true)}
        healthData={healthData}
        storageStats={storageStats}
        isHealthy={isHealthy}
        isClerkConfigured={isClerkConfigured}
        onRefresh={() => {
          if (activeWorkspace) refreshWorkspaceData(activeWorkspace.id);
          refreshStorageStats();
        }}
      />

      <main className="flex-1 px-3 pb-14 sm:px-6">
        <section className="product-hero">
          <img className="hero-art" src={heroArtwork} alt="Abstract glass documents connected by an evidence orbit" />
          <div className="hero-content flex min-h-[510px] flex-col justify-center px-6 py-12 sm:px-12 lg:px-16">
            <div className="hero-eyebrow editorial-kicker w-fit">
              <ShieldCheck className="h-3.5 w-3.5 text-trust-cyan" />
              Private evidence workspace
            </div>
            <h1 className="hero-title mt-6 text-white">
              Answers you can <em>trace</em> back to your documents.
            </h1>
            <p className="mt-6 max-w-xl text-sm leading-7 text-[#b9bbcf] sm:text-base">
              Bring your notes, reports, and working files together. TrustLens extracts the signal, tests claims against evidence, and makes uncertainty visible.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <button onClick={() => setIsIngestOpen(true)} className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-xs font-extrabold text-[#101122] shadow-xl transition hover:-translate-y-0.5 hover:bg-[#e8e4ff]">
                Add source material <ArrowUpRight className="h-4 w-4" />
              </button>
              <button onClick={() => setIsArchitectureOpen(true)} className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[.045] px-5 py-3 text-xs font-bold text-white transition hover:bg-white/[.09]">
                How verification works <Compass className="h-4 w-4 text-trust-cyan" />
              </button>
            </div>
            <div className="mt-10 flex flex-wrap gap-x-7 gap-y-3 text-[11px] font-mono text-[#aeb1c8]">
              <span className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-trust-green shadow-[0_0_12px_#61d9a8]" />workspace-isolated</span>
              <span className="flex items-center gap-2"><Layers className="h-3.5 w-3.5 text-trust-cyan" />evidence linked</span>
              <span className="flex items-center gap-2"><Activity className="h-3.5 w-3.5 text-[#c7b7ff]" />uncertainty surfaced</span>
            </div>
          </div>
          <div className="hero-orbit text-[11px] font-mono text-[#c4c6d7]">
            <span className="text-[#f1efff]">Evidence network</span>
            <p className="mt-2 leading-5 text-[#9295ad]">Sources, claims, and their provenance stay connected in one reviewable workspace.</p>
          </div>
        </section>

        {errorMessage && (
          <div className="mx-auto max-w-[1210px] pt-5">
            <div className="flex items-start gap-3 rounded-2xl border border-trust-red/35 bg-trust-red-bg px-4 py-3 text-xs text-[#ffb1b7]">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <div><span className="font-bold text-white">Action needed.</span> {errorMessage}</div>
            </div>
          </div>
        )}

        <section className="workspace-stage mt-8">
          <div className="workspace-intro px-5 pt-5 sm:px-7 sm:pt-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="editorial-kicker text-[#9598b2]">Your evidence desk</div>
                <h2 className="mt-2 text-xl font-bold tracking-[-.04em] text-white sm:text-2xl">
                  {activeWorkspace?.name || 'Preparing your workspace'}
                </h2>
                <p className="mt-1 text-xs text-trust-muted">Ask a question, inspect the evidence, or add material to strengthen the record.</p>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px] font-mono">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[.035] px-3 py-1.5 text-[#bfc1d1]"><FileText className="h-3 w-3 text-trust-cyan" />{workspaceDocuments.length} sources</span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[.035] px-3 py-1.5 text-[#bfc1d1]"><HardDrive className="h-3 w-3 text-[#c7b7ff]" />{storageStats?.durable ? 'durable storage' : 'workspace storage'}</span>
              </div>
            </div>
            <div className="workspace-nav mt-6">
              {VIEWS.map(({ id, label, icon: Icon }) => (
                <button key={id} onClick={() => setActiveView(id)} className={`workspace-tab ${activeView === id ? 'is-active' : ''}`}>
                  <Icon className="h-3.5 w-3.5" /> {label}{id === 'documents' ? ` (${workspaceDocuments.length})` : ''}
                </button>
              ))}
            </div>
          </div>

          {activeView === 'query' && (
            <>
              <QueryConsole onRunQuery={handleRunQuery} isLoading={isQuerying} activeWorkspace={activeWorkspace} />
              <SpecialistCanvas isExecuting={isQuerying} activePlanTrace={queryResult?.plan_trace || []} intent={queryResult?.intent} latencyMs={queryResult?.latency_ms} />
              <AnswerContractPanel data={queryResult} />
            </>
          )}
          {activeView === 'documents' && <DocumentLibrary documents={workspaceDocuments} activeWorkspace={activeWorkspace} />}
          {activeView === 'health' && <HealthAuditDashboard healthData={healthData} discoveries={discoveries} activeWorkspace={activeWorkspace} />}
          {activeView === 'graph' && <KnowledgeGraphTimeline entitiesData={entitiesData} timelineData={timelineData} />}
          {activeView === 'rules' && <SemanticRulesManager rules={rules} onAddRule={handleAddRule} activeWorkspace={activeWorkspace} />}
        </section>
      </main>

      <IngestionModal isOpen={isIngestOpen} onClose={() => setIsIngestOpen(false)} onIngest={handleIngestDocument} activeWorkspace={activeWorkspace} />
      <ArchitectureModal isOpen={isArchitectureOpen} onClose={() => setIsArchitectureOpen(false)} />
      <Footer />
    </div>
  );
}

function ClerkAppWrapper() {
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  return <AppContent isClerkConfigured clerkUser={user} getToken={getToken} isAuthReady={isLoaded} />;
}

function StandaloneAppWrapper() {
  return <AppContent />;
}

export default function App({ isClerkConfigured = false }) {
  return isClerkConfigured ? <ClerkAppWrapper /> : <StandaloneAppWrapper />;
}
