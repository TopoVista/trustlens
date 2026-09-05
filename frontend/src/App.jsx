import React, { useState, useEffect } from 'react';
import { useUser, useAuth } from '@clerk/clerk-react';
import KnowledgeHeader from './components/KnowledgeHeader.jsx';
import QueryConsole from './components/QueryConsole.jsx';
import SpecialistCanvas from './components/SpecialistCanvas.jsx';
import AnswerContractPanel from './components/AnswerContractPanel.jsx';
import HealthAuditDashboard from './components/HealthAuditDashboard.jsx';
import KnowledgeGraphTimeline from './components/KnowledgeGraphTimeline.jsx';
import SemanticRulesManager from './components/SemanticRulesManager.jsx';
import IngestionModal from './components/IngestionModal.jsx';
import ArchitectureModal from './components/ArchitectureModal.jsx';
import Footer from './components/Footer.jsx';
import {
  setAuthContext,
  getUserStorageInfo,
  listWorkspaces,
  createWorkspace,
  getWorkspaceHealth,
  getWorkspaceDiscoveries,
  uploadDocument,
  getWorkspaceEntities,
  getWorkspaceTimeline,
  getWorkspaceRules,
  addWorkspaceRule,
  queryKnowledge,
  checkHealth
} from './api.js';
import { 
  Sparkles, 
  ShieldCheck, 
  GitBranch, 
  Sliders, 
  AlertCircle, 
  Layers, 
  Activity,
  Compass,
  HardDrive
} from 'lucide-react';

