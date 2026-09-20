import React, { useState } from 'react';
import { CalendarClock, GitBranch } from 'lucide-react';
import IntelligenceGraph from './graph/IntelligenceGraph.jsx';
import KnowledgeGraphTimeline from './KnowledgeGraphTimeline.jsx';

export default function KnowledgeMap({ workspace, graph, graphLoading, graphError, timelineData, entitiesData, focusNodeId, onFocusHandled, onAskNode }) {
  const [view, setView] = useState('graph');
  return <section className="tl-knowledge-map"><div className="tl-map-switch"><button className={view === 'graph' ? 'is-active' : ''} onClick={() => setView('graph')}><GitBranch className="h-3.5 w-3.5" />Intelligence graph</button><button className={view === 'timeline' ? 'is-active' : ''} onClick={() => setView('timeline')}><CalendarClock className="h-3.5 w-3.5" />Timeline</button></div>{view === 'graph' ? <IntelligenceGraph workspace={workspace} graph={graph} loading={graphLoading} error={graphError} focusNodeId={focusNodeId} onFocusHandled={onFocusHandled} onAskNode={onAskNode} /> : <KnowledgeGraphTimeline entitiesData={entitiesData} timelineData={timelineData} />}</section>;
}
