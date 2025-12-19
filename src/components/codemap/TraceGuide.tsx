'use client';

import React, { useState, useCallback } from 'react';
import { FaChevronDown, FaChevronRight, FaLink, FaBookOpen } from 'react-icons/fa';
import Markdown from '@/components/Markdown';
import type { TraceGuide as TraceGuideType, TraceSection } from '@/types/codemap';

interface TraceGuideProps {
  traceGuide: TraceGuideType;
  onNodeClick?: (nodeId: string) => void;
  highlightedNodeIds?: string[];
}

export default function TraceGuide({
  traceGuide,
  onNodeClick,
  highlightedNodeIds = [],
}: TraceGuideProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(traceGuide.sections.map(s => s.id))
  );

  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  }, []);

  const renderSection = (section: TraceSection) => {
    const isExpanded = expandedSections.has(section.id);
    const hasHighlightedNodes = section.node_ids.some(id => highlightedNodeIds.includes(id));

    return (
      <div
        key={section.id}
        className={`border rounded-lg overflow-hidden transition-all ${
          hasHighlightedNodes
            ? 'border-[var(--accent-primary)]'
            : 'border-[var(--border-color)]'
        }`}
      >
        {/* Section Header */}
        <button
          onClick={() => toggleSection(section.id)}
          className="w-full flex items-center justify-between p-3 bg-[var(--bg-secondary)] hover:bg-[var(--background)] transition-colors"
        >
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <FaChevronDown className="w-3 h-3 text-[var(--text-secondary)]" />
            ) : (
              <FaChevronRight className="w-3 h-3 text-[var(--text-secondary)]" />
            )}
            <span className="font-medium text-[var(--foreground)]">
              {section.title}
            </span>
          </div>
          {section.node_ids.length > 0 && (
            <span className="text-xs text-[var(--text-secondary)] bg-[var(--background)] px-2 py-1 rounded">
              {section.node_ids.length} nodes
            </span>
          )}
        </button>

        {/* Section Content */}
        {isExpanded && (
          <div className="p-4 bg-[var(--background)]">
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <Markdown content={section.content} />
            </div>

            {/* Related Nodes */}
            {section.node_ids.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-secondary)] mb-2 flex items-center gap-1">
                  <FaLink className="w-3 h-3" />
                  Related nodes
                </p>
                <div className="flex flex-wrap gap-2">
                  {section.node_ids.map(nodeId => (
                    <button
                      key={nodeId}
                      onClick={() => onNodeClick?.(nodeId)}
                      className={`text-xs px-2 py-1 rounded transition-colors ${
                        highlightedNodeIds.includes(nodeId)
                          ? 'bg-[var(--accent-primary)] text-white'
                          : 'bg-[var(--bg-secondary)] text-[var(--foreground)] hover:bg-[var(--accent-primary)]/20'
                      }`}
                    >
                      {nodeId.split(':').pop()?.slice(0, 12) || nodeId}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-[var(--bg-secondary)]">
      {/* Header - Fixed, not sticky */}
      <div className="flex-shrink-0 p-4 bg-[var(--bg-secondary)] border-b border-[var(--border-color)]">
        <div className="flex items-center gap-2 mb-2">
          <FaBookOpen className="w-5 h-5 flex-shrink-0 text-[var(--accent-primary)]" />
          <h2 className="text-lg font-semibold text-[var(--foreground)] line-clamp-2">
            {traceGuide.title}
          </h2>
        </div>
        <p className="text-sm text-[var(--text-secondary)] line-clamp-3">
          {traceGuide.summary}
        </p>
      </div>

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto">
        {/* Sections */}
        <div className="p-4 space-y-3">
          {traceGuide.sections
            .sort((a, b) => a.order - b.order)
            .map(renderSection)}
        </div>

        {/* Conclusion */}
        {traceGuide.conclusion && (
          <div className="p-4 border-t border-[var(--border-color)]">
            <h3 className="text-sm font-medium text-[var(--foreground)] mb-2">
              Conclusion
            </h3>
            <p className="text-sm text-[var(--text-secondary)]">
              {traceGuide.conclusion}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
