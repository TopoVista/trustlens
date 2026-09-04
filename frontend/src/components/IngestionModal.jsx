import React, { useState } from 'react';
import { 
  X, 
  UploadCloud, 
  FileText, 
  Sparkles, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowRight, 
  Layers, 
  FileSpreadsheet,
  Zap
} from 'lucide-react';

const PRESET_PACKS = [
  {
    id: 'pack_q3_exec',
    title: 'Q3 Executive & Financial Review',
    authority: 'OFFICIAL',
    description: 'Corporate financial disclosure, engineering org updates, infrastructure cost optimizations, and SOC2 audit.',
    filename: 'q3_2024_executive_review.txt',
    content: `In Q3 2024, our revenue reached $12.5M, representing a 25% year-over-year increase. The engineering team expanded to 45 engineers led by VP of Engineering Alex Rivera. Cloud infrastructure costs decreased to $180K per month following full migration to AWS Graviton3 instances. The annual security compliance SOC2 Type II audit was successfully completed on August 15, 2024 with zero major non-conformities reported.`
  },
  {
    id: 'pack_product_roadmap',
    title: '2024-2025 Product Roadmap & Budget Update',
    authority: 'HIGH',
    description: 'Strategic roadmap update outlining feature launches, hiring goals, and revised launch schedules.',
    filename: 'product_strategy_roadmap_v2.txt',
    content: `Projected enterprise platform launch was initially scheduled for November 15, 2024 with an allocated launch budget of $5.0M. Following leadership review on September 1, 2024, the enterprise GA launch was rescheduled to March 10, 2025 to incorporate customer feedback, and the allocated launch budget was revised upwards to $7.2M. The engineering team plans to hire an additional 15 distributed systems engineers by end of Q4 2024.`
  },
  {
    id: 'pack_clinical_trial',
    title: 'Clinical Trial Comparison Study',
    authority: 'HIGH',
    description: 'Biomedical trial efficacy and dosage specifications across Phase II and Phase III cohorts.',
    filename: 'clinical_trial_summary.txt',
    content: `Phase II clinical evaluation of Compound TL-801 demonstrated an overall response rate of 68% when administered at 50mg daily dosage across 120 patients. Adverse gastrointestinal events occurred in 12% of participants. However, the subsequent Phase III trial observed an overall response rate of 54% at the same 50mg dosage, while reducing adverse events to 6% when co-administered with food.`
  }
];

