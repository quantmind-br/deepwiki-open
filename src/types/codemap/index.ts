/**
 * TypeScript types for the Codemap feature.
 */

// Enums
export type NodeType =
  | 'file' | 'module' | 'class' | 'function' | 'method'
  | 'variable' | 'constant' | 'interface' | 'type'
  | 'endpoint' | 'database' | 'external';

export type EdgeType =
  | 'imports' | 'exports' | 'calls' | 'extends' | 'implements'
  | 'uses' | 'returns' | 'instantiates' | 'data_flow'
  | 'control_flow' | 'depends_on' | 'contains';

export type Importance = 'critical' | 'high' | 'medium' | 'low';

export type CodemapStatus =
  | 'pending' | 'analyzing' | 'generating'
  | 'rendering' | 'completed' | 'failed';

// Core Types
export interface SourceLocation {
  file_path: string;
  line_start: number;
  line_end: number;
  column_start?: number;
  column_end?: number;
}

export interface CodeSnippet {
  code: string;
  language: string;
}

export interface CodemapNode {
  id: string;
  label: string;
  type: NodeType;
  location?: SourceLocation;
  description?: string;
  importance: Importance;
  snippet?: CodeSnippet;
  parent_id?: string;
  group?: string;
  metadata: Record<string, unknown>;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
}

export interface CodemapEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  label?: string;
  description?: string;
  weight: number;
  metadata: Record<string, unknown>;
}

export interface TraceSection {
  id: string;
  title: string;
  content: string;
  node_ids: string[];
  order: number;
}

export interface TraceGuide {
  title: string;
  summary: string;
  sections: TraceSection[];
  conclusion?: string;
}

export interface CodemapGraph {
  nodes: CodemapNode[];
  edges: CodemapEdge[];
  root_nodes: string[];
  clusters: Record<string, string[]>;
}

export interface CodemapRenderOutput {
  mermaid: string;
  json_graph: Record<string, unknown>;
  html?: string;
}

export interface Codemap {
  id: string;
  repo_url: string;
  repo_owner: string;
  repo_name: string;
  commit_hash?: string;
  query: string;
  analysis_type: string;
  title: string;
  description: string;
  graph: CodemapGraph;
  trace_guide: TraceGuide;
  render: CodemapRenderOutput;
  status: CodemapStatus;
  created_at: string;
  updated_at: string;
  generation_time_ms: number;
  model_used: string;
  is_public: boolean;
  share_token?: string;
}

// Request/Response Types
export interface CodemapGenerateRequest {
  repo_url: string;
  query: string;
  language?: string;
  analysis_type?: string;
  depth?: number;
  max_nodes?: number;
  excluded_dirs?: string[];
  excluded_files?: string[];
  included_dirs?: string[];
  included_files?: string[];
  file_types?: string[];
  provider?: string;
  model?: string;
  token?: string;
  type?: string;
}

export interface CodemapGenerateResponse {
  codemap_id: string;
  status: CodemapStatus;
  message: string;
  estimated_time_seconds?: number;
}

export interface CodemapProgress {
  codemap_id: string;
  status: CodemapStatus;
  progress_percent: number;
  current_step: string;
  details?: string;
  nodes_found: number;
  edges_found: number;
  files_analyzed: number;
  total_files: number;
}

// UI State Types
export interface CodemapViewState {
  selectedNodeId: string | null;
  hoveredNodeId: string | null;
  expandedSections: Set<string>;
  zoomLevel: number;
  panOffset: { x: number; y: number };
  viewMode: 'graph' | 'trace' | 'split';
  layoutType: 'hierarchical' | 'force' | 'radial';
}

export interface CodemapHistoryItem {
  id: string;
  query: string;
  title: string;
  created_at: string;
  repo_owner: string;
  repo_name: string;
}

// WebSocket Message Types
export interface CodemapWSMessage {
  type: 'progress' | 'complete' | 'error';
  data?: CodemapProgress | Codemap;
  message?: string;
}
