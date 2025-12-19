'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import type {
  Codemap,
  CodemapProgress,
  CodemapGenerateRequest,
  CodemapHistoryItem,
} from '@/types/codemap';
import {
  CodemapWebSocketClient,
  getCodemap,
  getRepoCodemaps,
  shareCodemap,
  exportCodemapHtml,
  exportCodemapMermaid,
} from '@/utils/codemap/client';

interface UseCodemapOptions {
  repoOwner: string;
  repoName: string;
  repoType: string;
  repoUrl: string;
  token?: string;
  provider?: string;
  model?: string;
}

interface UseCodemapReturn {
  codemap: Codemap | null;
  progress: CodemapProgress | null;
  history: CodemapHistoryItem[];
  isGenerating: boolean;
  error: string | null;
  generate: (query: string, options?: Partial<CodemapGenerateRequest>) => Promise<void>;
  loadCodemap: (codemapId: string) => Promise<void>;
  loadHistory: () => Promise<void>;
  share: () => Promise<string | null>;
  exportAs: (format: 'html' | 'mermaid' | 'json') => Promise<void>;
  clearError: () => void;
}

export function useCodemap(options: UseCodemapOptions): UseCodemapReturn {
  const { repoOwner, repoName, repoType, repoUrl, token, provider, model } = options;

  const [codemap, setCodemap] = useState<Codemap | null>(null);
  const [progress, setProgress] = useState<CodemapProgress | null>(null);
  const [history, setHistory] = useState<CodemapHistoryItem[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsClientRef = useRef<CodemapWebSocketClient | null>(null);

  // Clean up WebSocket on unmount
  useEffect(() => {
    return () => {
      wsClientRef.current?.disconnect();
    };
  }, []);

  // Load history on mount
  useEffect(() => {
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repoOwner, repoName]);

  const loadHistory = useCallback(async () => {
    try {
      const items = await getRepoCodemaps(repoOwner, repoName);
      setHistory(items);
    } catch (e) {
      console.error('Failed to load codemap history:', e);
    }
  }, [repoOwner, repoName]);

  const generate = useCallback(async (
    query: string,
    requestOptions?: Partial<CodemapGenerateRequest>
  ) => {
    setIsGenerating(true);
    setProgress(null);
    setError(null);
    setCodemap(null);

    const request: CodemapGenerateRequest = {
      repo_url: repoUrl,
      query,
      type: repoType,
      token,
      provider: provider || 'google',
      model,
      language: 'en',
      analysis_type: 'auto',
      depth: 3,
      max_nodes: 50,
      ...requestOptions,
    };

    // Use WebSocket for real-time updates
    const client = new CodemapWebSocketClient({
      onProgress: (progressData) => {
        setProgress(progressData);
      },
      onComplete: (codemapData) => {
        setCodemap(codemapData);
        setIsGenerating(false);
        setProgress(null);
        // Refresh history
        loadHistory();
      },
      onError: (errorMsg) => {
        setError(errorMsg);
        setIsGenerating(false);
        setProgress(null);
      },
    });

    wsClientRef.current = client;

    try {
      await client.connect();
      client.generate(request);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to connect');
      setIsGenerating(false);
    }
  }, [repoUrl, repoType, token, provider, model, loadHistory]);

  const loadCodemap = useCallback(async (codemapId: string) => {
    try {
      setError(null);
      const data = await getCodemap(codemapId);
      setCodemap(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load codemap');
    }
  }, []);

  const share = useCallback(async (): Promise<string | null> => {
    if (!codemap) return null;

    try {
      const result = await shareCodemap(codemap.id);
      return result.share_token;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to share');
      return null;
    }
  }, [codemap]);

  const exportAs = useCallback(async (format: 'html' | 'mermaid' | 'json') => {
    if (!codemap) return;

    try {
      if (format === 'html') {
        const blob = await exportCodemapHtml(codemap.id);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `codemap-${codemap.id}.html`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === 'mermaid') {
        const mermaidCode = await exportCodemapMermaid(codemap.id);
        const blob = new Blob([mermaidCode], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `codemap-${codemap.id}.mmd`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === 'json') {
        const json = JSON.stringify(codemap.render.json_graph, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `codemap-${codemap.id}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to export');
    }
  }, [codemap]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    codemap,
    progress,
    history,
    isGenerating,
    error,
    generate,
    loadCodemap,
    loadHistory,
    share,
    exportAs,
    clearError,
  };
}
