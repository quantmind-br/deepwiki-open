"""
Layout engine for positioning nodes in the codemap.
"""

import math
import logging
from typing import List, Dict, Tuple
from collections import defaultdict

from ..models import CodemapNode, CodemapEdge, NodeType

logger = logging.getLogger(__name__)


class LayoutEngine:
    """
    Calculates positions for nodes in the graph.
    
    Supports multiple layout algorithms:
    - hierarchical: Top-to-bottom tree layout
    - force: Force-directed layout
    - radial: Circular layout with root at center
    """
    
    def __init__(self):
        self.node_width = 150
        self.node_height = 50
        self.horizontal_spacing = 50
        self.vertical_spacing = 80
    
    def calculate(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge],
        layout_type: str = "hierarchical"
    ) -> List[CodemapNode]:
        """
        Calculate positions for all nodes.
        
        Args:
            nodes: List of nodes
            edges: List of edges
            layout_type: Layout algorithm to use
            
        Returns:
            Nodes with x, y positions set
        """
        if not nodes:
            return nodes
        
        if layout_type == "force":
            return self._force_layout(nodes, edges)
        elif layout_type == "radial":
            return self._radial_layout(nodes, edges)
        else:  # hierarchical (default)
            return self._hierarchical_layout(nodes, edges)
    
    def _hierarchical_layout(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge]
    ) -> List[CodemapNode]:
        """
        Arrange nodes in a hierarchical tree structure.
        
        Uses a simplified Sugiyama-style algorithm:
        1. Determine node levels based on dependencies
        2. Order nodes within each level to minimize crossings
        3. Position nodes based on level and order
        """
        node_map = {node.id: node for node in nodes}
        
        # Build adjacency lists
        outgoing = defaultdict(set)
        incoming = defaultdict(set)
        for edge in edges:
            if edge.source in node_map and edge.target in node_map:
                outgoing[edge.source].add(edge.target)
                incoming[edge.target].add(edge.source)
        
        # Find root nodes (nodes with no incoming edges)
        all_ids = set(node_map.keys())
        has_incoming = {edge.target for edge in edges if edge.target in node_map}
        root_ids = all_ids - has_incoming
        
        if not root_ids:
            # If no clear roots, use file nodes or nodes with most outgoing edges
            file_nodes = [n.id for n in nodes if n.type == NodeType.FILE]
            if file_nodes:
                root_ids = set(file_nodes[:5])
            else:
                # Use nodes with most outgoing edges
                root_ids = set(sorted(all_ids, key=lambda x: len(outgoing[x]), reverse=True)[:3])
        
        # Assign levels using BFS from roots
        levels = self._assign_levels(list(root_ids), outgoing, all_ids)
        
        # Group nodes by level
        level_groups = defaultdict(list)
        for node_id, level in levels.items():
            level_groups[level].append(node_id)
        
        # Handle unassigned nodes (not reachable from roots)
        max_level = max(levels.values()) if levels else 0
        unassigned = all_ids - set(levels.keys())
        if unassigned:
            level_groups[max_level + 1] = list(unassigned)
        
        # Position nodes
        for level, node_ids in level_groups.items():
            y = level * (self.node_height + self.vertical_spacing)
            total_width = len(node_ids) * (self.node_width + self.horizontal_spacing)
            start_x = -total_width / 2
            
            for i, node_id in enumerate(sorted(node_ids)):
                node = node_map.get(node_id)
                if node:
                    node.x = start_x + i * (self.node_width + self.horizontal_spacing)
                    node.y = y
                    node.width = self.node_width
                    node.height = self.node_height
        
        return nodes
    
    def _assign_levels(
        self,
        roots: List[str],
        outgoing: Dict[str, set],
        all_ids: set
    ) -> Dict[str, int]:
        """Assign levels to nodes using BFS"""
        levels = {}
        queue = [(root_id, 0) for root_id in roots]
        visited = set()
        
        while queue:
            node_id, level = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            levels[node_id] = level
            
            for neighbor in outgoing[node_id]:
                if neighbor not in visited:
                    queue.append((neighbor, level + 1))
        
        return levels
    
    def _force_layout(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge],
        iterations: int = 50
    ) -> List[CodemapNode]:
        """
        Force-directed layout using a simplified spring model.
        
        Nodes repel each other, edges act as springs.
        """
        import random
        
        node_map = {node.id: node for node in nodes}
        n = len(nodes)
        
        if n == 0:
            return nodes
        
        # Initial random positions
        area = n * 10000
        k = math.sqrt(area / n)  # Optimal distance between nodes
        
        positions = {}
        for node in nodes:
            positions[node.id] = (
                random.uniform(-area/4, area/4),
                random.uniform(-area/4, area/4)
            )
        
        # Build edge map
        edge_set = {(e.source, e.target) for e in edges}
        
        # Iterate
        temperature = area / 10
        cooling = temperature / (iterations + 1)
        
        for i in range(iterations):
            # Calculate repulsive forces
            displacement = {node_id: [0.0, 0.0] for node_id in positions}
            
            for n1 in nodes:
                for n2 in nodes:
                    if n1.id >= n2.id:
                        continue
                    
                    dx = positions[n1.id][0] - positions[n2.id][0]
                    dy = positions[n1.id][1] - positions[n2.id][1]
                    dist = max(math.sqrt(dx*dx + dy*dy), 0.01)
                    
                    # Repulsive force
                    force = k * k / dist
                    
                    displacement[n1.id][0] += dx / dist * force
                    displacement[n1.id][1] += dy / dist * force
                    displacement[n2.id][0] -= dx / dist * force
                    displacement[n2.id][1] -= dy / dist * force
            
            # Calculate attractive forces from edges
            for edge in edges:
                if edge.source not in positions or edge.target not in positions:
                    continue
                
                dx = positions[edge.source][0] - positions[edge.target][0]
                dy = positions[edge.source][1] - positions[edge.target][1]
                dist = max(math.sqrt(dx*dx + dy*dy), 0.01)
                
                # Attractive force
                force = dist * dist / k
                
                displacement[edge.source][0] -= dx / dist * force
                displacement[edge.source][1] -= dy / dist * force
                displacement[edge.target][0] += dx / dist * force
                displacement[edge.target][1] += dy / dist * force
            
            # Apply displacements with temperature limiting
            for node_id in positions:
                dx, dy = displacement[node_id]
                dist = max(math.sqrt(dx*dx + dy*dy), 0.01)
                
                # Limit by temperature
                x_disp = dx / dist * min(dist, temperature)
                y_disp = dy / dist * min(dist, temperature)
                
                new_x = positions[node_id][0] + x_disp
                new_y = positions[node_id][1] + y_disp
                
                # Keep within bounds
                bound = area / 2
                positions[node_id] = (
                    max(-bound, min(bound, new_x)),
                    max(-bound, min(bound, new_y))
                )
            
            temperature -= cooling
        
        # Apply positions to nodes
        for node in nodes:
            if node.id in positions:
                node.x = positions[node.id][0]
                node.y = positions[node.id][1]
                node.width = self.node_width
                node.height = self.node_height
        
        return nodes
    
    def _radial_layout(
        self,
        nodes: List[CodemapNode],
        edges: List[CodemapEdge]
    ) -> List[CodemapNode]:
        """
        Arrange nodes in concentric circles from a central root.
        """
        if not nodes:
            return nodes
        
        node_map = {node.id: node for node in nodes}
        
        # Build adjacency
        outgoing = defaultdict(set)
        for edge in edges:
            if edge.source in node_map and edge.target in node_map:
                outgoing[edge.source].add(edge.target)
        
        # Find center node (most connections)
        connection_counts = {
            node.id: len(outgoing[node.id]) + sum(1 for e in edges if e.target == node.id)
            for node in nodes
        }
        center_id = max(connection_counts.keys(), key=lambda x: connection_counts[x])
        
        # Assign levels from center using BFS
        levels = {center_id: 0}
        queue = [center_id]
        visited = {center_id}
        
        while queue:
            node_id = queue.pop(0)
            current_level = levels[node_id]
            
            for neighbor in outgoing[node_id]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    levels[neighbor] = current_level + 1
                    queue.append(neighbor)
            
            # Also check incoming edges
            for edge in edges:
                if edge.target == node_id and edge.source not in visited:
                    visited.add(edge.source)
                    levels[edge.source] = current_level + 1
                    queue.append(edge.source)
        
        # Handle unvisited nodes
        max_level = max(levels.values()) if levels else 0
        for node in nodes:
            if node.id not in levels:
                levels[node.id] = max_level + 1
        
        # Group by level
        level_groups = defaultdict(list)
        for node_id, level in levels.items():
            level_groups[level].append(node_id)
        
        # Position nodes in circles
        base_radius = 150
        for level, node_ids in level_groups.items():
            if level == 0:
                # Center node
                for node_id in node_ids:
                    node = node_map.get(node_id)
                    if node:
                        node.x = 0
                        node.y = 0
                        node.width = self.node_width
                        node.height = self.node_height
            else:
                # Nodes in circle
                radius = base_radius * level
                angle_step = 2 * math.pi / max(len(node_ids), 1)
                
                for i, node_id in enumerate(sorted(node_ids)):
                    node = node_map.get(node_id)
                    if node:
                        angle = i * angle_step
                        node.x = radius * math.cos(angle)
                        node.y = radius * math.sin(angle)
                        node.width = self.node_width
                        node.height = self.node_height
        
        return nodes
