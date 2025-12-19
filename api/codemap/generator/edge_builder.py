"""
Edge builder for creating graph edges from analysis results.
"""

import hashlib
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

from ..models import CodemapEdge, EdgeType
from ..analyzer.base import AnalysisResult, ImportInfo, CallInfo

logger = logging.getLogger(__name__)


@dataclass
class LLMRelationship:
    """Relationship extracted by LLM"""
    source: str
    target: str
    type: EdgeType
    description: str
    importance: str = "medium"


class EdgeBuilder:
    """
    Creates graph edges from code analysis results and LLM-inferred relationships.
    
    Converts ImportInfo and CallInfo objects into CodemapEdge objects,
    and merges with LLM-extracted relationships.
    """
    
    def __init__(self):
        self.edge_map: Dict[str, CodemapEdge] = {}
        self.seen_edges: Set[str] = set()
    
    def build(
        self,
        analysis_results: Dict[str, AnalysisResult],
        llm_relationships: Optional[List[LLMRelationship]] = None
    ) -> List[CodemapEdge]:
        """
        Build edges from analysis results and LLM relationships.
        
        Args:
            analysis_results: Dict of file_path -> AnalysisResult
            llm_relationships: Optional list of LLM-extracted relationships
            
        Returns:
            List of CodemapEdge objects
        """
        self.edge_map = {}
        self.seen_edges = set()
        edges = []
        
        # Build edges from imports
        for file_path, result in analysis_results.items():
            import_edges = self._build_import_edges(file_path, result.imports)
            edges.extend(import_edges)
        
        # Build edges from function calls
        for file_path, result in analysis_results.items():
            call_edges = self._build_call_edges(file_path, result.calls, analysis_results)
            edges.extend(call_edges)
        
        # Build edges from class inheritance
        for file_path, result in analysis_results.items():
            inheritance_edges = self._build_inheritance_edges(result)
            edges.extend(inheritance_edges)
        
        # Build containment edges (file -> symbols)
        for file_path, result in analysis_results.items():
            containment_edges = self._build_containment_edges(file_path, result)
            edges.extend(containment_edges)
        
        # Add LLM-inferred relationships
        if llm_relationships:
            llm_edges = self._build_llm_edges(llm_relationships)
            edges.extend(llm_edges)
        
        return edges
    
    def _build_import_edges(
        self,
        file_path: str,
        imports: List[ImportInfo]
    ) -> List[CodemapEdge]:
        """Create edges from import statements"""
        edges = []
        source_id = f"file:{file_path}"
        
        for imp in imports:
            # Use resolved path if available, otherwise use module name
            if imp.resolved_path:
                target_id = f"file:{imp.resolved_path}"
            else:
                # For external modules, create an external node reference
                target_id = f"external:{imp.module}"
            
            edge_key = f"{source_id}->imports->{target_id}"
            if edge_key in self.seen_edges:
                continue
            self.seen_edges.add(edge_key)
            
            edge = CodemapEdge(
                id=self._make_edge_id(source_id, target_id, EdgeType.IMPORTS),
                source=source_id,
                target=target_id,
                type=EdgeType.IMPORTS,
                label="imports",
                description=f"Imports {imp.module}",
                weight=1.0,
                metadata={
                    "names": imp.names,
                    "is_relative": imp.is_relative
                }
            )
            edges.append(edge)
            self.edge_map[edge.id] = edge
        
        return edges
    
    def _build_call_edges(
        self,
        file_path: str,
        calls: List[CallInfo],
        analysis_results: Dict[str, AnalysisResult]
    ) -> List[CodemapEdge]:
        """Create edges from function calls"""
        edges = []
        
        # Build a map of function names to their node IDs
        func_map = self._build_function_map(analysis_results)
        
        for call in calls:
            # Find source function node
            source_candidates = [
                node_id for name, node_id in func_map.items()
                if name == call.caller or name.endswith(f".{call.caller}")
            ]
            
            # Find target function node
            target_candidates = [
                node_id for name, node_id in func_map.items()
                if name == call.callee or name.endswith(f".{call.callee}")
            ]
            
            # If we can't find exact matches, use file-level nodes
            if not source_candidates:
                source_candidates = [f"file:{file_path}"]
            if not target_candidates:
                # Check if it's a method call on known object
                if call.is_method_call:
                    parts = call.callee.split('.')
                    if len(parts) > 1:
                        method_name = parts[-1]
                        for name, node_id in func_map.items():
                            if name.endswith(f".{method_name}"):
                                target_candidates.append(node_id)
                                break
                
                if not target_candidates:
                    continue  # Skip if we can't resolve the target
            
            for source_id in source_candidates[:1]:  # Take first match
                for target_id in target_candidates[:1]:
                    edge_key = f"{source_id}->calls->{target_id}"
                    if edge_key in self.seen_edges:
                        continue
                    self.seen_edges.add(edge_key)
                    
                    edge = CodemapEdge(
                        id=self._make_edge_id(source_id, target_id, EdgeType.CALLS),
                        source=source_id,
                        target=target_id,
                        type=EdgeType.CALLS,
                        label="calls",
                        description=f"{call.caller} calls {call.callee}",
                        weight=1.5,  # Higher weight for call edges
                        metadata={
                            "arguments": call.arguments
                        }
                    )
                    edges.append(edge)
                    self.edge_map[edge.id] = edge
        
        return edges
    
    def _build_inheritance_edges(self, result: AnalysisResult) -> List[CodemapEdge]:
        """Create edges from class inheritance"""
        edges = []
        
        for symbol in result.symbols:
            if not symbol.bases:
                continue
            
            source_id = self._symbol_to_node_id(symbol, result.file_path)
            
            for base in symbol.bases:
                # Try to find the base class in the same file
                target_symbol = None
                for s in result.symbols:
                    if s.name == base:
                        target_symbol = s
                        break
                
                if target_symbol:
                    target_id = self._symbol_to_node_id(target_symbol, result.file_path)
                else:
                    target_id = f"external:{base}"
                
                edge_key = f"{source_id}->extends->{target_id}"
                if edge_key in self.seen_edges:
                    continue
                self.seen_edges.add(edge_key)
                
                edge = CodemapEdge(
                    id=self._make_edge_id(source_id, target_id, EdgeType.EXTENDS),
                    source=source_id,
                    target=target_id,
                    type=EdgeType.EXTENDS,
                    label="extends",
                    description=f"{symbol.name} extends {base}",
                    weight=2.0  # High weight for inheritance
                )
                edges.append(edge)
                self.edge_map[edge.id] = edge
        
        return edges
    
    def _build_containment_edges(
        self,
        file_path: str,
        result: AnalysisResult
    ) -> List[CodemapEdge]:
        """Create edges showing file contains symbols"""
        edges = []
        file_node_id = f"file:{file_path}"
        
        for symbol in result.symbols:
            symbol_id = self._symbol_to_node_id(symbol, file_path)
            
            edge_key = f"{file_node_id}->contains->{symbol_id}"
            if edge_key in self.seen_edges:
                continue
            self.seen_edges.add(edge_key)
            
            edge = CodemapEdge(
                id=self._make_edge_id(file_node_id, symbol_id, EdgeType.CONTAINS),
                source=file_node_id,
                target=symbol_id,
                type=EdgeType.CONTAINS,
                label="contains",
                weight=0.5  # Lower weight for containment
            )
            edges.append(edge)
            self.edge_map[edge.id] = edge
        
        return edges
    
    def _build_llm_edges(
        self,
        relationships: List[LLMRelationship]
    ) -> List[CodemapEdge]:
        """Create edges from LLM-inferred relationships"""
        edges = []
        
        for rel in relationships:
            edge_key = f"{rel.source}->{rel.type.value}->{rel.target}"
            if edge_key in self.seen_edges:
                continue
            self.seen_edges.add(edge_key)
            
            # Calculate weight based on importance
            weight_map = {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.5}
            weight = weight_map.get(rel.importance, 1.0)
            
            edge = CodemapEdge(
                id=self._make_edge_id(rel.source, rel.target, rel.type),
                source=rel.source,
                target=rel.target,
                type=rel.type,
                label=rel.type.value.replace('_', ' '),
                description=rel.description,
                weight=weight,
                metadata={"source": "llm"}
            )
            edges.append(edge)
            self.edge_map[edge.id] = edge
        
        return edges
    
    def _build_function_map(
        self,
        analysis_results: Dict[str, AnalysisResult]
    ) -> Dict[str, str]:
        """Build a map of function names to node IDs"""
        func_map = {}
        
        for file_path, result in analysis_results.items():
            for symbol in result.symbols:
                node_id = self._symbol_to_node_id(symbol, file_path)
                
                # Add full qualified name
                func_map[f"{file_path}:{symbol.name}"] = node_id
                
                # Add simple name (may cause collisions)
                func_map[symbol.name] = node_id
        
        return func_map
    
    def _symbol_to_node_id(self, symbol, file_path: str) -> str:
        """Convert a symbol to its node ID"""
        components = [
            file_path,
            symbol.type.value,
            symbol.name,
            str(symbol.location.line_start) if symbol.location else "0"
        ]
        unique_str = ":".join(components)
        return f"symbol:{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"
    
    def _make_edge_id(self, source: str, target: str, edge_type: EdgeType) -> str:
        """Generate a unique ID for an edge"""
        unique_str = f"{source}:{edge_type.value}:{target}"
        return f"edge:{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"
