'use client';

import React, { useCallback, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { FaArrowLeft, FaGithub, FaGitlab, FaBitbucket, FaExclamationTriangle } from 'react-icons/fa';

import { CodemapPanel, CodemapViewer } from '@/components/codemap';
import { useCodemap } from '@/hooks/codemap';
import type { CodemapHistoryItem, CodemapGenerateRequest } from '@/types/codemap';

export default function CodemapPage() {
  const params = useParams();
  const searchParams = useSearchParams();

  const owner = params.owner as string;
  const repo = params.repo as string;
  const repoType = searchParams.get('type') || 'github';
  const token = searchParams.get('token') || '';

  // Build repo URL
  const getRepoUrl = () => {
    switch (repoType) {
      case 'gitlab':
        return `https://gitlab.com/${owner}/${repo}`;
      case 'bitbucket':
        return `https://bitbucket.org/${owner}/${repo}`;
      default:
        return `https://github.com/${owner}/${repo}`;
    }
  };

  const repoUrl = getRepoUrl();

  const {
    codemap,
    progress,
    history,
    isGenerating,
    error,
    generate,
    loadCodemap,
    share,
    exportAs,
    clearError,
  } = useCodemap({
    repoOwner: owner,
    repoName: repo,
    repoType,
    repoUrl,
    token: token || undefined,
    provider: 'google',
  });

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  const handleGenerate = useCallback((query: string, options?: Record<string, unknown>) => {
    generate(query, options as Partial<CodemapGenerateRequest>);
  }, [generate]);

  const handleSelectHistory = useCallback((item: CodemapHistoryItem) => {
    loadCodemap(item.id);
  }, [loadCodemap]);

  const handleShare = useCallback(async () => {
    const shareToken = await share();
    if (shareToken) {
      const url = `${window.location.origin}/${owner}/${repo}/codemap?share=${shareToken}`;
      setShareUrl(url);
      // Copy to clipboard
      navigator.clipboard.writeText(url);
      alert('Share link copied to clipboard!');
    }
  }, [share, owner, repo]);

  const handleExport = useCallback((format: 'html' | 'mermaid' | 'json') => {
    exportAs(format);
  }, [exportAs]);

  const getRepoIcon = () => {
    switch (repoType) {
      case 'gitlab':
        return <FaGitlab className="w-5 h-5" />;
      case 'bitbucket':
        return <FaBitbucket className="w-5 h-5" />;
      default:
        return <FaGithub className="w-5 h-5" />;
    }
  };

  return (
    <div className="flex h-screen bg-[var(--background)]">
      {/* Left Panel */}
      <div className="w-80 flex-shrink-0">
        <CodemapPanel
          repoOwner={owner}
          repoName={repo}
          repoType={repoType}
          token={token}
          onGenerate={handleGenerate}
          onSelectHistory={handleSelectHistory}
          progress={progress}
          history={history}
          isGenerating={isGenerating}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
          <div className="flex items-center gap-4">
            <Link
              href={`/${owner}/${repo}?type=${repoType}`}
              className="flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--foreground)] transition-colors"
            >
              <FaArrowLeft className="w-4 h-4" />
              <span>Back to Wiki</span>
            </Link>
            <div className="h-6 w-px bg-[var(--border-color)]" />
            <a
              href={repoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-[var(--foreground)] hover:text-[var(--accent-primary)] transition-colors"
            >
              {getRepoIcon()}
              <span className="font-medium">{owner}/{repo}</span>
            </a>
          </div>
          <div className="text-sm text-[var(--text-secondary)]">
            Code Map Explorer
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border-b border-red-500/20">
            <FaExclamationTriangle className="w-5 h-5 text-red-500" />
            <p className="text-sm text-red-500 flex-1">{error}</p>
            <button
              onClick={clearError}
              className="text-sm text-red-500 hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {codemap ? (
            <CodemapViewer
              codemap={codemap}
              onShare={handleShare}
              onExport={handleExport}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <div className="max-w-md">
                <h2 className="text-2xl font-semibold text-[var(--foreground)] mb-4">
                  Explore Your Codebase
                </h2>
                <p className="text-[var(--text-secondary)] mb-6">
                  Enter a question about your code in the panel on the left.
                  The AI will analyze the repository and generate an interactive
                  map showing how different parts of the code connect.
                </p>
                <div className="grid grid-cols-2 gap-4 text-left">
                  <div className="p-4 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                    <h3 className="font-medium text-[var(--foreground)] mb-2">
                      Data Flow
                    </h3>
                    <p className="text-sm text-[var(--text-secondary)]">
                      Trace how data moves through your application
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                    <h3 className="font-medium text-[var(--foreground)] mb-2">
                      Dependencies
                    </h3>
                    <p className="text-sm text-[var(--text-secondary)]">
                      See what modules depend on each other
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                    <h3 className="font-medium text-[var(--foreground)] mb-2">
                      Call Graph
                    </h3>
                    <p className="text-sm text-[var(--text-secondary)]">
                      Understand function call hierarchies
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                    <h3 className="font-medium text-[var(--foreground)] mb-2">
                      Architecture
                    </h3>
                    <p className="text-sm text-[var(--text-secondary)]">
                      Get a high-level view of your system
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
