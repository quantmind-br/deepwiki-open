# DeepWiki Codemaps - Implementation Plan

> **Feature**: AI-powered interactive code maps for codebase understanding
> **Branch**: `feature/codemaps`
> **Created**: 2025-12-17
> **Status**: Planning

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Feature Overview](#2-feature-overview)
3. [Technical Architecture](#3-technical-architecture)
4. [Data Models](#4-data-models)
5. [Backend Implementation](#5-backend-implementation)
6. [Frontend Implementation](#6-frontend-implementation)
7. [API Specification](#7-api-specification)
8. [LLM Prompts & Strategies](#8-llm-prompts--strategies)
9. [Integration Points](#9-integration-points)
10. [Testing Strategy](#10-testing-strategy)
11. [Implementation Phases](#11-implementation-phases)
12. [Performance Considerations](#12-performance-considerations)
13. [Future Enhancements](#13-future-enhancements)

---

## 1. Executive Summary

### 1.1 Objective

Implement **Codemaps** - an AI-powered feature that generates interactive, hierarchical maps of codebases. Unlike static documentation, Codemaps are **just-in-time** artifacts generated for specific queries, showing:

- How code components relate to each other
- Data and control flow through the system
- Execution order for specific features
- Direct links to source code locations

### 1.2 Value Proposition

| Benefit | Description |
|---------|-------------|
| **Faster Onboarding** | New developers understand codebases in minutes, not days |
| **Better AI Context** | Provide structured context to AI agents for more accurate code generation |
| **Reduced Cognitive Load** | Visual maps replace manual code navigation |
| **Team Collaboration** | Shareable artifacts for code reviews and architecture discussions |

### 1.3 Differentiation from Existing DeepWiki Features

| Feature | DeepWiki (Current) | Codemaps (New) |
|---------|-------------------|----------------|
| **Purpose** | Static documentation | Dynamic exploration |
| **Generation** | Once per repo | On-demand per query |
| **Output** | Wiki pages | Interactive graphs |
| **Focus** | "What exists" | "How it works together" |
| **Granularity** | Symbol-level docs | Execution/data flow |

---

## 2. Feature Overview

### 2.1 User Stories

```
US-1: As a developer, I want to ask "How does authentication work?" and get
      a visual map showing all auth-related files, functions, and their connections.

US-2: As a developer, I want to click on any node in the map and jump directly
      to that location in the code.

US-3: As a developer, I want to read a "trace guide" explaining the flow in
      plain language alongside the visual map.

US-4: As a team lead, I want to share a codemap link with my team for
      onboarding or code review discussions.

US-5: As an AI agent user, I want to reference a codemap in my prompts
      for better context-aware code generation.
```

### 2.2 Core Capabilities

1. **Query-Based Generation**
   - User enters natural language query: "Trace how API requests are handled"
   - System analyzes codebase and generates relevant map

2. **Multi-Layer Analysis**
   - **Static Analysis**: AST parsing, import/export tracing, call graphs
   - **Semantic Analysis**: RAG-powered relevance scoring
   - **LLM Synthesis**: Natural language explanations and relationship inference

3. **Interactive Visualization**
   - Zoomable/pannable graph view
   - Expandable/collapsible node groups
   - Click-to-navigate to source code
   - Multiple layout options (hierarchical, force-directed, etc.)

4. **Trace Guide**
   - Markdown narrative explaining the flow
   - Organized by logical sections
   - Code snippets with syntax highlighting
   - Links to relevant nodes in the graph

### 2.3 Supported Analysis Types

| Analysis Type | Description | Example Query |
|---------------|-------------|---------------|
| **Data Flow** | How data moves through the system | "How does user data flow from registration to database?" |
| **Control Flow** | Execution paths and branching | "What happens when a payment fails?" |
| **Dependencies** | Import/export relationships | "What modules depend on the auth service?" |
| **Call Graph** | Function call hierarchies | "What functions are called when processing an order?" |
| **Architecture** | High-level system structure | "Show me the overall architecture of this service" |

---

## 3. Technical Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Browser)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ CodemapPanel │  │ GraphViewer  │  │ TraceGuide   │  │ NodeDetails │ │
│  │  - Query UI  │  │  - Mermaid   │  │  - Markdown  │  │  - Code     │ │
│  │  - History   │  │  - D3.js     │  │  - Sections  │  │  - Links    │ │
│  │  - Favorites │  │  - Zoom/Pan  │  │  - Expand    │  │  - Context  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │  HTTP/WebSocket Connection    │
                    │  - REST: /api/codemap/*       │
                    │  - WS: /ws/codemap            │
                    └───────────────┬───────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                           SERVER (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     API Layer (api/codemap_api.py)                  │ │
│  │  POST /api/codemap/generate    - Start codemap generation          │ │
│  │  GET  /api/codemap/{id}        - Retrieve saved codemap            │ │
│  │  GET  /api/codemap/list        - List user's codemaps              │ │
│  │  DELETE /api/codemap/{id}      - Delete codemap                    │ │
│  │  WS   /ws/codemap              - Stream generation progress        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────┴───────────────────────────────────┐ │
│  │                  Codemap Engine (api/codemap/)                      │ │
│  │                                                                      │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │ │
│  │  │   Analyzer      │  │   Generator     │  │   Renderer          │ │ │
│  │  │                 │  │                 │  │                     │ │ │
│  │  │ - AST Parser    │  │ - Node Builder  │  │ - Mermaid Export    │ │ │
│  │  │ - Import Tracer │  │ - Edge Builder  │  │ - JSON Export       │ │ │
│  │  │ - Call Graph    │  │ - Clustering    │  │ - Trace Guide Gen   │ │ │
│  │  │ - Symbol Index  │  │ - Layout Algo   │  │ - HTML Export       │ │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │ │
│  │           │                    │                    │              │ │
│  │           └────────────────────┼────────────────────┘              │ │
│  │                                │                                    │ │
│  │  ┌─────────────────────────────┴─────────────────────────────────┐ │ │
│  │  │                    RAG + LLM Pipeline                          │ │ │
│  │  │                                                                │ │ │
│  │  │  1. Query Understanding    - Parse user intent                 │ │ │
│  │  │  2. Semantic Retrieval     - Find relevant code chunks         │ │ │
│  │  │  3. Relationship Inference - LLM extracts connections          │ │ │
│  │  │  4. Trace Generation       - LLM writes explanations           │ │ │
│  │  │  5. Validation             - Verify links exist in code        │ │ │
│  │  └────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌────────────────────────────────┴───────────────────────────────────┐ │
│  │                     Storage Layer                                   │ │
│  │                                                                      │ │
│  │  ~/.adalflow/                                                       │ │
│  │  ├── repos/          - Cloned source code                          │ │
│  │  ├── databases/      - FAISS vector indices                        │ │
│  │  ├── codemaps/       - Saved codemap artifacts (NEW)               │ │
│  │  │   ├── {id}.json   - Codemap data                                │ │
│  │  │   └── {id}.md     - Trace guide markdown                        │ │
│  │  └── cache/          - Analysis cache                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Responsibilities

#### 3.2.1 Analyzer Component

**Purpose**: Extract structural information from source code

| Sub-Component | Responsibility | Technology |
|---------------|----------------|------------|
| `ASTParser` | Parse source files into AST | Python `ast`, `tree-sitter` |
| `ImportTracer` | Build import/export dependency graph | Static analysis |
| `CallGraphBuilder` | Map function/method calls | AST walking |
| `SymbolIndexer` | Index classes, functions, variables | Custom indexer |
| `FileClassifier` | Categorize files by type/purpose | Heuristics + LLM |

#### 3.2.2 Generator Component

**Purpose**: Build graph structures from analysis results

| Sub-Component | Responsibility | Technology |
|---------------|----------------|------------|
| `NodeBuilder` | Create graph nodes from symbols | Python dataclasses |
| `EdgeBuilder` | Create edges from relationships | Graph algorithms |
| `Clusterer` | Group related nodes | Community detection |
| `LayoutEngine` | Position nodes spatially | Force-directed, hierarchical |
| `Pruner` | Remove irrelevant nodes based on query | Relevance scoring |

#### 3.2.3 Renderer Component

**Purpose**: Generate output formats

| Sub-Component | Responsibility | Technology |
|---------------|----------------|------------|
| `MermaidRenderer` | Generate Mermaid diagram code | String templates |
| `JSONRenderer` | Export graph as JSON | Pydantic serialization |
| `TraceGuideWriter` | Generate markdown explanations | LLM + templates |
| `HTMLExporter` | Create standalone HTML view | Jinja2 templates |

### 3.3 Data Flow

```
┌──────────┐    ┌───────────────┐    ┌────────────────┐    ┌──────────────┐
│  Query   │───►│ Query Parser  │───►│ RAG Retrieval  │───►│  Relevant    │
│  Input   │    │ (Intent)      │    │ (Semantic)     │    │  Documents   │
└──────────┘    └───────────────┘    └────────────────┘    └──────┬───────┘
                                                                   │
┌──────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Static         │    │ LLM            │    │ Graph          │
│ Analysis       │───►│ Relationship   │───►│ Construction   │
│ (AST/Imports)  │    │ Inference      │    │ (Nodes/Edges)  │
└────────────────┘    └────────────────┘    └───────┬────────┘
                                                     │
┌────────────────────────────────────────────────────┘
│
▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Layout         │    │ Mermaid/JSON   │    │ Trace Guide    │
│ Calculation    │───►│ Rendering      │───►│ Generation     │
│                │    │                │    │ (LLM)          │
└────────────────┘    └────────────────┘    └───────┬────────┘
                                                     │
                                                     ▼
                                            ┌────────────────┐
                                            │ Final Codemap  │
                                            │ Artifact       │
                                            └────────────────┘
```

---

## 4. Data Models

### 4.1 Core Models (Python - Pydantic)

```python
# api/codemap/models.py

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# ============================================================================
# Enums
# ============================================================================

class NodeType(str, Enum):
    """Types of nodes in the codemap"""
    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    INTERFACE = "interface"
    TYPE = "type"
    ENDPOINT = "endpoint"
    DATABASE = "database"
    EXTERNAL = "external"

class EdgeType(str, Enum):
    """Types of relationships between nodes"""
    IMPORTS = "imports"
    EXPORTS = "exports"
    CALLS = "calls"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    USES = "uses"
    RETURNS = "returns"
    INSTANTIATES = "instantiates"
    DATA_FLOW = "data_flow"
    CONTROL_FLOW = "control_flow"
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"

class Importance(str, Enum):
    """Importance level of a node"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CodemapStatus(str, Enum):
    """Status of codemap generation"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================================================
# Node Models
# ============================================================================

class SourceLocation(BaseModel):
    """Exact location in source code"""
    file_path: str = Field(..., description="Relative path from repo root")
    line_start: int = Field(..., ge=1, description="Starting line number")
    line_end: int = Field(..., ge=1, description="Ending line number")
    column_start: Optional[int] = Field(None, ge=0)
    column_end: Optional[int] = Field(None, ge=0)

class CodeSnippet(BaseModel):
    """Code snippet for preview"""
    code: str = Field(..., description="Actual code content")
    language: str = Field(..., description="Programming language")
    highlighted: Optional[str] = Field(None, description="HTML-highlighted code")

class CodemapNode(BaseModel):
    """A node in the codemap graph"""
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label")
    type: NodeType = Field(..., description="Node type")

    # Location
    location: SourceLocation = Field(..., description="Source code location")

    # Metadata
    description: Optional[str] = Field(None, description="Brief description")
    importance: Importance = Field(Importance.MEDIUM)

    # Code preview
    snippet: Optional[CodeSnippet] = Field(None, description="Code preview")

    # Grouping
    parent_id: Optional[str] = Field(None, description="Parent node for nesting")
    group: Optional[str] = Field(None, description="Logical group name")

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Computed fields (set during layout)
    x: Optional[float] = Field(None, description="X position")
    y: Optional[float] = Field(None, description="Y position")
    width: Optional[float] = Field(None)
    height: Optional[float] = Field(None)

# ============================================================================
# Edge Models
# ============================================================================

class CodemapEdge(BaseModel):
    """An edge connecting two nodes"""
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Relationship type")

    # Display
    label: Optional[str] = Field(None, description="Edge label")

    # Metadata
    description: Optional[str] = Field(None, description="Relationship description")
    weight: float = Field(1.0, ge=0, description="Edge weight for layout")

    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)

# ============================================================================
# Trace Guide Models
# ============================================================================

class TraceSection(BaseModel):
    """A section in the trace guide"""
    id: str
    title: str
    content: str  # Markdown content
    node_ids: List[str] = Field(default_factory=list, description="Related nodes")
    order: int = Field(0, description="Display order")

class TraceGuide(BaseModel):
    """The narrative explanation of the codemap"""
    title: str
    summary: str  # Brief overview
    sections: List[TraceSection]
    conclusion: Optional[str] = None

# ============================================================================
# Codemap Models
# ============================================================================

class CodemapGraph(BaseModel):
    """The graph structure of a codemap"""
    nodes: List[CodemapNode]
    edges: List[CodemapEdge]

    # Graph metadata
    root_nodes: List[str] = Field(default_factory=list, description="Entry point nodes")
    clusters: Dict[str, List[str]] = Field(default_factory=dict, description="Node clusters")

class CodemapRenderOutput(BaseModel):
    """Rendered output formats"""
    mermaid: str = Field(..., description="Mermaid diagram code")
    json_graph: Dict[str, Any] = Field(..., description="JSON representation")
    html: Optional[str] = Field(None, description="Standalone HTML")

class Codemap(BaseModel):
    """Complete codemap artifact"""
    # Identity
    id: str = Field(..., description="Unique codemap ID")

    # Source
    repo_url: str
    repo_owner: str
    repo_name: str
    commit_hash: Optional[str] = None

    # Query
    query: str = Field(..., description="Original user query")
    analysis_type: str = Field("general", description="Type of analysis performed")

    # Content
    title: str
    description: str
    graph: CodemapGraph
    trace_guide: TraceGuide
    render: CodemapRenderOutput

    # Metadata
    status: CodemapStatus = CodemapStatus.COMPLETED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_time_ms: int = Field(0, description="Time to generate in milliseconds")
    model_used: str = Field("", description="LLM model used")

    # Sharing
    is_public: bool = False
    share_token: Optional[str] = None

# ============================================================================
# Request/Response Models
# ============================================================================

class CodemapGenerateRequest(BaseModel):
    """Request to generate a new codemap"""
    repo_url: str
    query: str

    # Options
    analysis_type: Optional[str] = Field("auto", description="Type: auto, data_flow, control_flow, dependencies, architecture")
    depth: Optional[int] = Field(3, ge=1, le=10, description="Analysis depth")
    max_nodes: Optional[int] = Field(50, ge=10, le=200, description="Maximum nodes")

    # Filters
    include_paths: Optional[List[str]] = Field(None, description="Paths to include")
    exclude_paths: Optional[List[str]] = Field(None, description="Paths to exclude")
    file_types: Optional[List[str]] = Field(None, description="File extensions to include")

    # Model selection
    provider: Optional[str] = Field("google", description="LLM provider")
    model: Optional[str] = Field(None, description="Specific model")

    # Auth
    token: Optional[str] = Field(None, description="Repo access token")
    type: Optional[str] = Field("github", description="Repo type: github, gitlab, bitbucket")

class CodemapGenerateResponse(BaseModel):
    """Response from codemap generation"""
    codemap_id: str
    status: CodemapStatus
    message: str
    estimated_time_seconds: Optional[int] = None

class CodemapProgress(BaseModel):
    """Progress update during generation"""
    codemap_id: str
    status: CodemapStatus
    progress_percent: int = Field(ge=0, le=100)
    current_step: str
    details: Optional[str] = None

    # Partial results
    nodes_found: int = 0
    edges_found: int = 0
    files_analyzed: int = 0
    total_files: int = 0
```

### 4.2 TypeScript Models (Frontend)

```typescript
// src/types/codemap.ts

// ============================================================================
// Enums
// ============================================================================

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

// ============================================================================
// Core Types
// ============================================================================

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
  highlighted?: string;
}

export interface CodemapNode {
  id: string;
  label: string;
  type: NodeType;
  location: SourceLocation;
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

export interface CodemapEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  label?: string;
  description?: string;
  weight: number;
  metadata: Record<string, any>;
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
  json_graph: Record<string, any>;
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

// ============================================================================
// Request/Response Types
// ============================================================================

export interface CodemapGenerateRequest {
  repo_url: string;
  query: string;
  analysis_type?: string;
  depth?: number;
  max_nodes?: number;
  include_paths?: string[];
  exclude_paths?: string[];
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

// ============================================================================
// UI State Types
// ============================================================================

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
```

---

## 5. Backend Implementation

### 5.1 File Structure

```
api/
├── codemap/
│   ├── __init__.py
│   ├── models.py              # Pydantic models (Section 4.1)
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── base.py            # Base analyzer interface
│   │   ├── python_analyzer.py # Python AST analysis
│   │   ├── javascript_analyzer.py # JS/TS analysis
│   │   ├── generic_analyzer.py # Fallback analyzer
│   │   ├── import_tracer.py   # Cross-file import resolution
│   │   └── call_graph.py      # Function call tracking
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── node_builder.py    # Create nodes from analysis
│   │   ├── edge_builder.py    # Create edges from relationships
│   │   ├── clusterer.py       # Group related nodes
│   │   ├── pruner.py          # Remove irrelevant nodes
│   │   └── layout.py          # Position calculation
│   ├── renderer/
│   │   ├── __init__.py
│   │   ├── mermaid.py         # Mermaid diagram generation
│   │   ├── json_export.py     # JSON export
│   │   └── html_export.py     # Standalone HTML
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── prompts.py         # LLM prompts
│   │   ├── query_parser.py    # Parse user intent
│   │   ├── relationship_extractor.py # Infer relationships
│   │   └── trace_writer.py    # Generate trace guide
│   ├── storage.py             # Codemap persistence
│   └── engine.py              # Main orchestrator
├── codemap_api.py             # REST endpoints
└── websocket_codemap.py       # WebSocket handler
```

### 5.2 Core Engine Implementation

```python
# api/codemap/engine.py

import asyncio
import logging
from typing import Optional, Callable, AsyncGenerator
from datetime import datetime
import uuid

from .models import (
    Codemap, CodemapGraph, CodemapGenerateRequest,
    CodemapProgress, CodemapStatus, TraceGuide
)
from .analyzer import get_analyzer
from .generator import NodeBuilder, EdgeBuilder, Clusterer, Pruner, LayoutEngine
from .renderer import MermaidRenderer, JSONRenderer
from .llm import QueryParser, RelationshipExtractor, TraceWriter
from .storage import CodemapStorage

from api.data_pipeline import DatabaseManager
from api.rag import RAG

logger = logging.getLogger(__name__)


class CodemapEngine:
    """
    Main orchestrator for codemap generation.

    Pipeline:
    1. Parse query to understand intent
    2. Retrieve relevant code via RAG
    3. Analyze code structure (AST, imports, calls)
    4. Build graph (nodes, edges)
    5. Prune and cluster
    6. Generate layout
    7. Render outputs (Mermaid, JSON)
    8. Generate trace guide
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        provider: str = "google",
        model: Optional[str] = None
    ):
        self.db_manager = db_manager
        self.provider = provider
        self.model = model

        # Initialize components
        self.query_parser = QueryParser(provider, model)
        self.relationship_extractor = RelationshipExtractor(provider, model)
        self.trace_writer = TraceWriter(provider, model)

        self.node_builder = NodeBuilder()
        self.edge_builder = EdgeBuilder()
        self.clusterer = Clusterer()
        self.pruner = Pruner()
        self.layout_engine = LayoutEngine()

        self.mermaid_renderer = MermaidRenderer()
        self.json_renderer = JSONRenderer()

        self.storage = CodemapStorage()

    async def generate(
        self,
        request: CodemapGenerateRequest,
        progress_callback: Optional[Callable[[CodemapProgress], None]] = None
    ) -> Codemap:
        """
        Generate a complete codemap from a user query.

        Args:
            request: Generation request with query and options
            progress_callback: Optional callback for progress updates

        Returns:
            Complete Codemap object
        """
        codemap_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            # Step 1: Parse query
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.ANALYZING,
                progress_percent=5,
                current_step="Parsing query...",
            ))

            query_intent = await self.query_parser.parse(request.query)
            analysis_type = request.analysis_type if request.analysis_type != "auto" else query_intent.suggested_type

            # Step 2: Load repository and RAG
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.ANALYZING,
                progress_percent=10,
                current_step="Loading repository...",
            ))

            repo_info = self._parse_repo_url(request.repo_url)
            local_db = await self.db_manager.get_or_create_database(
                repo_url=request.repo_url,
                token=request.token,
                repo_type=request.type
            )

            # Step 3: Retrieve relevant documents via RAG
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.ANALYZING,
                progress_percent=20,
                current_step="Finding relevant code...",
            ))

            rag = RAG(local_db)
            relevant_docs = await rag.retrieve(
                query=request.query,
                top_k=request.max_nodes * 2  # Retrieve more, prune later
            )

            # Step 4: Static code analysis
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.ANALYZING,
                progress_percent=35,
                current_step="Analyzing code structure...",
            ))

            analyzer = get_analyzer(repo_info.language)
            analysis_result = await analyzer.analyze(
                documents=relevant_docs,
                repo_path=local_db.repo_path,
                include_paths=request.include_paths,
                exclude_paths=request.exclude_paths,
                depth=request.depth
            )

            # Step 5: LLM relationship extraction
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.GENERATING,
                progress_percent=50,
                current_step="Inferring relationships...",
            ))

            llm_relationships = await self.relationship_extractor.extract(
                query=request.query,
                analysis=analysis_result,
                query_intent=query_intent
            )

            # Step 6: Build graph
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.GENERATING,
                progress_percent=65,
                current_step="Building graph...",
            ))

            nodes = self.node_builder.build(analysis_result, query_intent)
            edges = self.edge_builder.build(analysis_result, llm_relationships)

            # Step 7: Prune and cluster
            nodes, edges = self.pruner.prune(
                nodes=nodes,
                edges=edges,
                query_intent=query_intent,
                max_nodes=request.max_nodes
            )

            clusters = self.clusterer.cluster(nodes, edges)

            # Step 8: Calculate layout
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.RENDERING,
                progress_percent=75,
                current_step="Calculating layout...",
            ))

            nodes = self.layout_engine.calculate(
                nodes=nodes,
                edges=edges,
                layout_type=query_intent.preferred_layout
            )

            graph = CodemapGraph(
                nodes=nodes,
                edges=edges,
                root_nodes=[n.id for n in nodes if n.parent_id is None][:5],
                clusters=clusters
            )

            # Step 9: Render outputs
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.RENDERING,
                progress_percent=85,
                current_step="Rendering diagram...",
            ))

            mermaid_code = self.mermaid_renderer.render(graph, query_intent)
            json_graph = self.json_renderer.render(graph)

            # Step 10: Generate trace guide
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.RENDERING,
                progress_percent=95,
                current_step="Writing trace guide...",
            ))

            trace_guide = await self.trace_writer.write(
                query=request.query,
                graph=graph,
                analysis=analysis_result,
                query_intent=query_intent
            )

            # Build final codemap
            end_time = datetime.utcnow()
            generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            codemap = Codemap(
                id=codemap_id,
                repo_url=request.repo_url,
                repo_owner=repo_info.owner,
                repo_name=repo_info.name,
                commit_hash=local_db.commit_hash,
                query=request.query,
                analysis_type=analysis_type,
                title=self._generate_title(request.query, query_intent),
                description=trace_guide.summary,
                graph=graph,
                trace_guide=trace_guide,
                render=CodemapRenderOutput(
                    mermaid=mermaid_code,
                    json_graph=json_graph
                ),
                status=CodemapStatus.COMPLETED,
                generation_time_ms=generation_time_ms,
                model_used=self.model or "default"
            )

            # Save to storage
            await self.storage.save(codemap)

            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.COMPLETED,
                progress_percent=100,
                current_step="Complete!",
                nodes_found=len(nodes),
                edges_found=len(edges)
            ))

            return codemap

        except Exception as e:
            logger.error(f"Codemap generation failed: {e}", exc_info=True)
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.FAILED,
                progress_percent=0,
                current_step="Failed",
                details=str(e)
            ))
            raise

    async def _emit_progress(
        self,
        callback: Optional[Callable[[CodemapProgress], None]],
        progress: CodemapProgress
    ):
        """Emit progress update if callback provided"""
        if callback:
            if asyncio.iscoroutinefunction(callback):
                await callback(progress)
            else:
                callback(progress)

    def _parse_repo_url(self, url: str):
        """Parse repository URL to extract owner, name, etc."""
        # Implementation to extract repo info from URL
        pass

    def _generate_title(self, query: str, query_intent) -> str:
        """Generate a title for the codemap"""
        # Summarize query into a short title
        pass
```

### 5.3 Analyzer Implementation

```python
# api/codemap/analyzer/python_analyzer.py

import ast
import os
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..models import SourceLocation, NodeType


@dataclass
class SymbolInfo:
    """Information about a code symbol"""
    name: str
    type: NodeType
    location: SourceLocation
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)  # For classes
    parameters: List[str] = field(default_factory=list)  # For functions
    return_type: Optional[str] = None


@dataclass
class ImportInfo:
    """Information about an import statement"""
    module: str
    names: List[str]  # Imported names (empty for 'import module')
    alias: Optional[str] = None
    location: SourceLocation = None
    is_relative: bool = False


@dataclass
class CallInfo:
    """Information about a function call"""
    caller: str  # Function making the call
    callee: str  # Function being called
    location: SourceLocation = None
    arguments: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete analysis result for a file or set of files"""
    symbols: List[SymbolInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    calls: List[CallInfo] = field(default_factory=list)
    file_path: str = ""
    language: str = "python"


class PythonAnalyzer:
    """
    Analyzes Python source code using AST.

    Extracts:
    - Classes, functions, methods
    - Import relationships
    - Function calls
    - Inheritance hierarchies
    """

    def __init__(self):
        self.current_file: str = ""
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None

    async def analyze(
        self,
        documents: List,
        repo_path: str,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        depth: int = 3
    ) -> Dict[str, AnalysisResult]:
        """
        Analyze multiple documents from a repository.

        Args:
            documents: List of Document objects from RAG
            repo_path: Path to cloned repository
            include_paths: Paths to include
            exclude_paths: Paths to exclude
            depth: Analysis depth

        Returns:
            Dict mapping file paths to AnalysisResult
        """
        results = {}

        for doc in documents:
            file_path = doc.meta_data.get("file_path", "")
            if not file_path.endswith(".py"):
                continue

            if self._should_skip(file_path, include_paths, exclude_paths):
                continue

            full_path = os.path.join(repo_path, file_path)
            if os.path.exists(full_path):
                try:
                    result = self.analyze_file(full_path, file_path)
                    results[file_path] = result
                except Exception as e:
                    # Log but continue with other files
                    pass

        # Resolve cross-file references
        self._resolve_imports(results, repo_path)

        return results

    def analyze_file(self, full_path: str, relative_path: str) -> AnalysisResult:
        """Analyze a single Python file"""
        self.current_file = relative_path

        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return AnalysisResult(file_path=relative_path)

        result = AnalysisResult(file_path=relative_path)

        # Extract all information
        result.symbols = self._extract_symbols(tree)
        result.imports = self._extract_imports(tree)
        result.calls = self._extract_calls(tree)

        return result

    def _extract_symbols(self, tree: ast.AST) -> List[SymbolInfo]:
        """Extract class and function definitions"""
        symbols = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append(SymbolInfo(
                    name=node.name,
                    type=NodeType.CLASS,
                    location=SourceLocation(
                        file_path=self.current_file,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        column_start=node.col_offset,
                        column_end=node.end_col_offset
                    ),
                    docstring=ast.get_docstring(node),
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    bases=[self._get_name(b) for b in node.bases]
                ))

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Determine if method or function
                is_method = self._is_inside_class(node, tree)

                symbols.append(SymbolInfo(
                    name=node.name,
                    type=NodeType.METHOD if is_method else NodeType.FUNCTION,
                    location=SourceLocation(
                        file_path=self.current_file,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        column_start=node.col_offset,
                        column_end=node.end_col_offset
                    ),
                    docstring=ast.get_docstring(node),
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    parameters=[arg.arg for arg in node.args.args],
                    return_type=self._get_annotation(node.returns)
                ))

        return symbols

    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """Extract import statements"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[],
                        alias=alias.asname,
                        location=SourceLocation(
                            file_path=self.current_file,
                            line_start=node.lineno,
                            line_end=node.lineno
                        )
                    ))

            elif isinstance(node, ast.ImportFrom):
                imports.append(ImportInfo(
                    module=node.module or "",
                    names=[alias.name for alias in node.names],
                    alias=node.names[0].asname if len(node.names) == 1 else None,
                    location=SourceLocation(
                        file_path=self.current_file,
                        line_start=node.lineno,
                        line_end=node.lineno
                    ),
                    is_relative=node.level > 0
                ))

        return imports

    def _extract_calls(self, tree: ast.AST) -> List[CallInfo]:
        """Extract function calls"""
        calls = []

        class CallVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.current_func = None

            def visit_FunctionDef(self, node):
                old_func = self.current_func
                self.current_func = node.name
                self.generic_visit(node)
                self.current_func = old_func

            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)

            def visit_Call(self, node):
                if self.current_func:
                    callee = self.analyzer._get_call_name(node)
                    if callee:
                        calls.append(CallInfo(
                            caller=self.current_func,
                            callee=callee,
                            location=SourceLocation(
                                file_path=self.analyzer.current_file,
                                line_start=node.lineno,
                                line_end=node.lineno
                            )
                        ))
                self.generic_visit(node)

        visitor = CallVisitor(self)
        visitor.visit(tree)

        return calls

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Get the name of a called function"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handle obj.method() calls
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None

    def _get_decorator_name(self, node) -> str:
        """Get decorator name as string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return ""

    def _get_name(self, node) -> str:
        """Get name from various node types"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        return ""

    def _get_annotation(self, node) -> Optional[str]:
        """Get type annotation as string"""
        if node is None:
            return None
        return self._get_name(node)

    def _is_inside_class(self, func_node, tree) -> bool:
        """Check if a function is a method inside a class"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item is func_node:
                        return True
        return False

    def _should_skip(
        self,
        path: str,
        include_paths: Optional[List[str]],
        exclude_paths: Optional[List[str]]
    ) -> bool:
        """Check if path should be skipped"""
        if exclude_paths:
            for pattern in exclude_paths:
                if pattern in path:
                    return True

        if include_paths:
            for pattern in include_paths:
                if pattern in path:
                    return False
            return True

        return False

    def _resolve_imports(self, results: Dict[str, AnalysisResult], repo_path: str):
        """Resolve imports to actual file paths"""
        # Build module to file mapping
        module_map = {}
        for file_path in results.keys():
            module_name = file_path.replace("/", ".").replace(".py", "")
            module_map[module_name] = file_path

        # Resolve each import
        for result in results.values():
            for imp in result.imports:
                if imp.module in module_map:
                    imp.resolved_path = module_map[imp.module]
```

### 5.4 LLM Prompts

```python
# api/codemap/llm/prompts.py

QUERY_PARSER_SYSTEM = """You are a code analysis query parser. Given a user's natural language query about a codebase, extract the intent and parameters.

Output JSON with:
- intent: The primary goal (understand_flow, find_dependencies, trace_data, architecture_overview, debug_issue)
- focus_areas: List of code areas to focus on (e.g., ["authentication", "database", "api"])
- analysis_type: Suggested analysis type (data_flow, control_flow, dependencies, call_graph, architecture)
- preferred_layout: Graph layout type (hierarchical, force, radial)
- depth: Suggested analysis depth (1-5, where 5 is deepest)
- keywords: Important terms to search for
"""

QUERY_PARSER_USER = """Parse this query about a codebase:

Query: {query}

Repository context:
- Language: {language}
- Main files: {main_files}

Output the analysis intent as JSON."""


RELATIONSHIP_EXTRACTOR_SYSTEM = """You are a code relationship analyzer. Given code analysis results and a user query, identify relationships between code components that are relevant to answering the query.

For each relationship, specify:
- source: The source component (file:function or file:class)
- target: The target component
- type: Relationship type (calls, imports, extends, implements, uses, data_flow, control_flow)
- description: Brief description of the relationship
- importance: How important this relationship is for the query (critical, high, medium, low)

Focus on relationships that help explain the answer to the user's query. Prioritize:
1. Direct relationships mentioned in the query
2. Data flow paths
3. Control flow paths
4. Key architectural connections
"""

RELATIONSHIP_EXTRACTOR_USER = """Analyze relationships for this query:

Query: {query}

Analysis Results:
{analysis_json}

Identified Symbols:
{symbols_list}

Identified Imports:
{imports_list}

Identified Calls:
{calls_list}

Extract the most relevant relationships as JSON array."""


TRACE_GUIDE_SYSTEM = """You are a technical documentation writer specializing in code explanations. Given a codemap (graph of code relationships) and the original query, write a clear, structured "trace guide" that explains how the code works.

Structure your response as:
1. **Summary**: 2-3 sentence overview answering the query
2. **Sections**: Logical sections explaining different parts of the flow
   - Each section should have a title, explanation, and reference relevant nodes
3. **Conclusion**: Key takeaways and important notes

Guidelines:
- Use clear, technical but accessible language
- Reference specific files, functions, and line numbers
- Explain the "why" not just the "what"
- Highlight important patterns or potential issues
- Use code snippets where helpful
"""

TRACE_GUIDE_USER = """Write a trace guide for this codemap:

Original Query: {query}

Graph Summary:
- Nodes: {node_count}
- Edges: {edge_count}
- Root nodes: {root_nodes}

Nodes:
{nodes_json}

Edges:
{edges_json}

Clusters:
{clusters_json}

Write a comprehensive trace guide in markdown format."""


MERMAID_OPTIMIZATION_SYSTEM = """You are a diagram optimization expert. Given a Mermaid diagram, optimize it for readability while preserving all information.

Optimization rules:
1. Group related nodes into subgraphs
2. Use consistent styling for node types
3. Simplify long labels (keep under 30 chars)
4. Arrange for top-to-bottom or left-to-right flow
5. Add meaningful link labels
6. Use appropriate shapes for node types:
   - Classes: rectangles
   - Functions: rounded rectangles
   - Files: parallelograms
   - External: circles
"""
```

### 5.5 WebSocket Handler

```python
# api/websocket_codemap.py

import json
import logging
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from api.codemap.models import CodemapGenerateRequest, CodemapProgress, CodemapStatus
from api.codemap.engine import CodemapEngine
from api.data_pipeline import DatabaseManager

logger = logging.getLogger(__name__)


class CodemapWebSocketHandler:
    """
    WebSocket handler for real-time codemap generation.

    Protocol:
    1. Client connects to /ws/codemap
    2. Client sends CodemapGenerateRequest as JSON
    3. Server streams CodemapProgress updates
    4. Server sends final Codemap or error
    5. Connection closes
    """

    def __init__(self):
        self.db_manager = DatabaseManager()

    async def handle(self, websocket: WebSocket):
        """Handle a WebSocket connection for codemap generation"""
        await websocket.accept()

        try:
            # Receive generation request
            data = await websocket.receive_text()
            request_dict = json.loads(data)

            try:
                request = CodemapGenerateRequest(**request_dict)
            except ValidationError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid request: {e}"
                })
                await websocket.close()
                return

            # Create engine
            engine = CodemapEngine(
                db_manager=self.db_manager,
                provider=request.provider or "google",
                model=request.model
            )

            # Progress callback
            async def send_progress(progress: CodemapProgress):
                await websocket.send_json({
                    "type": "progress",
                    "data": progress.model_dump()
                })

            # Generate codemap
            try:
                codemap = await engine.generate(
                    request=request,
                    progress_callback=send_progress
                )

                # Send final result
                await websocket.send_json({
                    "type": "complete",
                    "data": codemap.model_dump()
                })

            except Exception as e:
                logger.error(f"Codemap generation error: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

        except WebSocketDisconnect:
            logger.info("Client disconnected from codemap WebSocket")
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid JSON"
            })
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
            except:
                pass
        finally:
            try:
                await websocket.close()
            except:
                pass


# FastAPI route registration
def register_codemap_websocket(app):
    """Register the codemap WebSocket endpoint"""
    handler = CodemapWebSocketHandler()

    @app.websocket("/ws/codemap")
    async def codemap_websocket(websocket: WebSocket):
        await handler.handle(websocket)
```

---

## 6. Frontend Implementation

### 6.1 File Structure

```
src/
├── components/
│   └── codemap/
│       ├── index.ts                    # Exports
│       ├── CodemapPanel.tsx            # Main panel/sidebar
│       ├── CodemapQueryInput.tsx       # Query input with suggestions
│       ├── CodemapViewer.tsx           # Main viewer container
│       ├── CodemapGraph.tsx            # Graph visualization
│       ├── CodemapMermaid.tsx          # Mermaid-based rendering
│       ├── TraceGuide.tsx              # Trace guide panel
│       ├── TraceSection.tsx            # Individual trace section
│       ├── NodeInspector.tsx           # Node details panel
│       ├── CodemapProgress.tsx         # Generation progress UI
│       ├── CodemapHistory.tsx          # History list
│       ├── CodemapToolbar.tsx          # View controls
│       └── CodemapShare.tsx            # Share dialog
├── hooks/
│   └── codemap/
│       ├── useCodemap.ts               # Main codemap hook
│       ├── useCodemapGeneration.ts     # Generation with WebSocket
│       ├── useCodemapNavigation.ts     # Graph navigation
│       └── useCodemapStorage.ts        # Local storage
├── types/
│   └── codemap.ts                      # TypeScript types (Section 4.2)
├── utils/
│   └── codemap/
│       ├── codemapClient.ts            # API/WebSocket client
│       ├── graphLayout.ts              # Layout utilities
│       └── mermaidBuilder.ts           # Mermaid code helpers
└── app/
    └── [owner]/
        └── [repo]/
            └── codemap/
                └── page.tsx            # Codemap page route
```

### 6.2 Main Components

#### CodemapPanel.tsx
```tsx
// src/components/codemap/CodemapPanel.tsx

'use client';

import React, { useState, useCallback } from 'react';
import { Codemap, CodemapGenerateRequest, CodemapProgress } from '@/types/codemap';
import { useCodemapGeneration } from '@/hooks/codemap/useCodemapGeneration';
import { CodemapQueryInput } from './CodemapQueryInput';
import { CodemapViewer } from './CodemapViewer';
import { CodemapProgress as ProgressDisplay } from './CodemapProgress';
import { CodemapHistory } from './CodemapHistory';

interface CodemapPanelProps {
  repoUrl: string;
  repoOwner: string;
  repoName: string;
  repoType: string;
  token?: string;
}

export function CodemapPanel({
  repoUrl,
  repoOwner,
  repoName,
  repoType,
  token
}: CodemapPanelProps) {
  const [currentCodemap, setCurrentCodemap] = useState<Codemap | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const {
    isGenerating,
    progress,
    error,
    generate
  } = useCodemapGeneration();

  const handleGenerate = useCallback(async (query: string, options?: Partial<CodemapGenerateRequest>) => {
    const request: CodemapGenerateRequest = {
      repo_url: repoUrl,
      query,
      type: repoType,
      token,
      ...options
    };

    const codemap = await generate(request);
    if (codemap) {
      setCurrentCodemap(codemap);
    }
  }, [repoUrl, repoType, token, generate]);

  const handleSelectFromHistory = useCallback((codemap: Codemap) => {
    setCurrentCodemap(codemap);
    setShowHistory(false);
  }, []);

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Codemap
        </h2>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
        >
          {showHistory ? 'New Query' : 'History'}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {showHistory ? (
          <CodemapHistory
            repoOwner={repoOwner}
            repoName={repoName}
            onSelect={handleSelectFromHistory}
          />
        ) : isGenerating ? (
          <ProgressDisplay progress={progress} />
        ) : currentCodemap ? (
          <CodemapViewer
            codemap={currentCodemap}
            onNewQuery={() => setCurrentCodemap(null)}
          />
        ) : (
          <div className="p-4">
            <CodemapQueryInput
              onSubmit={handleGenerate}
              isLoading={isGenerating}
              repoOwner={repoOwner}
              repoName={repoName}
            />

            {error && (
              <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-lg">
                {error}
              </div>
            )}

            {/* Query suggestions */}
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
                Suggested queries
              </h3>
              <div className="space-y-2">
                {getDefaultQueries(repoOwner, repoName).map((query, i) => (
                  <button
                    key={i}
                    onClick={() => handleGenerate(query)}
                    className="w-full text-left p-3 text-sm bg-gray-50 dark:bg-gray-800
                             hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg
                             text-gray-700 dark:text-gray-300 transition-colors"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getDefaultQueries(owner: string, repo: string): string[] {
  return [
    'Show me the overall architecture',
    'How does the authentication flow work?',
    'Trace how API requests are handled',
    'What are the main entry points?',
    'Show database interactions',
  ];
}
```

#### CodemapViewer.tsx
```tsx
// src/components/codemap/CodemapViewer.tsx

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Codemap, CodemapNode, CodemapViewState } from '@/types/codemap';
import { CodemapGraph } from './CodemapGraph';
import { TraceGuide } from './TraceGuide';
import { NodeInspector } from './NodeInspector';
import { CodemapToolbar } from './CodemapToolbar';
import { CodemapMermaid } from './CodemapMermaid';

interface CodemapViewerProps {
  codemap: Codemap;
  onNewQuery: () => void;
}

export function CodemapViewer({ codemap, onNewQuery }: CodemapViewerProps) {
  const [viewState, setViewState] = useState<CodemapViewState>({
    selectedNodeId: null,
    hoveredNodeId: null,
    expandedSections: new Set(),
    zoomLevel: 1,
    panOffset: { x: 0, y: 0 },
    viewMode: 'split',
    layoutType: 'hierarchical'
  });

  const selectedNode = useMemo(() => {
    if (!viewState.selectedNodeId) return null;
    return codemap.graph.nodes.find(n => n.id === viewState.selectedNodeId) || null;
  }, [codemap.graph.nodes, viewState.selectedNodeId]);

  const handleNodeSelect = useCallback((nodeId: string | null) => {
    setViewState(prev => ({ ...prev, selectedNodeId: nodeId }));
  }, []);

  const handleNodeHover = useCallback((nodeId: string | null) => {
    setViewState(prev => ({ ...prev, hoveredNodeId: nodeId }));
  }, []);

  const handleZoom = useCallback((delta: number) => {
    setViewState(prev => ({
      ...prev,
      zoomLevel: Math.max(0.25, Math.min(3, prev.zoomLevel + delta))
    }));
  }, []);

  const handleViewModeChange = useCallback((mode: CodemapViewState['viewMode']) => {
    setViewState(prev => ({ ...prev, viewMode: mode }));
  }, []);

  const handleLayoutChange = useCallback((layout: CodemapViewState['layoutType']) => {
    setViewState(prev => ({ ...prev, layoutType: layout }));
  }, []);

  const handleSectionToggle = useCallback((sectionId: string) => {
    setViewState(prev => {
      const next = new Set(prev.expandedSections);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return { ...prev, expandedSections: next };
    });
  }, []);

  const handleNavigateToNode = useCallback((nodeId: string) => {
    // Find node and open file at location
    const node = codemap.graph.nodes.find(n => n.id === nodeId);
    if (node) {
      // This would integrate with IDE or file viewer
      console.log('Navigate to:', node.location);
      handleNodeSelect(nodeId);
    }
  }, [codemap.graph.nodes, handleNodeSelect]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <CodemapToolbar
        codemap={codemap}
        viewState={viewState}
        onViewModeChange={handleViewModeChange}
        onLayoutChange={handleLayoutChange}
        onZoomIn={() => handleZoom(0.25)}
        onZoomOut={() => handleZoom(-0.25)}
        onZoomReset={() => setViewState(prev => ({ ...prev, zoomLevel: 1 }))}
        onNewQuery={onNewQuery}
      />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph view */}
        {(viewState.viewMode === 'graph' || viewState.viewMode === 'split') && (
          <div className={`${viewState.viewMode === 'split' ? 'w-1/2' : 'w-full'} h-full border-r dark:border-gray-700`}>
            <CodemapMermaid
              mermaidCode={codemap.render.mermaid}
              nodes={codemap.graph.nodes}
              selectedNodeId={viewState.selectedNodeId}
              hoveredNodeId={viewState.hoveredNodeId}
              zoomLevel={viewState.zoomLevel}
              onNodeSelect={handleNodeSelect}
              onNodeHover={handleNodeHover}
            />
          </div>
        )}

        {/* Trace guide */}
        {(viewState.viewMode === 'trace' || viewState.viewMode === 'split') && (
          <div className={`${viewState.viewMode === 'split' ? 'w-1/2' : 'w-full'} h-full overflow-y-auto`}>
            <TraceGuide
              traceGuide={codemap.trace_guide}
              nodes={codemap.graph.nodes}
              expandedSections={viewState.expandedSections}
              selectedNodeId={viewState.selectedNodeId}
              onSectionToggle={handleSectionToggle}
              onNodeNavigate={handleNavigateToNode}
            />
          </div>
        )}
      </div>

      {/* Node inspector (slide-out panel) */}
      {selectedNode && (
        <NodeInspector
          node={selectedNode}
          edges={codemap.graph.edges.filter(
            e => e.source === selectedNode.id || e.target === selectedNode.id
          )}
          allNodes={codemap.graph.nodes}
          onClose={() => handleNodeSelect(null)}
          onNavigate={handleNavigateToNode}
        />
      )}
    </div>
  );
}
```

#### CodemapMermaid.tsx
```tsx
// src/components/codemap/CodemapMermaid.tsx

'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import mermaid from 'mermaid';
import svgPanZoom from 'svg-pan-zoom';
import { CodemapNode } from '@/types/codemap';

interface CodemapMermaidProps {
  mermaidCode: string;
  nodes: CodemapNode[];
  selectedNodeId: string | null;
  hoveredNodeId: string | null;
  zoomLevel: number;
  onNodeSelect: (nodeId: string | null) => void;
  onNodeHover: (nodeId: string | null) => void;
}

export function CodemapMermaid({
  mermaidCode,
  nodes,
  selectedNodeId,
  hoveredNodeId,
  zoomLevel,
  onNodeSelect,
  onNodeHover
}: CodemapMermaidProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const panZoomRef = useRef<SvgPanZoom.Instance | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        primaryColor: '#f8f4e6',
        primaryTextColor: '#333',
        primaryBorderColor: '#9b7cb9',
        lineColor: '#9b7cb9',
        secondaryColor: '#fff5e6',
        tertiaryColor: '#f0f0f0',
      },
      flowchart: {
        useMaxWidth: false,
        htmlLabels: true,
        curve: 'basis'
      },
      securityLevel: 'loose'
    });
  }, []);

  // Render diagram
  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || !mermaidCode) return;

      try {
        setError(null);

        // Clear previous content
        containerRef.current.innerHTML = '';

        // Render mermaid
        const { svg } = await mermaid.render(
          `codemap-${Date.now()}`,
          mermaidCode
        );

        containerRef.current.innerHTML = svg;

        // Get SVG element
        const svgElement = containerRef.current.querySelector('svg');
        if (svgElement) {
          svgRef.current = svgElement as SVGSVGElement;

          // Initialize pan-zoom
          if (panZoomRef.current) {
            panZoomRef.current.destroy();
          }

          panZoomRef.current = svgPanZoom(svgElement, {
            zoomEnabled: true,
            controlIconsEnabled: false,
            fit: true,
            center: true,
            minZoom: 0.25,
            maxZoom: 4,
            zoomScaleSensitivity: 0.3
          });

          // Add click handlers to nodes
          setupNodeInteractions(svgElement);
        }
      } catch (err) {
        console.error('Mermaid render error:', err);
        setError('Failed to render diagram');
      }
    };

    renderDiagram();

    return () => {
      if (panZoomRef.current) {
        panZoomRef.current.destroy();
        panZoomRef.current = null;
      }
    };
  }, [mermaidCode]);

  // Setup node interactions
  const setupNodeInteractions = useCallback((svg: SVGSVGElement) => {
    // Find all node groups
    const nodeGroups = svg.querySelectorAll('.node');

    nodeGroups.forEach(group => {
      const nodeId = group.id || group.getAttribute('data-id');
      if (!nodeId) return;

      // Click handler
      group.addEventListener('click', (e) => {
        e.stopPropagation();
        onNodeSelect(nodeId);
      });

      // Hover handlers
      group.addEventListener('mouseenter', () => {
        onNodeHover(nodeId);
      });

      group.addEventListener('mouseleave', () => {
        onNodeHover(null);
      });

      // Style for interactivity
      (group as HTMLElement).style.cursor = 'pointer';
    });

    // Click on background deselects
    svg.addEventListener('click', () => {
      onNodeSelect(null);
    });
  }, [onNodeSelect, onNodeHover]);

  // Update zoom level
  useEffect(() => {
    if (panZoomRef.current) {
      panZoomRef.current.zoom(zoomLevel);
    }
  }, [zoomLevel]);

  // Highlight selected/hovered nodes
  useEffect(() => {
    if (!svgRef.current) return;

    const nodeGroups = svgRef.current.querySelectorAll('.node');

    nodeGroups.forEach(group => {
      const nodeId = group.id || group.getAttribute('data-id');
      const rect = group.querySelector('rect, polygon, circle');

      if (rect) {
        if (nodeId === selectedNodeId) {
          rect.setAttribute('stroke', '#3b82f6');
          rect.setAttribute('stroke-width', '3');
        } else if (nodeId === hoveredNodeId) {
          rect.setAttribute('stroke', '#60a5fa');
          rect.setAttribute('stroke-width', '2');
        } else {
          rect.setAttribute('stroke', '#9b7cb9');
          rect.setAttribute('stroke-width', '1');
        }
      }
    });
  }, [selectedNodeId, hoveredNodeId]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-800">
        <div className="text-center p-4">
          <p className="text-red-500 mb-2">{error}</p>
          <pre className="text-xs text-gray-500 bg-gray-100 dark:bg-gray-700 p-2 rounded max-w-md overflow-auto">
            {mermaidCode.slice(0, 500)}...
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-white dark:bg-gray-900">
      <div
        ref={containerRef}
        className="w-full h-full overflow-hidden"
      />

      {/* Zoom controls */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-2">
        <button
          onClick={() => panZoomRef.current?.zoomIn()}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          title="Zoom In"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12M6 12h12" />
          </svg>
        </button>
        <button
          onClick={() => panZoomRef.current?.zoomOut()}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          title="Zoom Out"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12h12" />
          </svg>
        </button>
        <button
          onClick={() => panZoomRef.current?.resetZoom()}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          title="Reset View"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </button>
      </div>
    </div>
  );
}
```

### 6.3 Hooks

```typescript
// src/hooks/codemap/useCodemapGeneration.ts

import { useState, useCallback, useRef } from 'react';
import {
  Codemap,
  CodemapGenerateRequest,
  CodemapProgress,
  CodemapStatus
} from '@/types/codemap';

interface UseCodemapGenerationResult {
  isGenerating: boolean;
  progress: CodemapProgress | null;
  error: string | null;
  generate: (request: CodemapGenerateRequest) => Promise<Codemap | null>;
  cancel: () => void;
}

export function useCodemapGeneration(): UseCodemapGenerationResult {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState<CodemapProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const cancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsGenerating(false);
    setProgress(null);
  }, []);

  const generate = useCallback(async (request: CodemapGenerateRequest): Promise<Codemap | null> => {
    return new Promise((resolve) => {
      setIsGenerating(true);
      setError(null);
      setProgress(null);

      // Determine WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/codemap`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        // Send generation request
        ws.send(JSON.stringify(request));
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case 'progress':
              setProgress(message.data as CodemapProgress);
              break;

            case 'complete':
              setIsGenerating(false);
              setProgress(null);
              resolve(message.data as Codemap);
              ws.close();
              break;

            case 'error':
              setIsGenerating(false);
              setError(message.message);
              setProgress(null);
              resolve(null);
              ws.close();
              break;
          }
        } catch (err) {
          console.error('WebSocket message parse error:', err);
        }
      };

      ws.onerror = () => {
        setIsGenerating(false);
        setError('Connection error');
        setProgress(null);
        resolve(null);
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (isGenerating) {
          setIsGenerating(false);
        }
      };
    });
  }, []);

  return {
    isGenerating,
    progress,
    error,
    generate,
    cancel
  };
}
```

---

## 7. API Specification

### 7.1 REST Endpoints

```yaml
# OpenAPI 3.0 Specification