function AppContent({ isClerkConfigured = false, clerkUser = null, getToken = null }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  const [discoveries, setDiscoveries] = useState([]);
  const [entitiesData, setEntitiesData] = useState(null);
  const [timelineData, setTimelineData] = useState([]);
  const [rules, setRules] = useState([]);

  const [activeView, setActiveView] = useState('query'); // 'query' | 'health' | 'graph' | 'rules'
  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isArchitectureOpen, setIsArchitectureOpen] = useState(false);
  const [isHealthy, setIsHealthy] = useState(true);

  const [isQuerying, setIsQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Sync auth context whenever user changes
  useEffect(() => {
    const userId = clerkUser?.id || 'default_user';
    setAuthContext(userId, getToken);
    
    // Refresh storage stats and workspaces for this user
    checkHealth().then((ok) => setIsHealthy(ok));
    refreshStorageStats();
    loadWorkspaces();
  }, [clerkUser?.id]);

  const refreshStorageStats = async () => {
    try {
      const stats = await getUserStorageInfo();
      setStorageStats(stats);
    } catch (err) {
      console.error('Failed to load user storage stats:', err);
    }
  };

  const loadWorkspaces = async () => {
    try {
      const list = await listWorkspaces();
      setWorkspaces(list);
      if (list.length > 0) {
        setActiveWorkspace(list[0]);
      } else {
        setActiveWorkspace(null);
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
      setErrorMessage(
        'Unable to connect to the TrustLens backend. ' +
        'The production server may be deploying an update — please refresh in a minute. ' +
        `(${err.message})`
      );
    }
  };

  // When active workspace changes, reload its context
  useEffect(() => {
    if (!activeWorkspace?.id) return;
    refreshWorkspaceData(activeWorkspace.id);
  }, [activeWorkspace?.id]);

  const refreshWorkspaceData = async (wsId) => {
    try {
      const [h, d, e, t, r] = await Promise.all([
        getWorkspaceHealth(wsId).catch(() => null),
        getWorkspaceDiscoveries(wsId).catch(() => ({ discoveries: [] })),
        getWorkspaceEntities(wsId).catch(() => null),
        getWorkspaceTimeline(wsId).catch(() => []),
        getWorkspaceRules(wsId).catch(() => []),
      ]);

      setHealthData(h);
      setDiscoveries(d?.discoveries || []);
      setEntitiesData(e);
      setTimelineData(t || []);
      setRules(r || []);
      refreshStorageStats();
    } catch (err) {
      console.error('Error refreshing workspace data:', err);
    }
  };

  const handleCreateWorkspace = async (name, description) => {
    try {
      const newWs = await createWorkspace(name, description);
      setWorkspaces((prev) => [...prev, newWs]);
      setActiveWorkspace(newWs);
      refreshStorageStats();
    } catch (err) {
      console.error('Failed to create workspace:', err);
    }
  };

  const handleIngestDocument = async (docData) => {
    if (!activeWorkspace?.id) return;
    setErrorMessage(null);
    try {
      const res = await uploadDocument(activeWorkspace.id, docData);
      await refreshWorkspaceData(activeWorkspace.id);
      await refreshStorageStats();
      return res;
    } catch (err) {
      console.error('Ingestion failed:', err);
      const hint = err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')
        ? ' The backend server may be unavailable — please try again in a moment.'
        : '';
      setErrorMessage(`Document ingestion failed: ${err.message}.${hint}`);
      throw err;
    }
  };

  const handleAddRule = async (ruleData) => {
    if (!activeWorkspace?.id) return;
    const res = await addWorkspaceRule(activeWorkspace.id, ruleData);
    await refreshWorkspaceData(activeWorkspace.id);
    return res;
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
    <div className="min-h-screen flex flex-col bg-trust-bg selection:bg-trust-accent/30 selection:text-white">
      {/* 1. Header with Workspace Management, Clerk Auth & Storage Indicator */}
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

      <main className="flex-1 pb-16">
        {/* Error Notification */}
        {errorMessage && (
          <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-4">
            <div className="p-3.5 rounded-xl bg-trust-red-bg border border-trust-red/40 text-xs text-trust-red flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">Analysis Error</span>
                <span className="text-trust-red/90">{errorMessage}</span>
              </div>
            </div>
          </div>
        )}

        {/* 2. Hero & Query Console */}
        <div className="pt-8 pb-4 text-center px-4 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-trust-accent/15 border border-trust-accent/30 text-trust-accent text-xs font-mono mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Intent-Aware Personal Knowledge Intelligence</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Evidence-Grounded Intelligence Over Your Data
          </h1>
          <p className="text-xs sm:text-sm text-trust-muted mt-2 max-w-xl mx-auto">
            Each user's knowledge is strictly isolated in dedicated SQLite databases on their local hard disk.
            Decompose assertions, ground claims against evidence, and discover cross-document contradictions.
          </p>

          {storageStats && (
            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-xl bg-trust-card border border-trust-border text-[11px] font-mono text-gray-300">
              <HardDrive className="w-3.5 h-3.5 text-trust-cyan" />
              <span>Host Partition:</span>
              <span className="text-trust-cyan font-bold">{storageStats.storage_path}</span>
            </div>
          )}
        </div>

        {/* 3. Query Bar */}
        <QueryConsole
          onRunQuery={handleRunQuery}
          isLoading={isQuerying}
          activeWorkspace={activeWorkspace}
        />

        {/* 4. Specialist Multi-Agent Canvas */}
        <SpecialistCanvas
          isExecuting={isQuerying}
          activePlanTrace={queryResult?.plan_trace || []}
          intent={queryResult?.intent}
          latencyMs={queryResult?.latency_ms}
        />

        {/* 5. View Navigation Bar */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 my-6">
          <div className="flex items-center justify-between border-b border-trust-border/60 pb-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveView('query')}
                className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-2 ${
                  activeView === 'query'
                    ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                    : 'bg-trust-surface text-gray-400 hover:text-white'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Grounded Q&A & Claims</span>
              </button>

              <button
                onClick={() => setActiveView('health')}
                className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-2 ${
                  activeView === 'health'
                    ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                    : 'bg-trust-surface text-gray-400 hover:text-white'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Health & Blind Spot Audit</span>
              </button>

              <button
                onClick={() => setActiveView('graph')}
                className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-2 ${
                  activeView === 'graph'
                    ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                    : 'bg-trust-surface text-gray-400 hover:text-white'
                }`}
              >
                <GitBranch className="w-3.5 h-3.5" />
                <span>Graph & Timeline Explorer</span>
              </button>

              <button
                onClick={() => setActiveView('rules')}
                className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-2 ${
                  activeView === 'rules'
                    ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                    : 'bg-trust-surface text-gray-400 hover:text-white'
                }`}
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>Semantic Memory Rules</span>
              </button>
            </div>

            <button
              onClick={() => setIsArchitectureOpen(true)}
              className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-trust-muted hover:text-trust-accent transition-colors"
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Architecture Spec</span>
            </button>
          </div>
        </div>

        {/* 6. Active View Container */}
        {activeView === 'query' && (
          <AnswerContractPanel data={queryResult} />
        )}

        {activeView === 'health' && (
          <HealthAuditDashboard
            healthData={healthData}
            discoveries={discoveries}
            activeWorkspace={activeWorkspace}
          />
        )}

        {activeView === 'graph' && (
          <KnowledgeGraphTimeline
            entitiesData={entitiesData}
            timelineData={timelineData}
          />
        )}

        {activeView === 'rules' && (
          <SemanticRulesManager
            rules={rules}
            onAddRule={handleAddRule}
            activeWorkspace={activeWorkspace}
          />
        )}
      </main>

      {/* 7. Knowledge Ingestion Modal */}
      <IngestionModal
        isOpen={isIngestOpen}
        onClose={() => setIsIngestOpen(false)}
        onIngest={handleIngestDocument}
        activeWorkspace={activeWorkspace}
      />

      {/* 8. Architecture Spec Modal */}
      <ArchitectureModal
        isOpen={isArchitectureOpen}
        onClose={() => setIsArchitectureOpen(false)}
      />

      {/* 9. Footer */}
      <Footer />
    </div>
  );
}

function ClerkAppWrapper() {
  const { user } = useUser();
  const { getToken } = useAuth();
  return <AppContent isClerkConfigured={true} clerkUser={user} getToken={getToken} />;
}

function StandaloneAppWrapper() {
  return <AppContent isClerkConfigured={false} clerkUser={null} getToken={null} />;
}

export default function App({ isClerkConfigured = false }) {
  return isClerkConfigured ? <ClerkAppWrapper /> : <StandaloneAppWrapper />;
}
