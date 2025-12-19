"""
JSON renderer for exporting codemap graphs.
"""

import logging
from typing import Dict, Any

from ..models import CodemapGraph, CodemapNode, CodemapEdge

logger = logging.getLogger(__name__)


class JSONRenderer:
    """
    Exports codemap graphs as JSON for use with graph visualization libraries.
    
    The output format is compatible with common graph libraries like:
    - D3.js
    - vis.js
    - Cytoscape.js
    - React Flow
    """
    
    def __init__(self):
        pass
    
    def render(self, graph: CodemapGraph) -> Dict[str, Any]:
        """
        Render a codemap graph as JSON.
        
        Args:
            graph: The codemap graph
            
        Returns:
            JSON-serializable dictionary
        """
        return {
            "nodes": [self._serialize_node(node) for node in graph.nodes],
            "edges": [self._serialize_edge(edge) for edge in graph.edges],
            "rootNodes": graph.root_nodes,
            "clusters": graph.clusters,
            "metadata": {
                "nodeCount": len(graph.nodes),
                "edgeCount": len(graph.edges),
                "clusterCount": len(graph.clusters)
            }
        }
    
    def _serialize_node(self, node: CodemapNode) -> Dict[str, Any]:
        """Serialize a node to JSON"""
        data = {
            "id": node.id,
            "label": node.label,
            "type": node.type.value,
            "importance": node.importance.value,
        }
        
        # Add optional fields if present
        if node.location:
            data["location"] = {
                "filePath": node.location.file_path,
                "lineStart": node.location.line_start,
                "lineEnd": node.location.line_end,
                "columnStart": node.location.column_start,
                "columnEnd": node.location.column_end,
            }
        
        if node.description:
            data["description"] = node.description
        
        if node.snippet:
            data["snippet"] = {
                "code": node.snippet.code,
                "language": node.snippet.language,
            }
        
        if node.parent_id:
            data["parentId"] = node.parent_id
        
        if node.group:
            data["group"] = node.group
        
        if node.metadata:
            data["metadata"] = node.metadata
        
        # Position data
        if node.x is not None:
            data["position"] = {
                "x": node.x,
                "y": node.y,
            }
        
        if node.width:
            data["size"] = {
                "width": node.width,
                "height": node.height,
            }
        
        return data
    
    def _serialize_edge(self, edge: CodemapEdge) -> Dict[str, Any]:
        """Serialize an edge to JSON"""
        data = {
            "id": edge.id,
            "source": edge.source,
            "target": edge.target,
            "type": edge.type.value,
            "weight": edge.weight,
        }
        
        if edge.label:
            data["label"] = edge.label
        
        if edge.description:
            data["description"] = edge.description
        
        if edge.metadata:
            data["metadata"] = edge.metadata
        
        return data
    
    def render_d3_format(self, graph: CodemapGraph) -> Dict[str, Any]:
        """
        Render in D3.js force-directed graph format.
        
        D3 expects:
        - nodes: array of {id, ...}
        - links: array of {source, target, ...}
        """
        return {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "group": node.group or node.type.value,
                    "type": node.type.value,
                    "importance": node.importance.value,
                    "x": node.x,
                    "y": node.y,
                }
                for node in graph.nodes
            ],
            "links": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.type.value,
                    "value": edge.weight,
                }
                for edge in graph.edges
            ]
        }
    
    def render_cytoscape_format(self, graph: CodemapGraph) -> Dict[str, Any]:
        """
        Render in Cytoscape.js format.
        
        Cytoscape expects:
        - elements: array of {data: {...}, ...}
        """
        elements = []
        
        # Add nodes
        for node in graph.nodes:
            element = {
                "data": {
                    "id": node.id,
                    "label": node.label,
                    "type": node.type.value,
                    "importance": node.importance.value,
                }
            }
            
            if node.parent_id:
                element["data"]["parent"] = node.parent_id
            
            if node.x is not None:
                element["position"] = {"x": node.x, "y": node.y}
            
            elements.append(element)
        
        # Add edges
        for edge in graph.edges:
            elements.append({
                "data": {
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.type.value,
                    "label": edge.label or "",
                }
            })
        
        return {"elements": elements}
    
    def render_react_flow_format(self, graph: CodemapGraph) -> Dict[str, Any]:
        """
        Render in React Flow format.
        
        React Flow expects:
        - nodes: array of {id, position, data, type}
        - edges: array of {id, source, target, ...}
        """
        nodes = []
        for node in graph.nodes:
            rf_node = {
                "id": node.id,
                "type": self._map_to_react_flow_type(node.type),
                "data": {
                    "label": node.label,
                    "type": node.type.value,
                    "importance": node.importance.value,
                    "description": node.description,
                },
                "position": {
                    "x": node.x or 0,
                    "y": node.y or 0,
                }
            }
            
            if node.parent_id:
                rf_node["parentNode"] = node.parent_id
            
            nodes.append(rf_node)
        
        edges = []
        for edge in graph.edges:
            rf_edge = {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "type": self._map_to_react_flow_edge_type(edge.type),
                "label": edge.label,
                "animated": edge.type in (
                    "data_flow", "control_flow"
                ),
            }
            edges.append(rf_edge)
        
        return {"nodes": nodes, "edges": edges}
    
    def _map_to_react_flow_type(self, node_type) -> str:
        """Map node type to React Flow node type"""
        # Default custom node types (would need to be defined in frontend)
        type_map = {
            "file": "fileNode",
            "class": "classNode",
            "function": "functionNode",
            "method": "methodNode",
            "interface": "interfaceNode",
            "external": "externalNode",
        }
        return type_map.get(node_type.value, "default")
    
    def _map_to_react_flow_edge_type(self, edge_type) -> str:
        """Map edge type to React Flow edge type"""
        if edge_type.value in ("extends", "implements"):
            return "smoothstep"
        elif edge_type.value in ("calls", "data_flow"):
            return "default"
        else:
            return "straight"
