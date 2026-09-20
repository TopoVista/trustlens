import React, { useEffect, useState } from 'react';
import { useAuth, useUser } from '@clerk/clerk-react';
import {
  Activity, AlertCircle, ArrowUpRight, Compass, FileText, GitBranch,
  HardDrive, Layers, ShieldCheck, Sliders, Sparkles
} from 'lucide-react';
import KnowledgeHeader from './components/KnowledgeHeader.jsx';
import QueryConsole from './components/QueryConsole.jsx';
import SpecialistCanvas from './components/SpecialistCanvas.jsx';
import AnswerContractPanel from './components/AnswerContractPanel.jsx';
import HealthAuditDashboard from './components/HealthAuditDashboard.jsx';
import KnowledgeGraphTimeline from './components/KnowledgeGraphTimeline.jsx';
import KnowledgeMap from './components/KnowledgeMap.jsx';
import DocumentLibrary from './components/DocumentLibrary.jsx';
import SemanticRulesManager from './components/SemanticRulesManager.jsx';
import IngestionModal from './components/IngestionModal.jsx';
import ArchitectureModal from './components/ArchitectureModal.jsx';
import Footer from './components/Footer.jsx';
import GuideChat from './components/guide/GuideChat.jsx';
import {
  addWorkspaceRule, checkHealth, createWorkspace, getUserStorageInfo,
  getWorkspaceDiscoveries, getWorkspaceDocuments, getWorkspaceEntities,
  getWorkspaceGraph, getWorkspaceHealth, getWorkspaceRules, getWorkspaceTimeline, listWorkspaces,
  queryKnowledgeStream, setAuthContext, uploadDocument
} from './api.js';

const VIEWS = [
  { id: 'query', label: 'Verify an answer', icon: Sparkles },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'health', label: 'Evidence health', icon: ShieldCheck },
  { id: 'graph', label: 'Knowledge map', icon: GitBranch },
  { id: 'rules', label: 'Verification rules', icon: Sliders }
];

const VIEW_PATHS = {
  query: '/',
  documents: '/documents',
  health: '/health',
  graph: '/map',
  rules: '/rules'
};

function viewFromLocation() {
  if (typeof window === 'undefined') return 'query';
  const entry = Object.entries(VIEW_PATHS).find(([, path]) => path === window.location.pathname);
  return entry?.[0] || 'query';
}

