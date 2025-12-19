"""
Pruner for removing irrelevant nodes from the codemap.
"""

import logging
from typing import List, Tuple, Set
from collections import defaultdict

from ..models import CodemapNode, CodemapEdge, Importance, QueryIntent, EdgeType

logger = logging.getLogger(__name__)


class Pruner:
    """
    Removes irrelevant nodes to keep the codemap focused and readable.
    
    Uses query relevance scoring and connectivity analysis to
    determine which nodes to keep.
    """
    
    def __init__(self):
        pass
    
    def prune(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge],
        query_intent: QueryIntent,
        max_nodes: int = 50
    ) -> Tuple[List[CodemapNode], List[CodemapEdge]]:
        """
        Prune nodes and edges to a manageable size.
        
        Args:
            nodes: List of all nodes
            edges: List of all edges
            query_intent: Parsed query intent for relevance scoring
            max_nodes: Maximum number of nodes to keep
            
        Returns:
            Tuple of (pruned_nodes, pruned_edges)
        """
        if len(nodes) <= max_nodes:
            return nodes, edges
        
        # Score each node
        node_scores = {}
        for node in nodes:
            score = self._calculate_node_score(node, edges, query_intent)
            node_scores[node.id] = score
        
        # Sort by score and select top nodes
        sorted_nodes = sorted(nodes, key=lambda n: node_scores[n.id], reverse=True)
        kept_nodes = sorted_nodes[:max_nodes]
        kept_node_ids = {node.id for node in kept_nodes}
        
        # Keep edges that connect kept nodes
        kept_edges = [
            edge for edge in edges
            if edge.source in kept_node_ids and edge.target in kept_node_ids
        ]
        
        # Ensure we don't have orphaned nodes (nodes with no edges)
        kept_nodes, kept_edges = self._remove_orphans(kept_nodes, kept_edges)
        
        logger.info(f"Pruned from {len(nodes)} to {len(kept_nodes)} nodes")
        
        return kept_nodes, kept_edges
    
    def _calculate_node_score(
        self,
        node: CodemapNode,
        edges: List[CodemapEdge],
        query_intent: QueryIntent
    ) -> float:
        """Calculate a relevance score for a node"""
        score = 0.0
        
        # Base score from importance
        importance_scores = {
            Importance.CRITICAL: 100.0,
            Importance.HIGH: 50.0,
            Importance.MEDIUM: 20.0,
            Importance.LOW: 5.0,
        }
        score += importance_scores.get(node.importance, 10.0)
        
        # Connectivity score (more connections = more important)
        in_degree = sum(1 for e in edges if e.target == node.id)
        out_degree = sum(1 for e in edges if e.source == node.id)
        score += (in_degree * 3.0) + (out_degree * 2.0)
        
        # Query relevance score
        relevance = self._calculate_query_relevance(node, query_intent)
        score += relevance * 50.0
        
        # Bonus for having description or docstring
        if node.description:
            score += 5.0
        if node.snippet:
            score += 3.0
        
        return score
    
    def _calculate_query_relevance(
        self,
        node: CodemapNode,
        query_intent: QueryIntent
    ) -> float:
        """Calculate how relevant a node is to the query"""
        relevance = 0.0
        
        # Check name against keywords
        name_lower = node.label.lower()
        for keyword in query_intent.keywords:
            if keyword.lower() in name_lower:
                relevance += 1.0
        
        # Check against focus areas
        for focus in query_intent.focus_areas:
            if focus.lower() in name_lower:
                relevance += 0.8
        
        # Check description
        if node.description:
            desc_lower = node.description.lower()
            for keyword in query_intent.keywords:
                if keyword.lower() in desc_lower:
                    relevance += 0.5
        
        # Check file path
        if node.location:
            path_lower = node.location.file_path.lower()
            for keyword in query_intent.keywords:
                if keyword.lower() in path_lower:
                    relevance += 0.3
        
        return min(relevance, 5.0)  # Cap relevance score
    
    def _remove_orphans(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge]
    ) -> Tuple[List[CodemapNode], List[CodemapEdge]]:
        """
        Remove nodes that have no connections.
        
        Exception: Keep high-importance orphans as they may be entry points.
        """
        node_ids = {node.id for node in nodes}
        connected_ids: Set[str] = set()
        
        for edge in edges:
            connected_ids.add(edge.source)
            connected_ids.add(edge.target)
        
        # Keep connected nodes and high-importance orphans
        kept_nodes = [
            node for node in nodes
            if node.id in connected_ids or 
               node.importance in (Importance.CRITICAL, Importance.HIGH)
        ]
        
        # Update node set
        kept_node_ids = {node.id for node in kept_nodes}
        
        # Filter edges again with final node set
        kept_edges = [
            edge for edge in edges
            if edge.source in kept_node_ids and edge.target in kept_node_ids
        ]
        
        return kept_nodes, kept_edges
    
    def prune_by_depth(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge],
        root_nodes: List[str],
        max_depth: int = 3
    ) -> Tuple[List[CodemapNode], List[CodemapEdge]]:
        """
        Prune nodes beyond a certain depth from root nodes.
        
        Uses BFS to determine depth from root nodes.
        """
        # Build adjacency list for outgoing edges
        adjacency = defaultdict(set)
        for edge in edges:
            adjacency[edge.source].add(edge.target)
        
        # BFS to find depths
        node_depths = {}
        queue = [(root_id, 0) for root_id in root_nodes]
        visited = set()
        
        while queue:
            node_id, depth = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            node_depths[node_id] = depth
            
            if depth < max_depth:
                for neighbor in adjacency[node_id]:
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
        
        # Keep nodes within depth limit
        kept_node_ids = {
            node_id for node_id, depth in node_depths.items()
            if depth <= max_depth
        }
        
        kept_nodes = [node for node in nodes if node.id in kept_node_ids]
        kept_edges = [
            edge for edge in edges
            if edge.source in kept_node_ids and edge.target in kept_node_ids
        ]
        
        return kept_nodes, kept_edges
