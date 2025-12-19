'use client';

import React, { useState, useCallback } from 'react';
import { FaSearch, FaHistory, FaCog, FaSpinner } from 'react-icons/fa';
import type { CodemapProgress, CodemapHistoryItem } from '@/types/codemap';

interface CodemapPanelProps {
  repoOwner: string;
  repoName: string;
  repoType: string;
  token?: string;
  provider?: string;
  model?: string;
  onGenerate: (query: string, options?: Record<string, unknown>) => void;
  onSelectHistory?: (item: CodemapHistoryItem) => void;
  progress?: CodemapProgress | null;
  history?: CodemapHistoryItem[];
  isGenerating?: boolean;
}

export default function CodemapPanel({
  repoOwner,
  repoName,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  repoType,
  onGenerate,
  onSelectHistory,
  progress,
  history = [],
  isGenerating = false,
}: CodemapPanelProps) {
  const [query, setQuery] = useState('');
  const [showOptions, setShowOptions] = useState(false);
  const [options, setOptions] = useState({
    analysisType: 'auto',
    depth: 3,
    maxNodes: 50,
  });

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isGenerating) {
      onGenerate(query.trim(), options);
    }
  }, [query, options, isGenerating, onGenerate]);

  const suggestedQueries = [
    'How does authentication work?',
    'Show me the data flow for user registration',
    'What are the main API endpoints?',
    'How are database queries handled?',
    'Trace the request lifecycle',
  ];

  return (
    <div className="flex flex-col h-full bg-[var(--bg-secondary)] border-r border-[var(--border-color)]">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border-color)]">
        <h2 className="text-lg font-semibold text-[var(--foreground)]">
          Code Map
        </h2>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          {repoOwner}/{repoName}
        </p>
      </div>

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="p-4 border-b border-[var(--border-color)]">
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about the codebase..."
            className="w-full p-3 pr-10 rounded-lg bg-[var(--background)] border border-[var(--border-color)] text-[var(--foreground)] placeholder-[var(--text-secondary)] resize-none focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
            rows={3}
            disabled={isGenerating}
          />
          <button
            type="submit"
            disabled={!query.trim() || isGenerating}
            className="absolute right-2 bottom-2 p-2 rounded-md bg-[var(--accent-primary)] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--accent-primary)]/80 transition-colors"
          >
            {isGenerating ? (
              <FaSpinner className="w-4 h-4 animate-spin" />
            ) : (
              <FaSearch className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Options Toggle */}
        <button
          type="button"
          onClick={() => setShowOptions(!showOptions)}
          className="mt-2 flex items-center gap-1 text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
        >
          <FaCog className="w-3 h-3" />
          <span>Options</span>
        </button>

        {showOptions && (
          <div className="mt-3 space-y-3 p-3 rounded-lg bg-[var(--background)] border border-[var(--border-color)]">
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">
                Analysis Type
              </label>
              <select
                value={options.analysisType}
                onChange={(e) => setOptions({ ...options, analysisType: e.target.value })}
                className="w-full p-2 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)] text-sm"
              >
                <option value="auto">Auto-detect</option>
                <option value="data_flow">Data Flow</option>
                <option value="control_flow">Control Flow</option>
                <option value="dependencies">Dependencies</option>
                <option value="call_graph">Call Graph</option>
                <option value="architecture">Architecture</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">
                Depth: {options.depth}
              </label>
              <input
                type="range"
                min={1}
                max={5}
                value={options.depth}
                onChange={(e) => setOptions({ ...options, depth: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">
                Max Nodes: {options.maxNodes}
              </label>
              <input
                type="range"
                min={10}
                max={100}
                step={10}
                value={options.maxNodes}
                onChange={(e) => setOptions({ ...options, maxNodes: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>
          </div>
        )}
      </form>

      {/* Progress */}
      {progress && isGenerating && (
        <div className="p-4 border-b border-[var(--border-color)]">
          <div className="flex items-center gap-2 mb-2">
            <FaSpinner className="w-4 h-4 animate-spin text-[var(--accent-primary)]" />
            <span className="text-sm text-[var(--foreground)]">{progress.current_step}</span>
          </div>
          <div className="w-full h-2 bg-[var(--background)] rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--accent-primary)] transition-all duration-300"
              style={{ width: `${progress.progress_percent}%` }}
            />
          </div>
          <div className="mt-1 text-xs text-[var(--text-secondary)]">
            {progress.nodes_found > 0 && `${progress.nodes_found} nodes found`}
            {progress.files_analyzed > 0 && ` | ${progress.files_analyzed} files analyzed`}
          </div>
        </div>
      )}

      {/* Suggested Queries */}
      {!isGenerating && (
        <div className="p-4 border-b border-[var(--border-color)]">
          <h3 className="text-sm font-medium text-[var(--foreground)] mb-2">
            Suggestions
          </h3>
          <div className="space-y-1">
            {suggestedQueries.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setQuery(suggestion)}
                className="w-full text-left text-sm p-2 rounded hover:bg-[var(--background)] text-[var(--text-secondary)] hover:text-[var(--foreground)] transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex items-center gap-2 mb-3">
            <FaHistory className="w-4 h-4 text-[var(--text-secondary)]" />
            <h3 className="text-sm font-medium text-[var(--foreground)]">History</h3>
          </div>
          <div className="space-y-2">
            {history.map((item) => (
              <button
                key={item.id}
                onClick={() => onSelectHistory?.(item)}
                className="w-full text-left p-3 rounded-lg bg-[var(--background)] hover:bg-[var(--background)]/80 border border-[var(--border-color)] transition-colors"
              >
                <p className="text-sm font-medium text-[var(--foreground)] truncate">
                  {item.title}
                </p>
                <p className="text-xs text-[var(--text-secondary)] mt-1 truncate">
                  {item.query}
                </p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  {new Date(item.created_at).toLocaleDateString()}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
