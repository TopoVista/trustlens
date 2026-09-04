import React, { useState, useEffect } from 'react';
import Header from './components/Header.jsx';
import Hero from './components/Hero.jsx';
import VendorSelector from './components/VendorSelector.jsx';
import WorkflowPipeline from './components/WorkflowPipeline.jsx';
import LoadingWorkflow from './components/LoadingWorkflow.jsx';
import VendorRiskCard from './components/VendorRiskCard.jsx';
import ComplianceMatrix from './components/ComplianceMatrix.jsx';
import AgentProvenanceDrawer from './components/AgentProvenanceDrawer.jsx';
import InteractiveQABot from './components/InteractiveQABot.jsx';
import ResultsPanel from './components/ResultsPanel.jsx';
import ArchitectureModal from './components/ArchitectureModal.jsx';
import Footer from './components/Footer.jsx';
import { assessVendor, checkHealth } from './api.js';
import { AlertCircle, Shield, Sparkles, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [selectedVendor, setSelectedVendor] = useState({ id: 'snowflake', name: 'Snowflake Data Cloud', domain: 'snowflake.com' });
  const [isLoading, setIsLoading] = useState(false);
  const [isColdStarting, setIsColdStarting] = useState(false);
  const [activeStage, setActiveStage] = useState('idle');
  const [assessmentData, setAssessmentData] = useState(null);
  const [error, setError] = useState(null);
  const [isArchitectureOpen, setIsArchitectureOpen] = useState(false);
  const [isHealthy, setIsHealthy] = useState(true);
  const [activeTab, setActiveTab] = useState('assessment'); // 'assessment' | 'qa_claims'

  // Check health on load
  useEffect(() => {
    checkHealth().then((ok) => setIsHealthy(ok));
  }, []);

  const handleAssessVendor = async () => {
    if (!selectedVendor || isLoading) return;

    setError(null);
    setIsLoading(true);
    setAssessmentData(null);
    setIsColdStarting(false);
    setActiveStage('ingestion');

    // Multi-agent stage simulation timer to animate UI pipeline
    const stages = ['parsing', 'retrieval', 'compliance', 'scoring', 'report', 'qa_verifier'];
    let stageIdx = 0;
    const interval = setInterval(() => {
      if (stageIdx < stages.length) {
        setActiveStage(stages[stageIdx]);
        stageIdx++;
      }
    }, 1200);

    const coldStartTimer = setTimeout(() => {
      setIsColdStarting(true);
    }, 3000);

    try {
      const payload = {
        vendor: selectedVendor,
        query: `Comprehensive security and compliance audit for ${selectedVendor.name}`,
        documents_text: selectedVendor.documents_text || ''
      };

      const data = await assessVendor(payload);
      clearTimeout(coldStartTimer);
      clearInterval(interval);
      setActiveStage('qa_verifier');
      setAssessmentData(data);
    } catch (err) {
      clearTimeout(coldStartTimer);
      clearInterval(interval);
      setActiveStage('idle');
      console.error('Multi-Agent assessment error:', err);
      setError(err.message || 'Unable to complete multi-agent assessment. Ensure backend is running.');
    } finally {
      setIsLoading(false);
      setIsColdStarting(false);
    }
  };

  // Convert multi-agent QA claims into format expected by ResultsPanel for deep-dive
  const formattedResultsData = assessmentData ? {
    query: `Security assessment for ${assessmentData.vendor_profile?.name}`,
    answer: assessmentData.report_narrative,
    documents: assessmentData.evidence_documents || [],
    verified_claims: assessmentData.qa_verification?.verified_claims || [],
    stats: {
      claim_count: assessmentData.qa_verification?.verified_claims?.length || 0,
      faithfulness: (assessmentData.qa_verification?.faithfulness || 100) / 100,
      hallucination_rate: (assessmentData.qa_verification?.hallucination_rate || 0) / 100,
      supported: assessmentData.qa_verification?.verified_claims?.filter(c => c.label === 'SUPPORTED').length || 0,
      not_supported: assessmentData.qa_verification?.verified_claims?.filter(c => c.label === 'NOT_SUPPORTED').length || 0,
      contradicted: assessmentData.qa_verification?.verified_claims?.filter(c => c.label === 'CONTRADICTED').length || 0,
      total_ms: assessmentData.total_latency_ms
    }
  } : null;

  return (
    <div className="min-h-screen flex flex-col bg-trust-bg selection:bg-trust-accent/30 selection:text-white">
      {/* 1. Navigation Header */}
      <Header
        onOpenArchitecture={() => setIsArchitectureOpen(true)}
        isHealthy={isHealthy}
      />

      <main className="flex-1 pb-16">
        {/* 2. Hero Section */}
        <Hero />

        {/* 3. Vendor Assessment Selector */}
        <VendorSelector
          selectedVendor={selectedVendor}
          onSelectVendor={setSelectedVendor}
          onAssess={handleAssessVendor}
          isLoading={isLoading}
        />

        {/* Error notification banner */}
        {error && (
          <div className="max-w-3xl mx-auto px-4 mb-6">
            <div className="p-4 rounded-xl bg-trust-red-bg border border-trust-red/40 flex items-start space-x-3 text-trust-red text-xs sm:text-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block">Multi-Agent Assessment Error</span>
                <p className="text-trust-red/90 mt-0.5">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* 4. Multi-Agent Autonomous Collaboration Canvas */}
        <WorkflowPipeline
          activeStage={activeStage}
          isRunning={isLoading}
          hasResult={Boolean(assessmentData)}
        />

        {/* 5. Loading State */}
        {isLoading && <LoadingWorkflow isColdStarting={isColdStarting} />}

        {/* 6. Multi-Agent Assessment Results Dashboard */}
        {!isLoading && assessmentData && (
          <div className="max-w-6xl mx-auto px-4">
            {/* View Selector Tabs */}
            <div className="flex items-center justify-between mb-6 pb-2 border-b border-trust-border/40">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab('assessment')}
                  className={`text-xs font-mono px-4 py-2 rounded-xl transition-all flex items-center gap-2 ${
                    activeTab === 'assessment'
                      ? 'bg-trust-accent text-white font-semibold shadow-md shadow-trust-accent/20'
                      : 'bg-trust-surface/60 text-gray-400 hover:text-white'
                  }`}
                >
                  <Shield className="w-3.5 h-3.5" />
                  <span>Executive Risk & Compliance Matrix</span>
                </button>

                <button
                  onClick={() => setActiveTab('qa_claims')}
                  className={`text-xs font-mono px-4 py-2 rounded-xl transition-all flex items-center gap-2 ${
                    activeTab === 'qa_claims'
                      ? 'bg-trust-accent text-white font-semibold shadow-md shadow-trust-accent/20'
                      : 'bg-trust-surface/60 text-gray-400 hover:text-white'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>QA NLI Claim Grounding Deep-Dive</span>
                </button>
              </div>

              <span className="text-[11px] font-mono text-gray-400">
                Audited Vendor: <strong className="text-white">{assessmentData.vendor_profile?.name}</strong>
              </span>
            </div>

            {activeTab === 'assessment' ? (
              <>
                {/* Executive Vendor Risk Card */}
                <VendorRiskCard assessment={assessmentData} />

                {/* Compliance Framework Matrix */}
                <ComplianceMatrix
                  complianceFindings={assessmentData.compliance_findings}
                  complianceRate={assessmentData.compliance_rate}
                />

                {/* Agent Provenance & Execution Trace Drawer */}
                <AgentProvenanceDrawer
                  agentTraces={assessmentData.agent_traces}
                  qaOverview={assessmentData.qa_verification}
                  totalLatencyMs={assessmentData.total_latency_ms}
                />

                {/* Interactive User Q&A Bot */}
                <InteractiveQABot vendorProfile={assessmentData.vendor_profile} />
              </>
            ) : (
              /* QA Claim-Level Grounding Deep Dive */
              <ResultsPanel data={formattedResultsData} />
            )}
          </div>
        )}
      </main>

      {/* 7. Footer */}
      <Footer />

      {/* Architecture Explainer Modal */}
      <ArchitectureModal
        isOpen={isArchitectureOpen}
        onClose={() => setIsArchitectureOpen(false)}
      />
    </div>
  );
}
