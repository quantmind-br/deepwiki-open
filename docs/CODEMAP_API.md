# Codemap API Documentation

## Overview

The Codemap API provides programmatic access to generate and retrieve AI-powered code maps. It supports both REST endpoints for synchronous operations and WebSocket for real-time progress updates.

## REST Endpoints

### Generate Codemap

Start a new codemap generation.

```http
POST /api/codemap/generate
Content-Type: application/json

{
  "repo_url": "https://github.com/owner/repo",
  "query": "How does authentication work?",
  "language": "en",
  "analysis_type": "auto",
  "depth": 3,
  "max_nodes": 50,
  "excluded_dirs": ["node_modules", ".git"],
  "excluded_files": ["*.lock"],
  "provider": "google",
  "model": "gemini-2.5-flash",
  "token": "optional_access_token",
  "type": "github"
}
```

**Request Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| repo_url | string | required | Repository URL |
| query | string | required | Natural language query |
| language | string | "en" | Language for generated text |
| analysis_type | string | "auto" | Type: auto, data_flow, control_flow, dependencies, call_graph, architecture |
| depth | int | 3 | Analysis depth (1-10) |
| max_nodes | int | 50 | Maximum nodes (10-200) |
| excluded_dirs | string[] | null | Directories to exclude |
| excluded_files | string[] | null | File patterns to exclude |
| provider | string | "google" | LLM provider |
| model | string | null | Specific model |
| token | string | null | Repository access token |
| type | string | "github" | Repository type: github, gitlab, bitbucket |

**Response**:

```json
{
  "codemap_id": "uuid",
  "status": "completed",
  "message": "Codemap generated successfully"
}
```

### Get Codemap

Retrieve a saved codemap by ID.

```http
GET /api/codemap/{codemap_id}
```

**Response**: Full Codemap object (see Data Models).

### List Codemaps

List saved codemaps with optional filtering.

```http
GET /api/codemap/list/all?repo_url=...&limit=50
```

**Query Parameters**:
- `repo_url` (optional): Filter by repository URL
- `limit` (optional): Maximum results (1-100, default 50)

**Response**:

```json
[
  {
    "id": "uuid",
    "title": "Authentication Flow",
    "query": "How does auth work?",
    "repo_url": "https://github.com/owner/repo",
    "repo_owner": "owner",
    "repo_name": "repo",
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "is_public": false
  }
]
```

### Get Repository Codemaps

Get codemaps for a specific repository.

```http
GET /api/codemap/repo/{owner}/{repo}?limit=20
```

### Share Codemap

Generate a share token for a codemap.

```http
POST /api/codemap/{codemap_id}/share
```

**Response**:

```json
{
  "share_token": "abc12345",
  "codemap_id": "uuid",
  "is_public": true
}
```

### Get Shared Codemap

Retrieve a codemap by share token.

```http
GET /api/codemap/shared/{share_token}
```

**Note**: Returns 404 if token is expired or codemap is not public.

### Delete Codemap

Delete a codemap.

```http
DELETE /api/codemap/{codemap_id}
```

### Export HTML

Export a codemap as standalone HTML.

```http
GET /api/codemap/{codemap_id}/export/html
```

Returns HTML file with `Content-Disposition: attachment`.

### Export Mermaid

Export a codemap as Mermaid diagram code.

```http
GET /api/codemap/{codemap_id}/export/mermaid
```

Returns plain text Mermaid code.

### Export JSON

Export codemap graph data as JSON.

```http
GET /api/codemap/{codemap_id}/export/json
```

## WebSocket Protocol

For real-time progress updates during generation.

### Connect

```
ws://localhost:8001/ws/codemap
```

### Generate Request (Client -> Server)

```json
{
  "repo_url": "https://github.com/owner/repo",
  "query": "How does authentication work?",
  "language": "en",
  "analysis_type": "auto",
  "depth": 3,
  "max_nodes": 50
}
```

### Progress Update (Server -> Client)

```json
{
  "type": "progress",
  "data": {
    "codemap_id": "uuid",
    "status": "analyzing",
    "progress_percent": 35,
    "current_step": "Analyzing code structure...",
    "nodes_found": 12,
    "edges_found": 8,
    "files_analyzed": 5,
    "total_files": 15
  }
}
```

### Completion (Server -> Client)

```json
{
  "type": "complete",
  "data": {
    "id": "uuid",
    "title": "...",
    "graph": { ... },
    "trace_guide": { ... },
    "render": { ... }
  }
}
```

### Error (Server -> Client)

```json
{
  "type": "error",
  "message": "Error description"
}
```

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /generate | 5/minute |
| GET /{id} | 60/minute |
| GET /list | 30/minute |
| POST /share | 10/minute |
| GET /export/* | 20/minute |

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Unauthorized (invalid token) |
| 403 | Forbidden (codemap not public) |
| 404 | Codemap not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Data Models

### Codemap

```typescript
interface Codemap {
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
  render: RenderOutput;
  
  status: CodemapStatus;
  created_at: string;
  updated_at: string;
  generation_time_ms: number;
  model_used: string;
  
  is_public: boolean;
  share_token?: string;
  share_expires_at?: string;
}
```

### CodemapGraph

```typescript
interface CodemapGraph {
  nodes: CodemapNode[];
  edges: CodemapEdge[];
  root_nodes: string[];
  clusters: Record<string, string[]>;
}
```

### CodemapNode

```typescript
interface CodemapNode {
  id: string;
  label: string;
  type: NodeType;
  location?: SourceLocation;
  description?: string;
  importance: Importance;
  snippet?: CodeSnippet;
  parent_id?: string;
  group?: string;
  metadata: Record<string, any>;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
}
```

### CodemapEdge

```typescript
interface CodemapEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  label?: string;
  description?: string;
  weight: number;
  metadata: Record<string, any>;
}
```

### TraceGuide

```typescript
interface TraceGuide {
  title: string;
  summary: string;
  sections: TraceSection[];
  conclusion?: string;
}

interface TraceSection {
  id: string;
  title: string;
  content: string;  // Markdown
  node_ids: string[];
  order: number;
}
```

## Enums

### NodeType

- `file`, `module`, `class`, `function`, `method`
- `variable`, `constant`, `interface`, `type`
- `endpoint`, `database`, `external`

### EdgeType

- `imports`, `exports`, `calls`, `extends`, `implements`
- `uses`, `returns`, `instantiates`
- `data_flow`, `control_flow`, `depends_on`, `contains`

### Importance

- `critical`, `high`, `medium`, `low`

### CodemapStatus

- `pending`, `analyzing`, `generating`, `rendering`
- `completed`, `failed`