openapi: 3.0.0
info:
  title: DeepWiki Codemap API
  version: 1.0.0

paths:
  /api/codemap/generate:
    post:
      summary: Start codemap generation
      description: Initiates async codemap generation. Use WebSocket for real-time progress.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CodemapGenerateRequest'
      responses:
        '202':
          description: Generation started
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CodemapGenerateResponse'
        '400':
          description: Invalid request
        '401':
          description: Unauthorized

  /api/codemap/{codemap_id}:
    get:
      summary: Get codemap by ID
      parameters:
        - name: codemap_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Codemap found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Codemap'
        '404':
          description: Codemap not found

    delete:
      summary: Delete codemap
      parameters:
        - name: codemap_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Deleted successfully
        '404':
          description: Codemap not found

  /api/codemap/list:
    get:
      summary: List codemaps for a repository
      parameters:
        - name: repo_owner
          in: query
          required: true
          schema:
            type: string
        - name: repo_name
          in: query
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: List of codemaps
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/CodemapSummary'
                  total:
                    type: integer

  /api/codemap/{codemap_id}/share:
    post:
      summary: Generate share link
      parameters:
        - name: codemap_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Share link generated
          content:
            application/json:
              schema:
                type: object
                properties:
                  share_url:
                    type: string
                  expires_at:
                    type: string
                    format: date-time

  /api/codemap/shared/{share_token}:
    get:
      summary: Get shared codemap
      parameters:
        - name: share_token
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Shared codemap
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Codemap'
        '404':
          description: Share link invalid or expired