export default function IngestionModal({
  isOpen,
  onClose,
  onIngest,
  activeWorkspace
}) {
  const [activeTab, setActiveTab] = useState('text'); // 'text' | 'presets' | 'file'
  const [title, setTitle] = useState('');
  const [rawContent, setRawContent] = useState('');
  const [authorityLevel, setAuthorityLevel] = useState('HIGH');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ingestionResult, setIngestionResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!title.trim() || !rawContent.trim() || isSubmitting) return;

    setError(null);
    setIsSubmitting(true);
    setIngestionResult(null);

    try {
      const result = await onIngest({
        title: title.trim(),
        filename: `${title.trim().toLowerCase().replace(/[^a-z0-9]/g, '_')}.txt`,
        raw_content: rawContent.trim(),
        file_type: 'text',
        authority_level: authorityLevel
      });
      setIngestionResult(result);
    } catch (err) {
      console.error('Ingestion failed:', err);
      setError(err.message || 'Failed to ingest knowledge into workspace.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApplyPreset = (pack) => {
    setTitle(pack.title);
    setRawContent(pack.content);
    setAuthorityLevel(pack.authority);
    setActiveTab('text');
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setTitle(file.name.replace(/\.[^/.]+$/, ''));
    const reader = new FileReader();
    reader.onload = (event) => {
      setRawContent(event.target.result || '');
      setActiveTab('text');
    };
    reader.readAsText(file);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in">
      <div className="w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl bg-trust-card border border-trust-border shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-trust-border/80 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-trust-accent/20 border border-trust-accent/40 text-trust-accent">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Ingest Knowledge Content</h2>
              <p className="text-xs text-trust-muted font-mono">
                Target Workspace: <span className="text-trust-cyan">{activeWorkspace?.name || 'Default'}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-trust-muted hover:text-white rounded-lg hover:bg-trust-surface transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="px-6 pt-3 flex gap-2 border-b border-trust-border/60 bg-trust-surface/40">
          <button
            onClick={() => setActiveTab('text')}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'text'
                ? 'border-trust-accent text-white font-semibold'
                : 'border-transparent text-trust-muted hover:text-gray-300'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Direct Text & Notes</span>
          </button>
          <button
            onClick={() => setActiveTab('presets')}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'presets'
                ? 'border-trust-accent text-white font-semibold'
                : 'border-transparent text-trust-muted hover:text-gray-300'
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-trust-amber" />
            <span>1-Click Sample Packs</span>
          </button>
          <button
            onClick={() => setActiveTab('file')}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'file'
                ? 'border-trust-accent text-white font-semibold'
                : 'border-transparent text-trust-muted hover:text-gray-300'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {error && (
            <div className="p-3 rounded-xl bg-trust-red-bg border border-trust-red/40 text-xs text-trust-red flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {ingestionResult && (
            <div className="p-4 rounded-xl bg-trust-green-bg border border-trust-green/40 text-xs text-trust-green space-y-2">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Knowledge Ingested Successfully!</span>
              </div>
              <p className="text-gray-300 font-mono text-[11px]">
                Processed into {ingestionResult.chunks_count || 1} semantic chunk(s) with atomic claim extraction,
                entity recognition, and temporal anchoring.
              </p>
              <div className="flex gap-3 pt-1 text-[11px] font-mono">
                <span className="bg-trust-card px-2 py-0.5 rounded border border-trust-green/30">
                  ID: {ingestionResult.id}
                </span>
                <span className="bg-trust-card px-2 py-0.5 rounded border border-trust-green/30">
                  Authority: {ingestionResult.authority_level}
                </span>
              </div>
            </div>
          )}

          {/* TAB 1: DIRECT TEXT FORM */}
          {activeTab === 'text' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-mono text-gray-300 mb-1">
                    Document / Note Title
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Q3 Financial Review, Strategy Memo"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl bg-trust-surface border border-trust-border text-white focus:outline-none focus:border-trust-accent"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-gray-300 mb-1">
                    Authority Level
                  </label>
                  <select
                    value={authorityLevel}
                    onChange={(e) => setAuthorityLevel(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl bg-trust-surface border border-trust-border text-white focus:outline-none focus:border-trust-accent"
                  >
                    <option value="OFFICIAL">OFFICIAL (Audited/Final)</option>
                    <option value="HIGH">HIGH (Authoritative)</option>
                    <option value="MEDIUM">MEDIUM (Internal Notes)</option>
                    <option value="UNVERIFIED">UNVERIFIED (Draft/Rumor)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1 flex justify-between">
                  <span>Knowledge Content (Markdown / Text)</span>
                  <span className="text-trust-muted">{rawContent.length} chars</span>
                </label>
                <textarea
                  required
                  rows={8}
                  placeholder="Paste research notes, audit conclusions, financial metrics, roadmap milestones, or specifications..."
                  value={rawContent}
                  onChange={(e) => setRawContent(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-trust-surface border border-trust-border text-white focus:outline-none focus:border-trust-accent font-mono leading-relaxed"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs text-gray-400 hover:text-white rounded-xl bg-trust-surface border border-trust-border"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !title.trim() || !rawContent.trim()}
                  className="px-5 py-2 text-xs font-semibold text-white rounded-xl bg-gradient-to-r from-trust-accent to-purple-600 hover:from-trust-accent-hover hover:to-purple-500 shadow-md shadow-trust-accent/30 disabled:opacity-50 flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <span className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                      <span>Extracting Claims & Entities...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Ingest & Decompose</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* TAB 2: PRESET PACKS */}
          {activeTab === 'presets' && (
            <div className="space-y-3">
              <p className="text-xs text-trust-muted">
                Select a ready-to-test knowledge dossier to immediately test multi-agent claim decomposition,
                contradiction hunting, and grounded Q&A.
              </p>
              <div className="grid gap-3">
                {PRESET_PACKS.map((pack) => (
                  <div
                    key={pack.id}
                    onClick={() => handleApplyPreset(pack)}
                    className="p-4 rounded-xl bg-trust-surface/70 border border-trust-border hover:border-trust-accent/60 cursor-pointer transition-all hover:bg-trust-surface group"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-white group-hover:text-trust-accent transition-colors">
                          {pack.title}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-trust-accent/20 border border-trust-accent/30 text-trust-accent">
                          {pack.authority}
                        </span>
                      </div>
                      <ArrowRight className="w-4 h-4 text-trust-muted group-hover:text-trust-accent group-hover:translate-x-0.5 transition-all" />
                    </div>
                    <p className="text-xs text-gray-400 mb-2">{pack.description}</p>
                    <div className="p-2 rounded bg-trust-card/80 border border-trust-border/40 text-[11px] font-mono text-gray-400 line-clamp-2">
                      {pack.content}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: FILE UPLOAD */}
          {activeTab === 'file' && (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-trust-border hover:border-trust-accent/60 rounded-2xl p-8 text-center transition-all bg-trust-surface/30">
                <UploadCloud className="w-10 h-10 text-trust-muted mx-auto mb-3" />
                <h4 className="text-sm font-semibold text-white mb-1">
                  Upload Knowledge Document
                </h4>
                <p className="text-xs text-trust-muted max-w-sm mx-auto mb-4">
                  Drag and drop or browse plain text (.txt), Markdown (.md), or CSV tables (.csv).
                </p>
                <label className="inline-block px-4 py-2 rounded-xl bg-trust-accent hover:bg-trust-accent-hover text-xs font-semibold text-white cursor-pointer shadow-md shadow-trust-accent/25">
                  Browse File
                  <input
                    type="file"
                    accept=".txt,.md,.csv,.json"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
