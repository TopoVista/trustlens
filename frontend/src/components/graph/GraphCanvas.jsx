import React, { useEffect, useRef } from 'react';
import Sigma from 'sigma';
import { MultiDirectedGraph } from 'graphology';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import { connectedComponents } from 'graphology-components';

const COLORS = {
  CLAIM: '#b56f52', ENTITY: '#4c695c', VARIABLE: '#7b6aa8', VALUE: '#a57b43',
  EVENT: '#587895', DOCUMENT: '#6d665d', EVIDENCE: '#b48762', DATASET: '#4f7f78'
};

function seedComponents(graph) {
  const groups = connectedComponents(graph).filter((group) => group.length);
  const columns = Math.max(1, Math.ceil(Math.sqrt(groups.length)));
  groups.forEach((group, groupIndex) => {
    const centerX = (groupIndex % columns) * 16;
    const centerY = Math.floor(groupIndex / columns) * 16;
    group.forEach((nodeId, nodeIndex) => {
      const angle = (nodeIndex / Math.max(group.length, 1)) * Math.PI * 2;
      const radius = group.length === 1 ? 0 : 1.6 + Math.sqrt(nodeIndex + 1) * 1.15;
      graph.setNodeAttribute(nodeId, 'x', centerX + Math.cos(angle) * radius);
      graph.setNodeAttribute(nodeId, 'y', centerY + Math.sin(angle) * radius);
    });
  });
  // A single connected evidence story benefits from a light force pass. For
  // multiple disconnected stories, component packing is clearer and stable.
  if (groups.length === 1 && graph.order > 2) {
    try {
      forceAtlas2.assign(graph, {
        iterations: 90,
        settings: { gravity: 8, scalingRatio: 3, strongGravityMode: true, slowDown: 3 },
      });
    } catch {}
  }
}

export default function GraphCanvas({ nodes, edges, selectedNodeId, focusedNodeId, onSelectNode, onSelectEdge, onHoverNode }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return undefined;
    const graph = new MultiDirectedGraph();
    const nodeIds = new Set(nodes.map((node) => node.id));
    nodes.forEach((node) => {
      graph.addNode(node.id, {
        x: 0,
        y: 0,
        label: node.label.length > 54 ? `${node.label.slice(0, 51)}…` : node.label,
        fullLabel: node.label,
        size: 4.4,
        color: COLORS[node.type] || '#6d665d',
        nodeType: node.type,
        status: node.status,
      });
    });
    edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)).forEach((edge) => {
      graph.addEdgeWithKey(edge.id, edge.source, edge.target, {
        color: edge.relation === 'CONTRADICTS' ? '#b95b50' : '#b8ac9c',
        size: Math.max(0.65, 0.55 + edge.confidence * 1.05),
        relation: edge.relation,
        confidence: edge.confidence,
      });
    });
    graph.forEachNode((nodeId, attributes) => {
      graph.setNodeAttribute(nodeId, 'size', Math.min(12, attributes.size + Math.min(3.2, graph.degree(nodeId) * 0.5)));
    });
    seedComponents(graph);

    const renderer = new Sigma(graph, containerRef.current, {
      renderEdgeLabels: false,
      labelDensity: 0.06,
      labelGridCellSize: 145,
      labelRenderedSizeThreshold: 8,
      defaultEdgeColor: '#c6bcae',
      defaultNodeColor: '#6d665d',
      zIndex: true,
    });
    rendererRef.current = renderer;

    const applyAppearance = (nodeId) => {
      const neighbors = nodeId && graph.hasNode(nodeId) ? new Set(graph.neighbors(nodeId)) : new Set();
      renderer.setSetting('nodeReducer', (id, data) => {
        const isFocus = !nodeId || id === nodeId || neighbors.has(id);
        const showLabel = id === nodeId || (!nodeId && graph.degree(id) >= 4);
        return {
          ...data,
          label: showLabel ? data.label : undefined,
          color: isFocus ? data.color : '#ddd5c8',
          highlighted: id === nodeId,
          zIndex: id === nodeId ? 2 : 0,
        };
      });
      renderer.setSetting('edgeReducer', (id, data) => {
        const [source, target] = graph.extremities(id);
        const connected = !nodeId || source === nodeId || target === nodeId;
        return { ...data, color: connected ? data.color : '#e7e0d6', hidden: !connected, zIndex: connected ? 1 : 0 };
      });
      renderer.refresh();
    };
    const selectAndFocus = (nodeId) => {
      onSelectNode(nodeId);
      applyAppearance(nodeId);
      const display = renderer.getNodeDisplayData(nodeId);
      if (display) renderer.getCamera().animate({ x: display.x, y: display.y, ratio: 0.7 }, { duration: 360 });
    };

    renderer.on('clickNode', ({ node }) => selectAndFocus(node));
    renderer.on('doubleClickNode', ({ node }) => selectAndFocus(node));
    renderer.on('clickEdge', ({ edge }) => onSelectEdge(edge));
    renderer.on('enterNode', ({ node }) => { applyAppearance(node); onHoverNode(node); });
    renderer.on('leaveNode', () => { applyAppearance(focusedNodeId || selectedNodeId); onHoverNode(null); });
    applyAppearance(focusedNodeId || selectedNodeId);

    return () => {
      renderer.kill();
      rendererRef.current = null;
    };
  }, [nodes, edges, selectedNodeId, focusedNodeId, onSelectNode, onSelectEdge, onHoverNode]);

  return <div ref={containerRef} className="tl-graph-canvas" aria-label="Interactive evidence intelligence graph" role="application" />;
}