components:
  schemas:
    CodemapGenerateRequest:
      type: object
      required:
        - repo_url
        - query
      properties:
        repo_url:
          type: string
        query:
          type: string
        analysis_type:
          type: string
          enum: [auto, data_flow, control_flow, dependencies, call_graph, architecture]
          default: auto
        depth:
          type: integer
          minimum: 1
          maximum: 10
          default: 3
        max_nodes:
          type: integer
          minimum: 10
          maximum: 200
          default: 50
        include_paths:
          type: array
          items:
            type: string
        exclude_paths:
          type: array
          items:
            type: string
        provider:
          type: string
          default: google
        model:
          type: string
        token:
          type: string
        type:
          type: string
          enum: [github, gitlab, bitbucket]
          default: github

    CodemapGenerateResponse:
      type: object
      properties:
        codemap_id:
          type: string
        status:
          $ref: '#/components/schemas/CodemapStatus'
        message:
          type: string
        estimated_time_seconds:
          type: integer

    CodemapStatus:
      type: string
      enum: [pending, analyzing, generating, rendering, completed, failed]

    CodemapSummary:
      type: object
      properties:
        id:
          type: string
        query:
          type: string
        title:
          type: string
        created_at:
          type: string
          format: date-time
        node_count:
          type: integer
        edge_count:
          type: integer
