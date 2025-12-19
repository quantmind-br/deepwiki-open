/**
 * API client for codemap operations.
 */

import type {
  CodemapGenerateRequest,
  CodemapGenerateResponse,
  Codemap,
  CodemapProgress,
  CodemapHistoryItem,
} from '@/types/codemap';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

/**
 * Generate a new codemap via REST API (synchronous).
 */
export async function generateCodemap(
  request: CodemapGenerateRequest
): Promise<CodemapGenerateResponse> {
  const response = await fetch(`${API_BASE}/api/codemap/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to generate codemap');
  }

  return response.json();
}

/**
 * Get a codemap by ID.
 */
export async function getCodemap(codemapId: string): Promise<Codemap> {
  const response = await fetch(`${API_BASE}/api/codemap/${codemapId}`);

  if (!response.ok) {
    throw new Error(`Codemap ${codemapId} not found`);
  }

  return response.json();
}

/**
 * Delete a codemap.
 */
export async function deleteCodemap(codemapId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/codemap/${codemapId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete codemap ${codemapId}`);
  }
}

/**
 * List all codemaps.
 */
export async function listCodemaps(
  repoUrl?: string,
  limit = 50
): Promise<CodemapHistoryItem[]> {
  const params = new URLSearchParams();
  if (repoUrl) params.set('repo_url', repoUrl);
  params.set('limit', String(limit));

  const response = await fetch(`${API_BASE}/api/codemap/list/all?${params}`);

  if (!response.ok) {
    throw new Error('Failed to list codemaps');
  }

  return response.json();
}

/**
 * Get codemaps for a specific repository.
 */
export async function getRepoCodemaps(
  owner: string,
  repo: string,
  limit = 20
): Promise<CodemapHistoryItem[]> {
  const response = await fetch(
    `${API_BASE}/api/codemap/repo/${owner}/${repo}?limit=${limit}`
  );

  if (!response.ok) {
    throw new Error('Failed to get repository codemaps');
  }

  return response.json();
}

/**
 * Generate share token for a codemap.
 */
export async function shareCodemap(
  codemapId: string
): Promise<{ share_token: string; codemap_id: string; is_public: boolean }> {
  const response = await fetch(`${API_BASE}/api/codemap/${codemapId}/share`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to share codemap');
  }

  return response.json();
}

/**
 * Get a shared codemap by token.
 */
export async function getSharedCodemap(shareToken: string): Promise<Codemap> {
  const response = await fetch(`${API_BASE}/api/codemap/shared/${shareToken}`);

  if (!response.ok) {
    throw new Error('Shared codemap not found');
  }

  return response.json();
}

/**
 * Export codemap as HTML.
 */
export async function exportCodemapHtml(codemapId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/codemap/${codemapId}/export/html`);

  if (!response.ok) {
    throw new Error('Failed to export codemap');
  }

  return response.blob();
}

/**
 * Export codemap as Mermaid code.
 */
export async function exportCodemapMermaid(codemapId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/codemap/${codemapId}/export/mermaid`);

  if (!response.ok) {
    throw new Error('Failed to export codemap');
  }

  return response.text();
}

/**
 * WebSocket client for real-time codemap generation.
 */
export class CodemapWebSocketClient {
  private ws: WebSocket | null = null;
  private onProgress?: (progress: CodemapProgress) => void;
  private onComplete?: (codemap: Codemap) => void;
  private onError?: (error: string) => void;

  constructor(
    callbacks: {
      onProgress?: (progress: CodemapProgress) => void;
      onComplete?: (codemap: Codemap) => void;
      onError?: (error: string) => void;
    }
  ) {
    this.onProgress = callbacks.onProgress;
    this.onComplete = callbacks.onComplete;
    this.onError = callbacks.onError;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = API_BASE.replace('http', 'ws') + '/ws/codemap';
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        resolve();
      };

      this.ws.onerror = () => {
        reject(new Error('WebSocket connection failed'));
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case 'progress':
              this.onProgress?.(message.data as CodemapProgress);
              break;
            case 'complete':
              this.onComplete?.(message.data as Codemap);
              break;
            case 'error':
              this.onError?.(message.message || 'Unknown error');
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onclose = () => {
        this.ws = null;
      };
    });
  }

  generate(request: CodemapGenerateRequest): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.onError?.('WebSocket not connected');
      return;
    }

    this.ws.send(JSON.stringify(request));
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
