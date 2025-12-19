"""
Mermaid diagram renderer for codemaps.
"""

import logging
import re
from typing import Optional

from ..models import CodemapGraph, CodemapNode, CodemapEdge, NodeType, EdgeType, QueryIntent

logger = logging.getLogger(__name__)


class MermaidRenderer:
    """
    Renders codemap graphs as Mermaid flowchart diagrams.
    
    Generates Mermaid syntax that can be rendered by the frontend
    using mermaid.js.
    """
    
    # Node shapes by type
    NODE_SHAPES = {
        NodeType.FILE: ('([', '])'),           # Stadium shape
        NodeType.MODULE: ('[[', ']]'),         # Subroutine shape
        NodeType.CLASS: ('[', ']'),            # Rectangle
        NodeType.INTERFACE: ('{{', '}}'),      # Hexagon
        NodeType.FUNCTION: ('(', ')'),         # Rounded rectangle
        NodeType.METHOD: ('(', ')'),           # Rounded rectangle
        NodeType.TYPE: ('[/', '/]'),           # Parallelogram
        NodeType.ENDPOINT: ('>', ']'),         # Asymmetric
        NodeType.DATABASE: ('[(', ')]'),       # Cylinder
        NodeType.EXTERNAL: ('((', '))'),       # Circle
        NodeType.VARIABLE: ('[', ']'),         # Rectangle
        NodeType.CONSTANT: ('[', ']'),         # Rectangle
    }
    
    # Edge styles by type
    EDGE_STYLES = {
        EdgeType.IMPORTS: '-->',
        EdgeType.EXPORTS: '-->',
        EdgeType.CALLS: '==>',
        EdgeType.EXTENDS: '-.->',
        EdgeType.IMPLEMENTS: '-.->',
        EdgeType.USES: '-->',
        EdgeType.RETURNS: '-->',
        EdgeType.INSTANTIATES: '-->',
        EdgeType.DATA_FLOW: '~~~',
        EdgeType.CONTROL_FLOW: '-->',
        EdgeType.DEPENDS_ON: '-->',
        EdgeType.CONTAINS: '-->',
    }
    
    def __init__(self):
        pass
    
    def render(
        self,
        graph: CodemapGraph,
        query_intent: Optional[QueryIntent] = None
    ) -> str:
        """
        Render a codemap graph as Mermaid code.
        
        Args:
            graph: The codemap graph
            query_intent: Optional query intent for styling
            
        Returns:
            Mermaid diagram code as string
        """
        lines = []
        
        # Determine direction based on query intent or default
        direction = "TB"  # Top to Bottom
        if query_intent and query_intent.preferred_layout == "force":
            direction = "LR"  # Left to Right for force layout
        
        lines.append(f"flowchart {direction}")
        
        # Add styling
        lines.append("")
        lines.extend(self._generate_styles())
        lines.append("")
        
        # Generate subgraphs for clusters
        rendered_nodes = set()
        for cluster_name, node_ids in graph.clusters.items():
            if len(node_ids) >= 2:  # Only create subgraph for meaningful clusters
                subgraph_lines = self._render_subgraph(cluster_name, node_ids, graph.nodes)
                if subgraph_lines:
                    lines.extend(subgraph_lines)
                    rendered_nodes.update(node_ids)
        
        # Render remaining nodes not in subgraphs
        lines.append("")
        for node in graph.nodes:
            if node.id not in rendered_nodes:
                lines.append(self._render_node(node))
        
        # Render edges
        lines.append("")
        for edge in graph.edges:
            edge_line = self._render_edge(edge)
            if edge_line:
                lines.append(edge_line)
        
        return "\n".join(lines)
    
    def _render_node(self, node: CodemapNode) -> str:
        """Render a single node"""
        node_id = self._sanitize_id(node.id)
        label = self._sanitize_label(node.label)
        
        # Get shape delimiters
        start, end = self.NODE_SHAPES.get(node.type, ('[', ']'))
        
        # Add type prefix to label if it's a class or function
        if node.type in (NodeType.CLASS, NodeType.INTERFACE):
            label = f"📦 {label}"
        elif node.type == NodeType.FUNCTION:
            label = f"⚙️ {label}"
        elif node.type == NodeType.METHOD:
            label = f"🔧 {label}"
        elif node.type == NodeType.FILE:
            label = f"📄 {label}"
        elif node.type == NodeType.ENDPOINT:
            label = f"🌐 {label}"
        elif node.type == NodeType.DATABASE:
            label = f"🗄️ {label}"
        
        return f"    {node_id}{start}{label}{end}"
    
    def _render_edge(self, edge: CodemapEdge) -> str:
        """Render a single edge"""
        source_id = self._sanitize_id(edge.source)
        target_id = self._sanitize_id(edge.target)
        
        # Get edge style
        style = self.EDGE_STYLES.get(edge.type, '-->')
        
        # Add label if present
        if edge.label:
            label = self._sanitize_label(edge.label)
            return f"    {source_id} {style}|{label}| {target_id}"
        else:
            return f"    {source_id} {style} {target_id}"
    
    def _render_subgraph(
        self,
        cluster_name: str,
        node_ids: list,
        all_nodes: list
    ) -> list:
        """Render a subgraph for a cluster"""
        lines = []
        
        # Get nodes in this cluster
        cluster_nodes = [n for n in all_nodes if n.id in node_ids]
        if not cluster_nodes:
            return lines
        
        # Clean up cluster name for display
        display_name = cluster_name
        if display_name.startswith("dir:"):
            display_name = display_name[4:]
        elif display_name.startswith("type:"):
            display_name = display_name[5:].capitalize()
        elif display_name.startswith("component:"):
            display_name = f"Component {display_name[10:]}"
        
        subgraph_id = self._sanitize_id(cluster_name)
        
        lines.append(f"    subgraph {subgraph_id}[{display_name}]")
        
        for node in cluster_nodes:
            lines.append("    " + self._render_node(node))
        
        lines.append("    end")
        
        return lines
    
    def _generate_styles(self) -> list:
        """Generate Mermaid style definitions"""
        return [
            "    %% Styles",
            "    classDef fileNode fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
            "    classDef classNode fill:#fff3e0,stroke:#e65100,stroke-width:2px",
            "    classDef funcNode fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px",
            "    classDef interfaceNode fill:#f3e5f5,stroke:#4a148c,stroke-width:2px",
            "    classDef externalNode fill:#fafafa,stroke:#757575,stroke-width:1px,stroke-dasharray: 5 5",
        ]
    
    def _sanitize_id(self, id_str: str) -> str:
        """Sanitize a string for use as a Mermaid node ID"""
        # Replace special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', id_str)
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'n' + sanitized
        return sanitized
    
    def _sanitize_label(self, label: str) -> str:
        """Sanitize a string for use as a Mermaid label"""
        # Escape special characters
        label = label.replace('"', "'")
        label = label.replace('[', '(')
        label = label.replace(']', ')')
        label = label.replace('{', '(')
        label = label.replace('}', ')')
        label = label.replace('<', '&lt;')
        label = label.replace('>', '&gt;')
        # Truncate long labels
        if len(label) > 30:
            label = label[:27] + "..."
        return label
    
    def render_simple(self, graph: CodemapGraph) -> str:
        """
        Render a simplified version without subgraphs.
        
        Useful for smaller diagrams or when subgraphs cause rendering issues.
        """
        lines = ["flowchart TB"]
        
        # Render all nodes
        for node in graph.nodes:
            lines.append(self._render_node(node))
        
        lines.append("")
        
        # Render all edges
        for edge in graph.edges:
            edge_line = self._render_edge(edge)
            if edge_line:
                lines.append(edge_line)
        
        return "\n".join(lines)
