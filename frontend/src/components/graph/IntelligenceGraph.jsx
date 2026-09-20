import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, LoaderCircle, Maximize2, Network, Route, ShieldAlert } from 'lucide-react';
import { getWorkspaceGraphNode, getWorkspaceGraphPath } from '../../api.js';
import { curateGraph, filterGraph } from '../../graph/filters.js';
import GraphCanvas from './GraphCanvas.jsx';
import GraphToolbar from './GraphToolbar.jsx';
import NodeDetailDrawer from './NodeDetailDrawer.jsx';
import EdgeDetailDrawer from './EdgeDetailDrawer.jsx';
import ReasoningPathPanel from './ReasoningPathPanel.jsx';

const DEFAULT_FILTERS = {
  types: ['CLAIM', 'ENTITY', 'VARIABLE', 'VALUE', 'EVENT', 'DOCUMENT', 'EVIDENCE', 'DATASET'],
  relations: ['SUPPORTED_BY', 'CONTRADICTS', 'DEPENDS_ON', 'MENTIONS', 'PRECEDES', 'CORRELATED_WITH', 'HAS_VALUE'],
  minConfidence: 0.5,
  status: 'ALL',
};

export default function IntelligenceGraph({ workspace, graph, loading, error, focusNodeId, onFocusHandled, onAskNode }) {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [focusedNodeId, setFocusedNodeId] = useState(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState(null);
  const [nodeDetail, setNodeDetail] = useState(null);
  const [pathStart, setPathStart] = useState(null);
  const [path, setPath] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (!focusNodeId) return;
    setSelectedNodeId(focusNodeId);
    setFocusedNodeId(focusNodeId);
    onFocusHandled?.();
  }, [focusNodeId, onFocusHandled]);

  const filtered = useMemo(() => filterGraph(graph, filters), [graph, filters]);
  const displayed = useMemo(() => curateGraph(filtered, {
    maxNodes: showAll ? Number.MAX_SAFE_INTEGER : 52,
    focusNodeId: selectedNodeId || focusedNodeId,
  }), [filtered, showAll, selectedNodeId, focusedNodeId]);
  const selectedNode = graph.nodes.find((node) => node.id === selectedNodeId) || null;
  const selectedEdge = graph.edges.find((edge) => edge.id === selectedEdgeId) || null;

  const selectNode = useCallback(async (nodeId) => {
    setSelectedNodeId(nodeId);
    setFocusedNodeId(nodeId);
    setSelectedEdgeId(null);
    setDetailLoading(true);
    try {
      setNodeDetail(await getWorkspaceGraphNode(workspace.id, nodeId));
    } catch {
      setNodeDetail(null);
    } finally {
      setDetailLoading(false);
    }
    if (pathStart && pathStart !== nodeId) {
      try {
        setPath(await getWorkspaceGraphPath(workspace.id, pathStart, nodeId));
      } catch {
        setPath({ hops: [], explanation: 'The reasoning path could not be loaded.' });
      }
      setPathStart(null);
    }
  }, [workspace?.id, pathStart]);

  const selectEdge = useCallback((edgeId) => {
    setSelectedEdgeId(edgeId);
    setSelectedNodeId(null);
  }, []);
  const hoverNode = useCallback(() => {}, []);
  const focus = useCallback((nodeId = selectedNodeId) => {
    if (nodeId) setFocusedNodeId(nodeId);
  }, [selectedNodeId]);
  const findPath = useCallback(() => {
    if (selectedNodeId) setPathStart(selectedNodeId);
  }, [selectedNodeId]);
  const showEvidence = useCallback(() => {
    setFilters({ ...filters, types: ['CLAIM', 'EVIDENCE', 'DOCUMENT'], relations: ['SUPPORTED_BY', 'CONTRADICTS'], minConfidence: 0 });
    setShowAll(false);
  }, [filters]);

  if (loading) return <div className="tl-graph-state"><LoaderCircle className="h-5 w-5 animate-spin" />Building evidence map…</div>;
  if (error) return <div className="tl-graph-state is-error"><AlertTriangle className="h-5 w-5" /><div><strong>Knowledge map unavailable.</strong><p>Your documents and evidence remain safe. Refresh the workspace to retry.</p></div></div>;
  if (!graph.nodes.length) return <div className="tl-graph-state"><Network className="h-6 w-6" /><div><strong>No relationships yet.</strong><p>Add sources containing claims, entities, dates, or structured values and TrustLens will build an evidence-backed relationship map.</p></div></div>;

  return (
    <section className="tl-intelligence-graph">
      <div className="tl-graph-head">
        <div>
          <p className="editorial-kicker tl-status">Knowledge map</p>
          <h3>See how evidence, claims, and facts connect.</h3>
          <p>{graph.stats?.claims || 0} claims · {graph.stats?.nodes || 0} nodes · {graph.stats?.edges || 0} evidence-backed relations · {graph.stats?.contradictions || 0} conflicts</p>
        </div>
        <div className="tl-graph-mode-actions">
          <button className={filters.relations.includes('CONTRADICTS') && filters.types.length <= 4 ? 'is-active' : ''} onClick={() => { setFilters({ ...filters, types: ['CLAIM', 'EVIDENCE', 'EVENT', 'DOCUMENT'], relations: ['CONTRADICTS', 'SUPPORTED_BY', 'PRECEDES'], minConfidence: 0.5 }); setShowAll(false); }}><ShieldAlert className="h-3.5 w-3.5" />Contradictions</button>
          <button className={showAll ? 'is-active' : ''} onClick={() => setShowAll((value) => !value)}>{showAll ? 'Curated view' : `Show all (${filtered.nodes.length})`}</button>
          <button onClick={() => { setFilters(DEFAULT_FILTERS); setFocusedNodeId(null); setShowAll(false); }}><Maximize2 className="h-3.5 w-3.5" />Reset view</button>
        </div>
      </div>
      <GraphToolbar graph={filtered} filters={filters} onChange={setFilters} onPickNode={selectNode} />
      <div className="tl-graph-overview-note">{displayed.curated ? <>Showing {displayed.nodes.length} high-signal nodes; {displayed.hiddenNodes} lower-signal nodes remain searchable.</> : <>Showing the complete filtered evidence record.</>}</div>
      <div className="tl-graph-stage">
        <GraphCanvas nodes={displayed.nodes} edges={displayed.edges} selectedNodeId={selectedNodeId} focusedNodeId={focusedNodeId} onSelectNode={selectNode} onSelectEdge={selectEdge} onHoverNode={hoverNode} />
        {pathStart && <div className="tl-path-select">Path start selected. Choose another node to explain the connection.<button onClick={() => setPathStart(null)}>Cancel</button></div>}
        {detailLoading && <div className="tl-graph-detail-loading"><LoaderCircle className="h-4 w-4 animate-spin" />Loading node intelligence…</div>}
        <NodeDetailDrawer node={selectedNode} detail={nodeDetail} onClose={() => { setSelectedNodeId(null); setNodeDetail(null); }} onFocus={() => focus()} onShowEvidence={showEvidence} onStartPath={findPath} onAsk={() => onAskNode?.(selectedNode)} />
        <EdgeDetailDrawer edge={selectedEdge} nodes={graph.nodes} onClose={() => setSelectedEdgeId(null)} />
        <ReasoningPathPanel path={path} onClose={() => setPath(null)} />
      </div>
      <div className="tl-graph-legend"><span><i className="claim" />Claims</span><span><i className="entity" />Entities</span><span><i className="variable" />Variables</span><span><i className="event" />Events</span><span><i className="evidence" />Evidence</span><span><i className="contradiction" />Contradiction edge</span>{pathStart && <span className="tl-status"><Route className="h-3 w-3" />Select a destination node</span>}</div>
    </section>
  );
}