```

### 7.2 WebSocket Protocol

```
# WebSocket: /ws/codemap

## Client -> Server

### Generate Request
{
  "repo_url": "https://github.com/owner/repo",
  "query": "How does authentication work?",
  "analysis_type": "auto",
  "depth": 3,
  "max_nodes": 50,
  "provider": "google",
  "model": "gemini-2.5-flash",
  "token": "optional_access_token",
  "type": "github"
}

## Server -> Client

### Progress Update
{
  "type": "progress",
  "data": {
    "codemap_id": "uuid",
    "status": "analyzing",
    "progress_percent": 35,
    "current_step": "Analyzing code structure...",
    "details": "Processing api/main.py",
    "nodes_found": 12,
    "edges_found": 8,
    "files_analyzed": 5,
    "total_files": 15
  }
}

### Completion
{
  "type": "complete",
  "data": {
    // Full Codemap object
  }
}

### Error
{
  "type": "error",
  "message": "Error description"
}
```

---

## 8. LLM Prompts & Strategies

### 8.1 Query Understanding Strategy

```
Input: "How does authentication work?"

Step 1: Extract intent
- Primary goal: understand_flow
- Domain: authentication, security
- Expected output: data_flow diagram with auth components

Step 2: Generate search queries
- "authentication login flow"
- "user session management"
- "JWT token validation"
- "middleware auth"