function AppContent({ isClerkConfigured = false, clerkUser = null, getToken = null, isAuthReady = true }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  const [discoveries, setDiscoveries] = useState([]);
  const [entitiesData, setEntitiesData] = useState(null);
  const [timelineData, setTimelineData] = useState([]);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], stats: {} });
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState(false);
  const [graphFocusNodeId, setGraphFocusNodeId] = useState(null);
  const [rules, setRules] = useState([]);
  const [workspaceDocuments, setWorkspaceDocuments] = useState([]);
  const [activeView, setActiveView] = useState(viewFromLocation);
  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isArchitectureOpen, setIsArchitectureOpen] = useState(false);
  const [isHealthy, setIsHealthy] = useState(true);
  const [isQuerying, setIsQuerying] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [queryResult, setQueryResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    const syncView = () => setActiveView(viewFromLocation());
    window.addEventListener('popstate', syncView);
    return () => window.removeEventListener('popstate', syncView);
  }, []);

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
      setGraphLoading(true);
      const [health, discoveryResult, entities, timeline, workspaceRules, documents, graph] = await Promise.all([
        getWorkspaceHealth(workspaceId).catch(() => null),
        getWorkspaceDiscoveries(workspaceId).catch(() => ({ discoveries: [] })),
        getWorkspaceEntities(workspaceId).catch(() => null),
        getWorkspaceTimeline(workspaceId).catch(() => []),
        getWorkspaceRules(workspaceId).catch(() => []),
        getWorkspaceDocuments(workspaceId).catch(() => []),
        getWorkspaceGraph(workspaceId).catch(() => null)
      ]);
      setHealthData(health);
      setDiscoveries(discoveryResult?.discoveries || []);
      setEntitiesData(entities);
      setTimelineData(timeline || []);
      setRules(workspaceRules || []);
      setWorkspaceDocuments(documents || []);
      setGraphData(graph || { nodes: [], edges: [], stats: {} });
      setGraphError(!graph);
      refreshStorageStats();
    } catch (err) {
      console.error('Error refreshing workspace data:', err);
      setGraphError(true);
    } finally {
      setGraphLoading(false);
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

  const navigateView = (view) => {
    if (!VIEW_PATHS[view]) return;
    if (window.location.pathname !== VIEW_PATHS[view]) {
      window.history.pushState({}, '', VIEW_PATHS[view]);
    }
    setActiveView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRunQuery = async (queryText) => {
    if (!activeWorkspace?.id || isQuerying) return;
    setErrorMessage(null);
    setIsQuerying(true);
    setPipelineStatus('Preparing the verification path.');
    try {
      const result = await queryKnowledgeStream(
        activeWorkspace.id,
        queryText,
        setPipelineStatus
      );
      setQueryResult(result);
      navigateView('query');
    } catch (err) {
      console.error('Knowledge query failed:', err);
      setErrorMessage(err.message || 'Execution error during multi-agent analysis.');
    } finally {
      setIsQuerying(false);
      setPipelineStatus(null);
    }
  };

  const handleAskGraphNode = (node) => {
    if (!node?.label) return;
    handleRunQuery(`Show the evidence and verification context for: ${node.label}`);
  };

  const handleFocusGraphClaim = (claim) => {
    const label = claim?.claim_text || claim?.statement || claim?.claim;
    const normalized = (label || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
    const match = graphData.nodes.find((node) => node.type === 'CLAIM' && ((node.label || '').toLowerCase() === (label || '').toLowerCase() || (node.label || '').toLowerCase().includes(normalized)));
    if (match) {
      setGraphFocusNodeId(match.id);
      navigateView('graph');
    }
  };

  const handleGuideAction = (action) => {
    if (action === 'openIngest') setIsIngestOpen(true);
    if (action === 'navigateQuery') navigateView('query');
    if (action === 'navigateDocuments') navigateView('documents');
    if (action === 'navigateGraph') navigateView('graph');
    if (action === 'navigateHealth') navigateView('health');
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
        activeView={activeView}
        onNavigate={navigateView}
      />

      <main className="flex-1 pb-14">
        <div className="tl-shell">
          {activeView === 'query' && (
            <section className="tl-hero">
              <div className="tl-hero-copy">
                <div className="editorial-kicker flex items-center gap-2 tl-status"><ShieldCheck className="h-3.5 w-3.5" />Private evidence workspace</div>
                <h1 className="tl-hero-title">Answers you can <em>trace</em> to the record.</h1>
                <p className="tl-hero-description">Bring in your working documents, ask a precise question, and review the evidence that supports—or limits—the answer.</p>
                <div className="mt-7 flex flex-wrap gap-3">
                  <button data-guide-id="add-source" onClick={() => setIsIngestOpen(true)} className="tl-primary inline-flex items-center gap-2 px-4 py-2.5 text-xs font-bold">Add source material <ArrowUpRight className="h-4 w-4" /></button>
                  <button onClick={() => setIsArchitectureOpen(true)} className="tl-secondary inline-flex items-center gap-2 px-4 py-2.5 text-xs font-bold">How it works <Compass className="h-4 w-4 tl-status" /></button>
                </div>
              </div>
              <div className="tl-assurance text-xs">
                <div><p className="editorial-kicker tl-status">01 · private</p><p className="mt-2 font-semibold">One workspace, one evidence record.</p></div>
                <div><p className="editorial-kicker tl-status">02 · linked</p><p className="mt-2 font-semibold">Claims stay beside their source passages.</p></div>
                <div><p className="editorial-kicker tl-status">03 · candid</p><p className="mt-2 font-semibold">Uncertainty is part of the answer.</p></div>
              </div>
            </section>
          )}

          {errorMessage && <div className="mt-5 flex items-start gap-3 rounded-[18px] border border-trust-red/25 bg-trust-red-bg px-4 py-3 text-xs text-[#7c302b]"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /><div><span className="font-bold">Action needed.</span> {errorMessage}</div></div>}

          <section key={activeView} className="tl-page">
            <div className="tl-workspace-bar">
              <div>
                <div className="editorial-kicker tl-status">{activeView === 'query' ? 'Evidence desk' : 'Workspace'}</div>
                <h2 className="mt-2 text-2xl font-semibold tracking-[-.055em] text-[#28251f]">{activeView === 'query' ? activeWorkspace?.name || 'Preparing your workspace' : VIEWS.find((view) => view.id === activeView)?.label}</h2>
                <p className="mt-1 text-xs text-trust-muted">{activeView === 'query' ? 'Ask the record and inspect the result without leaving the evidence.' : activeWorkspace?.name || 'Your evidence workspace'}</p>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px] font-mono">
                <span className="tl-pill inline-flex items-center gap-1.5 px-3 py-1.5"><FileText className="h-3 w-3 tl-status" />{workspaceDocuments.length} sources</span>
                <span className="tl-pill inline-flex items-center gap-1.5 px-3 py-1.5"><HardDrive className="h-3 w-3 tl-status" />{storageStats?.durable ? 'durable' : 'workspace'} storage</span>
              </div>
            </div>
            <nav aria-label="Workspace pages" className="tl-tab-row border-y border-[var(--tl-line-300)]">
              {VIEWS.map(({ id, label, icon: Icon }) => <button key={id} data-guide-id={`nav-${id}`} onClick={() => navigateView(id)} className={`tl-tab ${activeView === id ? 'is-active' : ''}`}><Icon className="h-3.5 w-3.5" />{label}{id === 'documents' ? ` (${workspaceDocuments.length})` : ''}</button>)}
            </nav>
            <div className="mt-4 tl-panel overflow-hidden">
              {activeView === 'query' && <><QueryConsole onRunQuery={handleRunQuery} isLoading={isQuerying} progressMessage={pipelineStatus} activeWorkspace={activeWorkspace} /><SpecialistCanvas isExecuting={isQuerying} activePlanTrace={queryResult?.plan_trace || []} intent={queryResult?.intent} latencyMs={queryResult?.latency_ms} /><AnswerContractPanel data={queryResult} onFocusGraph={handleFocusGraphClaim} /></>}
              {activeView === 'documents' && <DocumentLibrary documents={workspaceDocuments} activeWorkspace={activeWorkspace} />}
              {activeView === 'health' && <HealthAuditDashboard healthData={healthData} discoveries={discoveries} activeWorkspace={activeWorkspace} />}
              {activeView === 'graph' && <KnowledgeMap workspace={activeWorkspace} graph={graphData} graphLoading={graphLoading} graphError={graphError} timelineData={timelineData} entitiesData={entitiesData} focusNodeId={graphFocusNodeId} onFocusHandled={() => setGraphFocusNodeId(null)} onAskNode={handleAskGraphNode} />}
              {activeView === 'rules' && <SemanticRulesManager rules={rules} onAddRule={handleAddRule} activeWorkspace={activeWorkspace} />}
            </div>
          </section>
        </div>
      </main>

      <IngestionModal isOpen={isIngestOpen} onClose={() => setIsIngestOpen(false)} onIngest={handleIngestDocument} activeWorkspace={activeWorkspace} />
      <ArchitectureModal isOpen={isArchitectureOpen} onClose={() => setIsArchitectureOpen(false)} />
      <Footer />
      <GuideChat context={{ view: activeView, documents: workspaceDocuments.length, hasGraph: graphData.nodes.length > 0 }} onAction={handleGuideAction} />
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
