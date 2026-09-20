import React, { useEffect, useRef } from 'react';
import Sigma from 'sigma';
import { MultiDirectedGraph } from 'graphology';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import { connectedComponents } from 'graphology-components';

const COLORS = {
  CLAIM: '#b56f52', ENTITY: '#4c695c', VARIABLE: '#7b6aa8', VALUE: '#a57b43',
  EVENT: '#587895', DOCUMENT: '#6d665d', EVIDENCE: '#b48762', DATASET: '#4f7f78'
};

const layoutPoint = (index, total) => {
  const angle = (index / Math.max(total, 1)) * Math.PI * 2;
  const radius = 4 + Math.sqrt(index + 1) * 1.65;
  return { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
};

export default function GraphCanvas({ nodes, edges, selectedNodeId, focusedNodeId, onSelectNode, onSelectEdge, onHoverNode }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return undefined;
    const graph = new MultiDirectedGraph();
    const nodeIds = new Set(nodes.map((node) => node.id));
    nodes.forEach((node, index) => {
      const position = layoutPoint(index, nodes.length);
      graph.addNode(node.id, {
        ...position,
        label: node.label.length > 54 ? `${node.label.slice(0, 51)}…` : node.label,
        size: Math.min(11, 4.5 + Math.sqrt((node.degree || 1)) * 1.2),
        color: COLORS[node.type] || '#6d665d',
        nodeType: node.type,
        status: node.status,
      });
    });
    edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)).forEach((edge) => {
      graph.addEdgeWithKey(edge.id, edge.source, edge.target, {
        color: edge.relation === 'CONTRADICTS' ? '#b95b50' : '#b8ac9c',
        size: Math.max(0.7, 0.65 + edge.confidence * 1.3),
        relation: edge.relation,
        confidence: edge.confidence,
      });
    });
    // ForceAtlas2 refines the deterministic seed only for manageable graphs;
    // the radial seed remains a low-latency fallback for very large workspaces.
    if (graph.order > 1 && graph.order <= 800 && graph.size > 0) {
      try { forceAtlas2.assign(graph, { iterations: 18, settings: { gravity: 1, scalingRatio: 8, slowDown: 1 } }); } catch {}
    }
    const componentCount = connectedComponents(graph).length;
    graph.forEachNode((node, attributes) => {
      graph.mergeNodeAttributes(node, { size: Math.min(11, attributes.size + Math.min(1.5, graph.degree(node) * 0.22)), componentCount });
    });
    const renderer = new Sigma(graph, containerRef.current, {
      renderEdgeLabels: false,
      labelDensity: 0.08,
      labelGridCellSize: 120,
      labelRenderedSizeThreshold: 7,
      defaultEdgeColor: '#c6bcae',
      defaultNodeColor: '#6d665d',
      zIndex: true,
    });
    rendererRef.current = renderer;

    const applyAppearance = (nodeId) => {
      const neighbors = nodeId && graph.hasNode(nodeId) ? new Set(graph.neighbors(nodeId)) : new Set();
      renderer.setSetting('nodeReducer', (id, data) => {
        const isFocus = !nodeId || id === nodeId || neighbors.has(id);
        return { ...data, color: isFocus ? data.color : '#ddd5c8', highlighted: id === nodeId, zIndex: id === nodeId ? 2 : 0 };
      });
      renderer.setSetting('edgeReducer', (id, data) => {
        const [source, target] = graph.extremities(id);
        const connected = !nodeId || source === nodeId || target === nodeId;
        return { ...data, color: connected ? data.color : '#e7e0d6', hidden: false, zIndex: connected ? 1 : 0 };
      });
      renderer.refresh();
    };
    const applyFocus = (nodeId) => {
      applyAppearance(nodeId);
      if (nodeId && graph.hasNode(nodeId)) {
        const display = renderer.getNodeDisplayData(nodeId);
        if (display) renderer.getCamera().animate({ x: display.x, y: display.y, ratio: 0.62 }, { duration: 420 });
      }
    };

    renderer.on('clickNode', ({ node }) => onSelectNode(node));
    renderer.on('doubleClickNode', ({ node }) => { onSelectNode(node); applyFocus(node); });
    renderer.on('clickEdge', ({ edge }) => onSelectEdge(edge));
    renderer.on('enterNode', ({ node }) => { applyAppearance(node); onHoverNode(node); });
    renderer.on('leaveNode', () => { applyAppearance(focusedNodeId || selectedNodeId); onHoverNode(null); });
    applyFocus(focusedNodeId || selectedNodeId);

    return () => {
      renderer.kill();
      rendererRef.current = null;
    };
  }, [nodes, edges, selectedNodeId, focusedNodeId, onSelectNode, onSelectEdge, onHoverNode]);

  return <div ref={containerRef} className="tl-graph-canvas" aria-label="Interactive evidence intelligence graph" role="application" />;
}