Step 3: Prioritize file types
- auth*.py, *auth*.ts
- middleware*.py
- session*.py
- jwt*.py
```

### 8.2 Relationship Inference Strategy

```
Given:
- Static analysis: imports, function calls
- Semantic similarity: related code chunks
- User query context

Infer:
1. Direct relationships (from static analysis)
   - File A imports File B → "imports" edge
   - Function X calls Function Y → "calls" edge

2. Indirect relationships (from LLM reasoning)
   - "This validator is used before database write" → "guards" edge
   - "Error from here propagates to handler" → "error_flow" edge

3. Architectural relationships
   - "Service layer depends on repository layer" → "depends_on" edge
   - "Controller routes to service" → "routes_to" edge
```

### 8.3 Trace Guide Generation Strategy

```
Structure:
1. Executive Summary (2-3 sentences)
   - Direct answer to the query
   - Key components involved

2. Entry Points
   - Where the flow starts
   - Initial triggers (API endpoint, event, etc.)

3. Core Flow (ordered sections)
   - Each section: what happens, why, where
   - Code references with line numbers
   - Data transformations

4. Edge Cases
   - Error handling
   - Alternative paths
   - Security considerations

5. Conclusion
   - Summary of key points
   - Related areas to explore
```

---

## 9. Integration Points

### 9.1 Integration with Existing DeepWiki

| Integration Point | Implementation |
|-------------------|----------------|
| **Wiki Pages** | Add "Generate Codemap" button to wiki page headers |
| **Ask Chat** | Allow `@codemap` mention to include codemap context |
| **Navigation** | Add Codemap tab alongside Wiki in repo view |
| **Search** | Include codemaps in search results |
| **Cache** | Share RAG index between wiki and codemap |

### 9.2 File System Integration

```
~/.adalflow/
├── repos/           # Shared with existing wiki
├── databases/       # Shared FAISS indices
├── wikicache/       # Existing wiki cache
└── codemaps/        # NEW: Codemap storage
    ├── {id}.json    # Codemap data
    ├── {id}.md      # Trace guide markdown
    └── index.json   # Index of all codemaps
