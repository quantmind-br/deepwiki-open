'use client';

import React, { useState, useCallback } from 'react';
import { FaColumns, FaProjectDiagram, FaBook, FaShare, FaDownload } from 'react-icons/fa';
import CodemapGraph from './CodemapGraph';
import TraceGuide from './TraceGuide';
import NodeInspector from './NodeInspector';
import Mermaid from '@/components/Mermaid';
import type { Codemap, CodemapNode } from '@/types/codemap';

interface CodemapViewerProps {
  codemap: Codemap;
  onShare?: () => void;
  onExport?: (format: 'html' | 'mermaid' | 'json') => void;
}

type ViewMode = 'split' | 'graph' | 'trace' | 'mermaid';

export default function CodemapViewer({
  codemap,
  onShare,
  onExport,
}: CodemapViewerProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [selectedNode, setSelectedNode] = useState<CodemapNode | null>(null);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState<string[]>([]);

  const handleNodeClick = useCallback((node: CodemapNode) => {
    setSelectedNode(node);
    setHighlightedNodeIds([node.id]);
  }, []);

  const handleNodeHover = useCallback((node: CodemapNode | null) => {
    if (node && !selectedNode) {
      setHighlightedNodeIds([node.id]);
    }
  }, [selectedNode]);

  const handleTraceNodeClick = useCallback((nodeId: string) => {
    const node = codemap.graph.nodes.find(n => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
      setHighlightedNodeIds([nodeId]);
    }
  }, [codemap.graph.nodes]);

  const handleNavigateToCode = useCallback((location: CodemapNode['location']) => {
    if (!location) return;
    // Could integrate with GitHub/GitLab link or VS Code extension
    const url = `${codemap.repo_url}/blob/main/${location.file_path}#L${location.line_start}`;
    window.open(url, '_blank');
  }, [codemap.repo_url]);

  return (
    <div className="flex flex-col h-full bg-[var(--background)]">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-[var(--foreground)]">
            {codemap.title}
          </h2>
          <span className="text-xs text-[var(--text-secondary)] bg-[var(--background)] px-2 py-1 rounded">
            {codemap.graph.nodes.length} nodes | {codemap.graph.edges.length} edges
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Buttons */}
          <div className="flex rounded-lg overflow-hidden border border-[var(--border-color)]">
            <button
              onClick={() => setViewMode('split')}
              className={`p-2 ${viewMode === 'split' ? 'bg-[var(--accent-primary)] text-white' : 'bg-[var(--background)] hover:bg-[var(--bg-secondary)]'}`}
              title="Split View"
            >
              <FaColumns className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`p-2 ${viewMode === 'graph' ? 'bg-[var(--accent-primary)] text-white' : 'bg-[var(--background)] hover:bg-[var(--bg-secondary)]'}`}
              title="Graph View"
            >
              <FaProjectDiagram className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('trace')}
              className={`p-2 ${viewMode === 'trace' ? 'bg-[var(--accent-primary)] text-white' : 'bg-[var(--background)] hover:bg-[var(--bg-secondary)]'}`}
              title="Trace Guide"
            >
              <FaBook className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('mermaid')}
              className={`p-2 ${viewMode === 'mermaid' ? 'bg-[var(--accent-primary)] text-white' : 'bg-[var(--background)] hover:bg-[var(--bg-secondary)]'}`}
              title="Mermaid Diagram"
            >
              <span className="text-xs font-bold">M</span>
            </button>
          </div>

          {/* Actions */}
          {onShare && (
            <button
              onClick={onShare}
              className="p-2 rounded-lg bg-[var(--background)] border border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors"
              title="Share"
            >
              <FaShare className="w-4 h-4" />
            </button>
          )}
          {onExport && (
            <div className="relative group">
              <button
                className="p-2 rounded-lg bg-[var(--background)] border border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors"
                title="Export"
              >
                <FaDownload className="w-4 h-4" />
              </button>
              <div className="absolute right-0 top-full mt-1 hidden group-hover:block bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg shadow-lg overflow-hidden z-20">
                <button
                  onClick={() => onExport('html')}
                  className="block w-full px-4 py-2 text-sm text-left hover:bg-[var(--background)]"
                >
                  Export as HTML
                </button>
                <button
                  onClick={() => onExport('mermaid')}
                  className="block w-full px-4 py-2 text-sm text-left hover:bg-[var(--background)]"
                >
                  Export Mermaid
                </button>
                <button
                  onClick={() => onExport('json')}
                  className="block w-full px-4 py-2 text-sm text-left hover:bg-[var(--background)]"
                >
                  Export JSON
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'split' && (
          <div className="flex h-full overflow-hidden">
            <div className="flex-1 relative border-r border-[var(--border-color)] overflow-hidden">
              <CodemapGraph
                graph={codemap.graph}
                selectedNodeId={selectedNode?.id}
                onNodeClick={handleNodeClick}
                onNodeHover={handleNodeHover}
              />
              {selectedNode && (
                <NodeInspector
                  node={selectedNode}
                  onClose={() => setSelectedNode(null)}
                  onNavigateToCode={handleNavigateToCode}
                />
              )}
            </div>
            <div className="w-96 flex-shrink-0 overflow-hidden">
              <TraceGuide
                traceGuide={codemap.trace_guide}
                onNodeClick={handleTraceNodeClick}
                highlightedNodeIds={highlightedNodeIds}
              />
            </div>
          </div>
        )}

        {viewMode === 'graph' && (
          <div className="h-full relative">
            <CodemapGraph
              graph={codemap.graph}
              selectedNodeId={selectedNode?.id}
              onNodeClick={handleNodeClick}
              onNodeHover={handleNodeHover}
            />
            {selectedNode && (
              <NodeInspector
                node={selectedNode}
                onClose={() => setSelectedNode(null)}
                onNavigateToCode={handleNavigateToCode}
              />
            )}
          </div>
        )}

        {viewMode === 'trace' && (
          <TraceGuide
            traceGuide={codemap.trace_guide}
            onNodeClick={handleTraceNodeClick}
            highlightedNodeIds={highlightedNodeIds}
          />
        )}

        {viewMode === 'mermaid' && (
          <div className="h-full p-4 overflow-auto">
            <Mermaid chart={codemap.render.mermaid} />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <p className="text-xs text-[var(--text-secondary)] text-center">
          Generated in {(codemap.generation_time_ms / 1000).toFixed(1)}s | 
          Model: {codemap.model_used} | 
          Query: &quot;{codemap.query}&quot;
        </p>
      </div>
    </div>
  );
}
