"""
Clusterer for grouping related nodes in the codemap.
"""

import logging
from typing import List, Dict, Set
from collections import defaultdict

from ..models import CodemapNode, CodemapEdge, EdgeType

logger = logging.getLogger(__name__)


class Clusterer:
    """
    Groups related nodes into clusters for visual organization.
    
    Uses multiple strategies:
    - Directory-based clustering
    - Import-dependency clustering
    - Type-based clustering (classes together, functions together)
    """
    
    def __init__(self):
        pass
    
    def cluster(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge]
    ) -> Dict[str, List[str]]:
        """
        Create clusters from nodes and edges.
        
        Args:
            nodes: List of graph nodes
            edges: List of graph edges
            
        Returns:
            Dict mapping cluster name to list of node IDs
        """
        clusters = {}
        
        # Strategy 1: Directory-based clustering
        dir_clusters = self._cluster_by_directory(nodes)
        clusters.update(dir_clusters)
        
        # Strategy 2: Group by node type
        type_clusters = self._cluster_by_type(nodes)
        
        # Merge type clusters into directory clusters where appropriate
        for type_name, node_ids in type_clusters.items():
            if len(node_ids) >= 3:  # Only create type cluster if meaningful
                clusters[f"type:{type_name}"] = node_ids
        
        # Strategy 3: Connected component clustering for orphaned nodes
        component_clusters = self._cluster_by_connectivity(nodes, edges)
        for i, node_ids in enumerate(component_clusters):
            if len(node_ids) >= 2:
                cluster_name = f"component:{i}"
                if cluster_name not in clusters:
                    clusters[cluster_name] = node_ids
        
        return clusters
    
    def _cluster_by_directory(self, nodes: List[CodemapNode]) -> Dict[str, List[str]]:
        """Group nodes by their directory path"""
        clusters = defaultdict(list)
        
        for node in nodes:
            if node.location:
                # Extract directory from file path
                parts = node.location.file_path.split('/')
                if len(parts) > 1:
                    # Use first two levels of directory as cluster
                    dir_path = '/'.join(parts[:min(2, len(parts)-1)])
                else:
                    dir_path = "root"
                
                clusters[f"dir:{dir_path}"].append(node.id)
            elif node.group:
                clusters[f"dir:{node.group}"].append(node.id)
        
        return dict(clusters)
    
    def _cluster_by_type(self, nodes: List[CodemapNode]) -> Dict[str, List[str]]:
        """Group nodes by their type"""
        clusters = defaultdict(list)
        
        for node in nodes:
            clusters[node.type.value].append(node.id)
        
        return dict(clusters)
    
    def _cluster_by_connectivity(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge]
    ) -> List[List[str]]:
        """
        Find connected components using union-find.
        
        This groups nodes that are connected by edges.
        """
        # Build adjacency list
        adjacency = defaultdict(set)
        node_ids = {node.id for node in nodes}
        
        for edge in edges:
            if edge.source in node_ids and edge.target in node_ids:
                # Only consider strong connections for clustering
                if edge.type in (EdgeType.IMPORTS, EdgeType.CALLS, EdgeType.EXTENDS):
                    adjacency[edge.source].add(edge.target)
                    adjacency[edge.target].add(edge.source)
        
        # Union-Find
        parent = {node_id: node_id for node_id in node_ids}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Union connected nodes
        for node_id, neighbors in adjacency.items():
            for neighbor in neighbors:
                union(node_id, neighbor)
        
        # Group by root
        components = defaultdict(list)
        for node_id in node_ids:
            root = find(node_id)
            components[root].append(node_id)
        
        return list(components.values())
    
    def refine_clusters(
        self,
        clusters: Dict[str, List[str]],
        nodes: List[CodemapNode],
        max_cluster_size: int = 20,
        min_cluster_size: int = 2
    ) -> Dict[str, List[str]]:
        """
        Refine clusters by splitting large ones and removing small ones.
        
        Args:
            clusters: Initial clusters
            nodes: List of nodes
            max_cluster_size: Maximum nodes per cluster
            min_cluster_size: Minimum nodes to keep cluster
            
        Returns:
            Refined clusters
        """
        node_map = {node.id: node for node in nodes}
        refined = {}
        
        for cluster_name, node_ids in clusters.items():
            if len(node_ids) < min_cluster_size:
                continue  # Skip tiny clusters
            
            if len(node_ids) <= max_cluster_size:
                refined[cluster_name] = node_ids
            else:
                # Split large cluster by sub-directory or type
                sub_clusters = self._split_cluster(cluster_name, node_ids, node_map)
                refined.update(sub_clusters)
        
        return refined
    
    def _split_cluster(
        self,
        cluster_name: str,
        node_ids: List[str],
        node_map: Dict[str, CodemapNode]
    ) -> Dict[str, List[str]]:
        """Split a large cluster into smaller ones"""
        sub_clusters = defaultdict(list)
        
        for node_id in node_ids:
            node = node_map.get(node_id)
            if not node:
                continue
            
            # Try to split by sub-directory
            if node.location:
                parts = node.location.file_path.split('/')
                if len(parts) > 2:
                    sub_key = f"{cluster_name}/{parts[1]}"
                else:
                    sub_key = f"{cluster_name}/{node.type.value}"
            else:
                sub_key = f"{cluster_name}/{node.type.value}"
            
            sub_clusters[sub_key].append(node_id)
        
        return dict(sub_clusters)