```

### 9.3 Frontend Route Integration

```typescript
// src/app/[owner]/[repo]/layout.tsx

// Add codemap tab to repository layout
const tabs = [
  { name: 'Wiki', href: `/${owner}/${repo}` },
  { name: 'Codemap', href: `/${owner}/${repo}/codemap` },  // NEW
  { name: 'Ask', href: `/${owner}/${repo}/ask` },
];
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

```python
# tests/codemap/test_analyzer.py

import pytest
from api.codemap.analyzer.python_analyzer import PythonAnalyzer

class TestPythonAnalyzer:
    def test_extract_classes(self):
        code = '''
class MyClass:
    def method(self):
        pass
'''
        analyzer = PythonAnalyzer()
        result = analyzer.analyze_code(code, "test.py")

        assert len(result.symbols) == 2
        assert result.symbols[0].name == "MyClass"
        assert result.symbols[0].type == "class"

    def test_extract_imports(self):
        code = '''
from module import func
import os
'''
        analyzer = PythonAnalyzer()
        result = analyzer.analyze_code(code, "test.py")

        assert len(result.imports) == 2
        assert result.imports[0].module == "module"
        assert result.imports[0].names == ["func"]

    def test_extract_calls(self):
        code = '''
def caller():
    callee()
    obj.method()
'''
        analyzer = PythonAnalyzer()
        result = analyzer.analyze_code(code, "test.py")

        assert len(result.calls) == 2
        assert result.calls[0].callee == "callee"
        assert result.calls[1].callee == "obj.method"
```

