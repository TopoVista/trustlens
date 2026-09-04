import React, { useState } from 'react';
import { 
  GitBranch, 
  CalendarClock, 
  Layers, 
  Tag, 
  Building, 
  User, 
  Cpu, 
  ExternalLink,
  ChevronRight
} from 'lucide-react';

export default function KnowledgeGraphTimeline({
  entitiesData = null,
  timelineData = []
}) {
  const [activeTab, setActiveTab] = useState('timeline'); // 'timeline' | 'entities'

  const nodes = entitiesData?.nodes || [];
  const edges = entitiesData?.edges || [];

  return (
    <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 my-6 space-y-6">
      <div className="p-6 rounded-2xl bg-trust-card border border-trust-border/80 shadow-2xl">
        {/* Navigation Tabs */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-trust-border/60">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-2 ${
                activeTab === 'timeline'
                  ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                  : 'bg-trust-surface text-gray-400 hover:text-white'
              }`}
            >
              <CalendarClock className="w-3.5 h-3.5" />
              <span>Chronological Timeline ({timelineData.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('entities')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-2 ${
                activeTab === 'entities'
                  ? 'bg-trust-accent text-white shadow-md shadow-trust-accent/20'
                  : 'bg-trust-surface text-gray-400 hover:text-white'
              }`}
            >
              <GitBranch className="w-3.5 h-3.5" />
              <span>Extracted Knowledge Graph ({nodes.length} Nodes)</span>
            </button>
          </div>
        </div>

        {/* 1. TIMELINE VIEW */}
        {activeTab === 'timeline' && (
          <div className="space-y-4">
            {timelineData.length === 0 ? (
              <p className="text-xs text-trust-muted font-mono py-8 text-center">
                No chronological events detected yet. Ingest documents with dates or milestones.
              </p>
            ) : (
              <div className="relative pl-6 border-l-2 border-trust-accent/40 space-y-6">
                {timelineData.map((evt, idx) => (
                  <div key={idx} className="relative group">
                    {/* Timeline Pin */}
                    <div className="absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full bg-trust-card border-2 border-trust-accent group-hover:bg-trust-accent transition-colors" />

                    <div className="p-4 rounded-xl bg-trust-surface/80 border border-trust-border/70 hover:border-trust-accent/40 transition-colors space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-trust-cyan bg-trust-cyan/10 px-2.5 py-0.5 rounded border border-trust-cyan/30">
                          {evt.temporal_anchor || evt.date_str || 'Milestone'}
                        </span>
                        {evt.source_document && (
                          <span className="text-[11px] font-mono text-trust-muted">
                            {evt.source_document}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-200 leading-relaxed font-sans pt-1">
                        {evt.event_description || evt.summary || evt.statement}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 2. ENTITIES KNOWLEDGE GRAPH */}
        {activeTab === 'entities' && (
          <div className="space-y-4">
            {nodes.length === 0 ? (
              <p className="text-xs text-trust-muted font-mono py-8 text-center">
                No entities recognized yet. Ingest knowledge to build your personal knowledge graph.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {nodes.map((node, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-trust-surface/80 border border-trust-border/70 flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-2.5">
                      <div className="p-2 rounded-lg bg-trust-accent/20 text-trust-accent border border-trust-accent/30">
                        <Tag className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-white leading-tight">
                          {node.name || node.id}
                        </h4>
                        <span className="text-[10px] font-mono text-trust-muted">
                          {node.type || 'CONCEPT'}
                        </span>
                      </div>
                    </div>
                    {node.occurrences && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-trust-card border border-trust-border text-gray-300">
                        {node.occurrences}x
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
