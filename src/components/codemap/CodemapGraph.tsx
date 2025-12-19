'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { FaExpand, FaSearchPlus, FaSearchMinus } from 'react-icons/fa';
import type { CodemapGraph as CodemapGraphType, CodemapNode, CodemapEdge } from '@/types/codemap';

interface CodemapGraphProps {
  graph: CodemapGraphType;
  selectedNodeId?: string | null;
  onNodeClick?: (node: CodemapNode) => void;
  onNodeHover?: (node: CodemapNode | null) => void;
}

const NODE_COLORS: Record<string, string> = {
  file: '#60a5fa',
  module: '#34d399',
  class: '#f97316',
  function: '#a78bfa',
  method: '#c084fc',
  interface: '#ec4899',
  type: '#f472b6',
  endpoint: '#fbbf24',
  database: '#6366f1',
  external: '#9ca3af',
  variable: '#94a3b8',
  constant: '#94a3b8',
};

const IMPORTANCE_SCALE: Record<string, number> = {
  critical: 1.5,
  high: 1.25,
  medium: 1,
  low: 0.75,
};

export default function CodemapGraph({
  graph,
  selectedNodeId,
  onNodeClick,
  onNodeHover,
}: CodemapGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, width: 1000, height: 800 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [zoom, setZoom] = useState(1);

  // Calculate bounds from nodes
  useEffect(() => {
    if (graph.nodes.length === 0) return;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    
    graph.nodes.forEach(node => {
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      const w = node.width ?? 150;
      const h = node.height ?? 50;
      
      minX = Math.min(minX, x - w/2);
      minY = Math.min(minY, y - h/2);
      maxX = Math.max(maxX, x + w/2);
      maxY = Math.max(maxY, y + h/2);
    });

    const padding = 100;
    setViewBox({
      x: minX - padding,
      y: minY - padding,
      width: Math.max(maxX - minX + padding * 2, 800),
      height: Math.max(maxY - minY + padding * 2, 600),
    });
  }, [graph.nodes]);

  // Mouse handlers for panning
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsPanning(true);
      setPanStart({ x: e.clientX, y: e.clientY });
    }
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isPanning) return;

    const dx = (e.clientX - panStart.x) * (viewBox.width / (containerRef.current?.clientWidth ?? 1000));
    const dy = (e.clientY - panStart.y) * (viewBox.height / (containerRef.current?.clientHeight ?? 800));

    setViewBox(prev => ({
      ...prev,
      x: prev.x - dx,
      y: prev.y - dy,
    }));

    setPanStart({ x: e.clientX, y: e.clientY });
  }, [isPanning, panStart, viewBox]);

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
  }, []);

  // Zoom handlers
  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(prev * 1.2, 3));
    setViewBox(prev => ({
      x: prev.x + prev.width * 0.1,
      y: prev.y + prev.height * 0.1,
      width: prev.width * 0.8,
      height: prev.height * 0.8,
    }));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(prev / 1.2, 0.3));
    setViewBox(prev => ({
      x: prev.x - prev.width * 0.125,
      y: prev.y - prev.height * 0.125,
      width: prev.width * 1.25,
      height: prev.height * 1.25,
    }));
  }, []);

  const handleFitView = useCallback(() => {
    if (graph.nodes.length === 0) return;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    
    graph.nodes.forEach(node => {
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    });

    const padding = 150;
    setViewBox({
      x: minX - padding,
      y: minY - padding,
      width: Math.max(maxX - minX + padding * 2, 800),
      height: Math.max(maxY - minY + padding * 2, 600),
    });
    setZoom(1);
  }, [graph.nodes]);

  // Render node
  const renderNode = (node: CodemapNode) => {
    const x = node.x ?? 0;
    const y = node.y ?? 0;
    const width = (node.width ?? 150) * IMPORTANCE_SCALE[node.importance];
    const height = (node.height ?? 50) * IMPORTANCE_SCALE[node.importance];
    const isSelected = node.id === selectedNodeId;
    const color = NODE_COLORS[node.type] ?? '#6b7280';

    return (
      <g
        key={node.id}
        transform={`translate(${x}, ${y})`}
        onClick={() => onNodeClick?.(node)}
        onMouseEnter={() => onNodeHover?.(node)}
        onMouseLeave={() => onNodeHover?.(null)}
        className="cursor-pointer"
      >
        {/* Node background */}
        <rect
          x={-width / 2}
          y={-height / 2}
          width={width}
          height={height}
          rx={node.type === 'function' || node.type === 'method' ? height / 2 : 8}
          fill={color}
          fillOpacity={0.2}
          stroke={isSelected ? '#fff' : color}
          strokeWidth={isSelected ? 3 : 2}
          className="transition-all duration-200"
        />
        
        {/* Node label */}
        <text
          y={5}
          textAnchor="middle"
          fill="currentColor"
          fontSize={12}
          fontWeight={isSelected ? 600 : 400}
          className="pointer-events-none select-none"
        >
          {node.label.length > 20 ? node.label.slice(0, 17) + '...' : node.label}
        </text>

        {/* Type indicator */}
        <text
          y={-height / 2 + 12}
          x={-width / 2 + 8}
          fontSize={10}
          fill={color}
          className="pointer-events-none select-none"
        >
          {node.type}
        </text>
      </g>
    );
  };

  // Render edge
  const renderEdge = (edge: CodemapEdge) => {
    const sourceNode = graph.nodes.find(n => n.id === edge.source);
    const targetNode = graph.nodes.find(n => n.id === edge.target);
    
    if (!sourceNode || !targetNode) return null;

    const x1 = sourceNode.x ?? 0;
    const y1 = sourceNode.y ?? 0;
    const x2 = targetNode.x ?? 0;
    const y2 = targetNode.y ?? 0;

    // Calculate control point for curved edge
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const offset = Math.min(Math.sqrt(dx * dx + dy * dy) * 0.2, 50);
    const cx = midX + (dy > 0 ? offset : -offset) * 0.3;
    const cy = midY;

    const isHighlighted = selectedNodeId === edge.source || selectedNodeId === edge.target;

    return (
      <g key={edge.id}>
        <path
          d={`M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`}
          fill="none"
          stroke={isHighlighted ? '#fff' : '#6b7280'}
          strokeWidth={isHighlighted ? 2 : 1}
          strokeOpacity={isHighlighted ? 0.8 : 0.4}
          markerEnd="url(#arrowhead)"
          className="transition-all duration-200"
        />
        {edge.label && (
          <text
            x={cx}
            y={cy - 5}
            textAnchor="middle"
            fontSize={10}
            fill="#9ca3af"
            className="pointer-events-none select-none"
          >
            {edge.label}
          </text>
        )}
      </g>
    );
  };

  if (graph.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-secondary)]">
        <p>No graph data available</p>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-full bg-[var(--background)]"
    >
      {/* Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
        <button
          onClick={handleZoomIn}
          className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] hover:bg-[var(--background)] transition-colors"
          title="Zoom In"
        >
          <FaSearchPlus className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] hover:bg-[var(--background)] transition-colors"
          title="Zoom Out"
        >
          <FaSearchMinus className="w-4 h-4" />
        </button>
        <button
          onClick={handleFitView}
          className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] hover:bg-[var(--background)] transition-colors"
          title="Fit View"
        >
          <FaExpand className="w-4 h-4" />
        </button>
      </div>

      {/* SVG Graph */}
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={isPanning ? 'cursor-grabbing' : 'cursor-grab'}
      >
        {/* Defs */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#6b7280" />
          </marker>
        </defs>

        {/* Edges (render first so they're behind nodes) */}
        <g className="edges">
          {graph.edges.map(renderEdge)}
        </g>

        {/* Nodes */}
        <g className="nodes">
          {graph.nodes.map(renderNode)}
        </g>
      </svg>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 p-3 rounded-lg bg-[var(--bg-secondary)]/90 border border-[var(--border-color)]">
        <p className="text-xs text-[var(--text-secondary)] mb-2">Node Types</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(NODE_COLORS).slice(0, 6).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <div 
                className="w-3 h-3 rounded"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-[var(--foreground)]">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