### 10.2 Integration Tests

```python
# tests/codemap/test_engine.py

import pytest
from api.codemap.engine import CodemapEngine
from api.codemap.models import CodemapGenerateRequest

@pytest.mark.asyncio
async def test_generate_codemap():
    engine = CodemapEngine(db_manager=mock_db_manager)

    request = CodemapGenerateRequest(
        repo_url="https://github.com/test/repo",
        query="How does the API work?"
    )

    progress_updates = []
    async def track_progress(p):
        progress_updates.append(p)

    codemap = await engine.generate(request, progress_callback=track_progress)

    assert codemap is not None
    assert len(codemap.graph.nodes) > 0
    assert len(progress_updates) > 0
    assert codemap.status == "completed"
```

### 10.3 E2E Tests

```typescript
// tests/e2e/codemap.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Codemap Feature', () => {
  test('should generate codemap from query', async ({ page }) => {
    await page.goto('/owner/repo/codemap');

    // Enter query
    await page.fill('[data-testid="codemap-query-input"]', 'How does authentication work?');
    await page.click('[data-testid="codemap-generate-btn"]');

    // Wait for generation
    await expect(page.locator('[data-testid="codemap-progress"]')).toBeVisible();
    await expect(page.locator('[data-testid="codemap-viewer"]')).toBeVisible({ timeout: 60000 });

    // Verify diagram rendered
    await expect(page.locator('svg.mermaid')).toBeVisible();

    // Verify trace guide
    await expect(page.locator('[data-testid="trace-guide"]')).toContainText('authentication');
  });

  test('should navigate to code on node click', async ({ page }) => {
    // Setup: have a codemap displayed
    await page.goto('/owner/repo/codemap/existing-id');

    // Click on a node
    await page.click('.node:first-child');

    // Verify node inspector opens
    await expect(page.locator('[data-testid="node-inspector"]')).toBeVisible();

    // Verify file location shown
    await expect(page.locator('[data-testid="node-location"]')).toContainText('.py');
  });
});
```

