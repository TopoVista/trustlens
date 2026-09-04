import React, { useState, useEffect } from 'react';
import Header from './components/Header.jsx';
import Hero from './components/Hero.jsx';
import QueryInput from './components/QueryInput.jsx';
import WorkflowPipeline from './components/WorkflowPipeline.jsx';
import LoadingWorkflow from './components/LoadingWorkflow.jsx';
import ResultsPanel from './components/ResultsPanel.jsx';
import ArchitectureModal from './components/ArchitectureModal.jsx';
import Footer from './components/Footer.jsx';
import { analyzeQuery, checkHealth } from './api.js';
import { AlertCircle } from 'lucide-react';

export default function App() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isColdStarting, setIsColdStarting] = useState(false);
  const [activeStage, setActiveStage] = useState('idle');
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState(null);
  const [isArchitectureOpen, setIsArchitectureOpen] = useState(false);
  const [isHealthy, setIsHealthy] = useState(true);

  // Check health on initial load
  useEffect(() => {
    checkHealth().then((ok) => setIsHealthy(ok));
  }, []);

  const handleAnalyze = async () => {
    if (!query.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);
    setResultData(null);
    setIsColdStarting(false);
    setActiveStage('query');

    // Stage simulation timer to animate pipeline visually while awaiting API response
    const stageSequence = ['embed', 'retrieve', 'generate', 'claims', 'nli'];
    let stageIndex = 0;
    const interval = setInterval(() => {
      if (stageIndex < stageSequence.length) {
        setActiveStage(stageSequence[stageIndex]);
        stageIndex++;
      }
    }, 1200);

    // Cold-start detection timer (if backend is on a free Render tier waking up)
    const coldStartTimer = setTimeout(() => {
      setIsColdStarting(true);
    }, 3000);

    try {
      // Single request to backend /analyze endpoint (runs retrieval, generation, verification once)
      const data = await analyzeQuery(query.trim());
      clearTimeout(coldStartTimer);
      clearInterval(interval);
      setActiveStage('result');
      setResultData(data);
    } catch (err) {
      clearTimeout(coldStartTimer);
      clearInterval(interval);
      setActiveStage('idle');
      console.error('Analysis error:', err);
      setError(err.message || 'Unable to complete verification analysis. Please ensure the backend server is running.');
    } finally {
      setIsLoading(false);
      setIsColdStarting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-trust-bg selection:bg-trust-accent/30 selection:text-white">
      {/* 1. Header */}
      <Header
        onOpenArchitecture={() => setIsArchitectureOpen(true)}
        isHealthy={isHealthy}
      />

      <main className="flex-1 pb-16">
        {/* 2. Hero Section */}
        <Hero />

        {/* 3. Query Input */}
        <QueryInput
          query={query}
          setQuery={setQuery}
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
        />

        {/* Error notification banner */}
        {error && (
          <div className="max-w-3xl mx-auto px-4 mt-6">
            <div className="p-4 rounded-xl bg-trust-red-bg border border-trust-red/40 flex items-start space-x-3 text-trust-red text-xs sm:text-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block">Analysis Error</span>
                <p className="text-trust-red/90 mt-0.5">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* 4. Animated Workflow Pipeline */}
        <WorkflowPipeline
          activeStage={activeStage}
          stats={resultData?.stats}
          isRunning={isLoading}
          hasResult={Boolean(resultData)}
        />

        {/* 5. Loading State */}
        {isLoading && <LoadingWorkflow isColdStarting={isColdStarting} />}

        {/* 6. Verification Results */}
        {!isLoading && resultData && <ResultsPanel data={resultData} />}
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
