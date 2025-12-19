'use client';

import React from 'react';
import { FaTimes, FaFile, FaCode, FaExternalLinkAlt } from 'react-icons/fa';
import type { CodemapNode } from '@/types/codemap';

interface NodeInspectorProps {
  node: CodemapNode;
  onClose: () => void;
  onNavigateToCode?: (location: CodemapNode['location']) => void;
}

const TYPE_ICONS: Record<string, string> = {
  file: '📄',
  module: '📦',
  class: '🏛️',
  function: '⚙️',
  method: '🔧',
  interface: '📋',
  type: '📝',
  endpoint: '🌐',
  database: '🗄️',
  external: '🔗',
  variable: '📊',
  constant: '🔒',
};

export default function NodeInspector({
  node,
  onClose,
  onNavigateToCode,
}: NodeInspectorProps) {
  return (
    <div className="absolute bottom-4 left-4 right-4 max-w-md bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg shadow-xl overflow-hidden z-20">
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-[var(--background)] border-b border-[var(--border-color)]">
        <div className="flex items-center gap-2">
          <span className="text-xl">{TYPE_ICONS[node.type] || '📦'}</span>
          <div>
            <h3 className="font-semibold text-[var(--foreground)]">{node.label}</h3>
            <p className="text-xs text-[var(--text-secondary)]">{node.type}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-[var(--bg-secondary)] transition-colors"
        >
          <FaTimes className="w-4 h-4 text-[var(--text-secondary)]" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4 max-h-80 overflow-y-auto">
        {/* Description */}
        {node.description && (
          <div>
            <p className="text-xs text-[var(--text-secondary)] mb-1">Description</p>
            <p className="text-sm text-[var(--foreground)]">{node.description}</p>
          </div>
        )}

        {/* Location */}
        {node.location && (
          <div>
            <p className="text-xs text-[var(--text-secondary)] mb-1 flex items-center gap-1">
              <FaFile className="w-3 h-3" />
              Location
            </p>
            <button
              onClick={() => onNavigateToCode?.(node.location!)}
              className="flex items-center gap-2 text-sm text-[var(--accent-primary)] hover:underline"
            >
              <span>{node.location.file_path}</span>
              <span className="text-[var(--text-secondary)]">
                L{node.location.line_start}
                {node.location.line_end !== node.location.line_start && `-${node.location.line_end}`}
              </span>
              <FaExternalLinkAlt className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* Code Snippet */}
        {node.snippet && (
          <div>
            <p className="text-xs text-[var(--text-secondary)] mb-1 flex items-center gap-1">
              <FaCode className="w-3 h-3" />
              Preview
            </p>
            <pre className="p-3 rounded bg-[var(--background)] text-xs overflow-x-auto border border-[var(--border-color)]">
              <code>{node.snippet.code}</code>
            </pre>
          </div>
        )}

        {/* Importance Badge */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--text-secondary)]">Importance:</span>
          <span className={`text-xs px-2 py-0.5 rounded ${
            node.importance === 'critical' ? 'bg-red-500/20 text-red-400' :
            node.importance === 'high' ? 'bg-orange-500/20 text-orange-400' :
            node.importance === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-gray-500/20 text-gray-400'
          }`}>
            {node.importance}
          </span>
        </div>

        {/* Metadata */}
        {Object.keys(node.metadata).length > 0 && (
          <div>
            <p className="text-xs text-[var(--text-secondary)] mb-1">Details</p>
            <div className="space-y-1">
              {Array.isArray(node.metadata.parameters) && (
                <p className="text-xs text-[var(--foreground)]">
                  <span className="text-[var(--text-secondary)]">Parameters: </span>
                  {(node.metadata.parameters as string[]).join(', ') || 'none'}
                </p>
              )}
              {typeof node.metadata.return_type === 'string' && (
                <p className="text-xs text-[var(--foreground)]">
                  <span className="text-[var(--text-secondary)]">Returns: </span>
                  {node.metadata.return_type}
                </p>
              )}
              {Array.isArray(node.metadata.bases) && (node.metadata.bases as string[]).length > 0 && (
                <p className="text-xs text-[var(--foreground)]">
                  <span className="text-[var(--text-secondary)]">Extends: </span>
                  {(node.metadata.bases as string[]).join(', ')}
                </p>
              )}
              {Array.isArray(node.metadata.decorators) && (node.metadata.decorators as string[]).length > 0 && (
                <p className="text-xs text-[var(--foreground)]">
                  <span className="text-[var(--text-secondary)]">Decorators: </span>
                  {(node.metadata.decorators as string[]).join(', ')}
                </p>
              )}
              {node.metadata.is_async === true && (
                <p className="text-xs text-[var(--accent-primary)]">async</p>
              )}
              {node.metadata.is_exported === true && (
                <p className="text-xs text-green-400">exported</p>
              )}
            </div>
          </div>
        )}

        {/* Group */}
        {node.group && (
          <div>
            <span className="text-xs text-[var(--text-secondary)]">Group: </span>
            <span className="text-xs text-[var(--foreground)]">{node.group}</span>
          </div>
        )}
      </div>
    </div>
  );
}