---

## 11. Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal**: Basic infrastructure and data models

- [ ] Create `api/codemap/` directory structure
- [ ] Implement Pydantic models (`models.py`)
- [ ] Implement Python AST analyzer (`analyzer/python_analyzer.py`)
- [ ] Create basic node/edge builders
- [ ] Set up storage layer
- [ ] Add REST endpoints (generate, get, list)
- [ ] Basic unit tests

**Deliverable**: Can analyze Python files and generate raw graph data

### Phase 2: LLM Integration (Week 3-4)
**Goal**: AI-powered analysis and generation

- [ ] Implement query parser with LLM
- [ ] Implement relationship extractor
- [ ] Implement trace guide writer
- [ ] Add Mermaid renderer
- [ ] Integrate with existing RAG pipeline
- [ ] WebSocket handler for streaming

**Deliverable**: Can generate complete codemaps with AI explanations

### Phase 3: Frontend Core (Week 5-6)
**Goal**: Basic UI for codemap viewing

- [ ] Create TypeScript types
- [ ] Implement `CodemapPanel` component
- [ ] Implement `CodemapMermaid` component
- [ ] Implement `TraceGuide` component
- [ ] Add WebSocket hook for generation
- [ ] Create codemap page route

**Deliverable**: Can view codemaps in browser with basic interactions

### Phase 4: Interactivity (Week 7-8)
**Goal**: Rich interactive experience

- [ ] Node selection and highlighting
- [ ] Node inspector panel
- [ ] Click-to-navigate to source
- [ ] Zoom/pan controls
- [ ] View mode switching (graph/trace/split)
- [ ] History and favorites

**Deliverable**: Full interactive codemap experience

### Phase 5: Polish & Integration (Week 9-10)
**Goal**: Production-ready feature

- [ ] JavaScript/TypeScript analyzer
- [ ] Share functionality
- [ ] Integration with existing wiki
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Documentation

**Deliverable**: Feature ready for release

---

## 12. Performance Considerations

### 12.1 Optimization Strategies

| Area | Strategy |
|------|----------|
| **Large Repos** | Limit initial analysis scope, expand on demand |
| **LLM Calls** | Cache query parsing, batch relationship extraction |
| **Graph Rendering** | Use virtualization for large graphs (>100 nodes) |
| **Storage** | Compress codemap JSON, lazy-load trace guide sections |
| **Memory** | Stream analysis results, don't load entire repo in memory |

### 12.2 Caching Strategy

```python
# Cache levels:
# L1: In-memory (current request)
# L2: Local storage (~/.adalflow/cache/)
# L3: Browser localStorage (frontend)

CACHE_CONFIG = {
    "ast_analysis": {
        "ttl": 3600,  # 1 hour
        "key": "{repo}:{file}:{hash}"
    },
    "query_intent": {
        "ttl": 86400,  # 24 hours
        "key": "{query_normalized}"
    },
    "codemap": {
        "ttl": 604800,  # 7 days
        "key": "{repo}:{query}:{commit}"
    }
}
```

### 12.3 Scalability Limits

| Metric | Recommended Limit | Hard Limit |
|--------|-------------------|------------|
| Repository size | 10,000 files | 50,000 files |
| Files per analysis | 100 files | 500 files |
| Nodes per codemap | 50 nodes | 200 nodes |
| Concurrent generations | 5 | 20 |
| WebSocket connections | 100 | 1000 |

---

## 13. Future Enhancements

### 13.1 Short-term (v1.1)

- [ ] Support for more languages (Go, Rust, Java)
- [ ] Codemap diff (compare two codemaps)
- [ ] Export to PNG/PDF
- [ ] Keyboard shortcuts
- [ ] Dark mode optimizations

### 13.2 Medium-term (v1.2)

- [ ] Collaborative annotations
- [ ] Version history (track codemap changes over commits)
- [ ] Custom node styling
- [ ] Integration with IDE extensions
- [ ] API for external tools

### 13.3 Long-term (v2.0)

- [ ] Real-time collaborative editing
- [ ] AI-suggested queries based on recent changes
- [ ] Automatic codemap updates on commit
- [ ] Cross-repository codemaps
- [ ] 3D visualization option
- [ ] Voice-guided code tours

---

## Appendix A: File Templates

### A.1 Backend File Template

```python
# api/codemap/{module}.py

"""
{Module Name}

{Brief description of what this module does}
"""

import logging
from typing import List, Optional, Dict, Any

from .models import {RelevantModels}

logger = logging.getLogger(__name__)


class {ClassName}:
    """
    {Class description}

    Attributes:
        {attr}: {description}
    """

    def __init__(self, **kwargs):
        """Initialize {ClassName}."""
        pass

    async def {main_method}(self, **kwargs) -> {ReturnType}:
        """
        {Method description}

        Args:
            {arg}: {description}

        Returns:
            {description}

        Raises:
            {Exception}: {when}
        """
        pass
```

### A.2 Frontend Component Template

```tsx
// src/components/codemap/{ComponentName}.tsx

'use client';

import React, { useState, useCallback } from 'react';
import { {Types} } from '@/types/codemap';

interface {ComponentName}Props {
  // Props definition
}

export function {ComponentName}({ ...props }: {ComponentName}Props) {
  // State
  const [state, setState] = useState();

  // Handlers
  const handleAction = useCallback(() => {
    // Implementation
  }, []);

  // Render
  return (
    <div className="">
      {/* Component content */}
    </div>
  );
}
```

---

## Appendix B: References

1. [Cognition Codemaps Blog Post](https://cognition.ai/blog/codemaps)
2. [Windsurf Codemaps Documentation](https://docs.windsurf.com/windsurf/codemaps)
3. [Mermaid.js Documentation](https://mermaid.js.org/)
4. [Python AST Documentation](https://docs.python.org/3/library/ast.html)
5. [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
6. [FastAPI WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/)

---

*This plan was generated on 2025-12-17 and should be reviewed and updated as implementation progresses.*
