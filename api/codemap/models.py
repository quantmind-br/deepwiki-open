"""
Pydantic models for the Codemap feature.

These models define the data structures used throughout the codemap
generation pipeline, from request/response to graph representation.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime


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


class SourceLocation(BaseModel):
    """Exact location in source code"""
    file_path: str = Field(..., description="Relative path from repo root")
    line_start: int = Field(..., ge=1, description="Starting line number")
    line_end: int = Field(..., ge=1, description="Ending line number")
    column_start: Optional[int] = Field(None, ge=0)
    column_end: Optional[int] = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_range(self):
        if self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        return self


class CodeSnippet(BaseModel):
    """Code snippet for preview"""
    code: str = Field(..., description="Actual code content")
    language: str = Field(..., description="Programming language")


class CodemapNode(BaseModel):
    """A node in the codemap graph"""
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label")
    type: NodeType = Field(..., description="Node type")

    location: Optional[SourceLocation] = Field(
        None, description="Source code location (required for navigable nodes)"
    )

    description: Optional[str] = Field(None, description="Brief description")
    importance: Importance = Field(Importance.MEDIUM)

    snippet: Optional[CodeSnippet] = Field(None, description="Code preview")

    parent_id: Optional[str] = Field(None, description="Parent node for nesting")
    group: Optional[str] = Field(None, description="Logical group name")

    metadata: Dict[str, Any] = Field(default_factory=dict)

    x: Optional[float] = Field(None, description="X position")
    y: Optional[float] = Field(None, description="Y position")
    width: Optional[float] = Field(None)
    height: Optional[float] = Field(None)


class CodemapEdge(BaseModel):
    """An edge connecting two nodes"""
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Relationship type")

    label: Optional[str] = Field(None, description="Edge label")

    description: Optional[str] = Field(None, description="Relationship description")
    weight: float = Field(1.0, ge=0, description="Edge weight for layout")

    metadata: Dict[str, Any] = Field(default_factory=dict)


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


class CodemapGraph(BaseModel):
    """The graph structure of a codemap"""
    nodes: List[CodemapNode]
    edges: List[CodemapEdge]

    root_nodes: List[str] = Field(default_factory=list, description="Entry point nodes")
    clusters: Dict[str, List[str]] = Field(default_factory=dict, description="Node clusters")


class CodemapRenderOutput(BaseModel):
    """Rendered output formats"""
    mermaid: str = Field(..., description="Mermaid diagram code")
    json_graph: Dict[str, Any] = Field(..., description="JSON representation")
    html: Optional[str] = Field(None, description="Standalone HTML")


class Codemap(BaseModel):
    """Complete codemap artifact"""
    id: str = Field(..., description="Unique codemap ID")

    repo_url: str
    repo_owner: str
    repo_name: str
    commit_hash: Optional[str] = None

    query: str = Field(..., description="Original user query")
    analysis_type: str = Field("general", description="Type of analysis performed")

    title: str
    description: str
    graph: CodemapGraph
    trace_guide: TraceGuide
    render: CodemapRenderOutput

    status: CodemapStatus = CodemapStatus.COMPLETED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_time_ms: int = Field(0, description="Time to generate in milliseconds")
    model_used: str = Field("", description="LLM model used")

    is_public: bool = False
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = Field(None, description="Share token expiry time")


class CodemapGenerateRequest(BaseModel):
    """Request to generate a new codemap"""
    repo_url: str
    query: str

    language: Optional[str] = Field("en", description="Language for generated text")
    analysis_type: Optional[str] = Field(
        "auto", 
        description="Type: auto, data_flow, control_flow, dependencies, call_graph, architecture"
    )
    depth: Optional[int] = Field(3, ge=1, le=10, description="Analysis depth")
    max_nodes: Optional[int] = Field(50, ge=10, le=200, description="Maximum nodes")

    excluded_dirs: Optional[List[str]] = Field(None, description="Directories to exclude")
    excluded_files: Optional[List[str]] = Field(None, description="File patterns to exclude")
    included_dirs: Optional[List[str]] = Field(None, description="Directories to include exclusively")
    included_files: Optional[List[str]] = Field(None, description="File patterns to include exclusively")
    file_types: Optional[List[str]] = Field(None, description="File extensions to prioritize")

    provider: Optional[str] = Field("google", description="LLM provider")
    model: Optional[str] = Field(None, description="Specific model")

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

    nodes_found: int = 0
    edges_found: int = 0
    files_analyzed: int = 0
    total_files: int = 0


class QueryIntent(BaseModel):
    """Parsed intent from user query"""
    intent: str = Field(..., description="Primary goal of the query")
    focus_areas: List[str] = Field(default_factory=list)
    analysis_type: str = Field("general")
    preferred_layout: str = Field("hierarchical")
    depth: int = Field(3, ge=1, le=5)
    keywords: List[str] = Field(default_factory=list)
