"""
Node builder for creating graph nodes from analysis results.
"""

import hashlib
import logging
from typing import List, Dict, Optional

from ..models import CodemapNode, NodeType, Importance, SourceLocation, CodeSnippet, QueryIntent
from ..analyzer.base import AnalysisResult, SymbolInfo

logger = logging.getLogger(__name__)


class NodeBuilder:
    """
    Creates graph nodes from code analysis results.
    
    Converts SymbolInfo objects into CodemapNode objects,
    handling deduplication and importance scoring.
    """
    
    def __init__(self):
        self.node_map: Dict[str, CodemapNode] = {}
    
    def build(
        self,
        analysis_results: Dict[str, AnalysisResult],
        query_intent: Optional[QueryIntent] = None
    ) -> List[CodemapNode]:
        """
        Build nodes from analysis results.
        
        Args:
            analysis_results: Dict of file_path -> AnalysisResult
            query_intent: Optional query intent for relevance scoring
            
        Returns:
            List of CodemapNode objects
        """
        self.node_map = {}
        nodes = []
        
        # First pass: Create file nodes
        for file_path, result in analysis_results.items():
            file_node = self._create_file_node(file_path, result)
            nodes.append(file_node)
            self.node_map[file_node.id] = file_node
        
        # Second pass: Create symbol nodes
        for file_path, result in analysis_results.items():
            file_node_id = self._make_file_node_id(file_path)
            
            for symbol in result.symbols:
                symbol_node = self._create_symbol_node(symbol, file_node_id, query_intent)
                if symbol_node.id not in self.node_map:
                    nodes.append(symbol_node)
                    self.node_map[symbol_node.id] = symbol_node
        
        return nodes
    
    def _create_file_node(self, file_path: str, result: AnalysisResult) -> CodemapNode:
        """Create a node for a file"""
        node_id = self._make_file_node_id(file_path)
        
        # Extract file name for label
        parts = file_path.split('/')
        label = parts[-1] if parts else file_path
        
        # Determine importance based on content
        symbol_count = len(result.symbols)
        if symbol_count > 10:
            importance = Importance.HIGH
        elif symbol_count > 5:
            importance = Importance.MEDIUM
        else:
            importance = Importance.LOW
        
        return CodemapNode(
            id=node_id,
            label=label,
            type=NodeType.FILE,
            location=SourceLocation(
                file_path=file_path,
                line_start=1,
                line_end=1
            ),
            description=f"File: {file_path}",
            importance=importance,
            group=self._extract_group(file_path),
            metadata={
                "full_path": file_path,
                "language": result.language,
                "symbol_count": symbol_count
            }
        )
    
    def _create_symbol_node(
        self,
        symbol: SymbolInfo,
        parent_id: str,
        query_intent: Optional[QueryIntent] = None
    ) -> CodemapNode:
        """Create a node for a code symbol"""
        node_id = self._make_symbol_node_id(symbol)
        
        # Determine importance based on symbol characteristics and query relevance
        importance = self._calculate_importance(symbol, query_intent)
        
        # Create snippet if we have location
        snippet = None
        if symbol.docstring:
            snippet = CodeSnippet(
                code=symbol.docstring[:200] + "..." if len(symbol.docstring) > 200 else symbol.docstring,
                language="text"
            )
        
        # Build description
        description = self._build_description(symbol)
        
        return CodemapNode(
            id=node_id,
            label=symbol.name,
            type=symbol.type,
            location=symbol.location,
            description=description,
            importance=importance,
            snippet=snippet,
            parent_id=parent_id,
            group=self._extract_group(symbol.location.file_path) if symbol.location else None,
            metadata={
                "decorators": symbol.decorators,
                "bases": symbol.bases,
                "parameters": symbol.parameters,
                "return_type": symbol.return_type,
                "is_async": symbol.is_async,
                "is_exported": symbol.is_exported
            }
        )
    
    def _calculate_importance(
        self,
        symbol: SymbolInfo,
        query_intent: Optional[QueryIntent] = None
    ) -> Importance:
        """Calculate importance of a symbol"""
        score = 0
        
        # Base score by type
        type_scores = {
            NodeType.CLASS: 3,
            NodeType.INTERFACE: 3,
            NodeType.FUNCTION: 2,
            NodeType.METHOD: 1,
            NodeType.TYPE: 1,
            NodeType.VARIABLE: 0,
            NodeType.CONSTANT: 0,
        }
        score += type_scores.get(symbol.type, 0)
        
        # Bonus for exported symbols
        if symbol.is_exported:
            score += 2
        
        # Bonus for having docstring
        if symbol.docstring:
            score += 1
        
        # Bonus for having inheritance
        if symbol.bases:
            score += 1
        
        # Query relevance scoring
        if query_intent:
            name_lower = symbol.name.lower()
            for keyword in query_intent.keywords:
                if keyword.lower() in name_lower:
                    score += 3
            
            for focus in query_intent.focus_areas:
                if focus.lower() in name_lower:
                    score += 2
        
        # Convert score to importance
        if score >= 7:
            return Importance.CRITICAL
        elif score >= 5:
            return Importance.HIGH
        elif score >= 3:
            return Importance.MEDIUM
        else:
            return Importance.LOW
    
    def _build_description(self, symbol: SymbolInfo) -> str:
        """Build a description string for a symbol"""
        parts = []
        
        if symbol.is_async:
            parts.append("async")
        
        parts.append(symbol.type.value)
        parts.append(symbol.name)
        
        if symbol.parameters:
            params = ", ".join(symbol.parameters[:5])
            if len(symbol.parameters) > 5:
                params += ", ..."
            parts.append(f"({params})")
        
        if symbol.return_type:
            parts.append(f"-> {symbol.return_type}")
        
        if symbol.bases:
            parts.append(f"extends {', '.join(symbol.bases)}")
        
        return " ".join(parts)
    
    def _extract_group(self, file_path: str) -> str:
        """Extract logical group from file path"""
        parts = file_path.split('/')
        
        # Use first significant directory as group
        for part in parts:
            if part and not part.startswith('.') and part not in ('src', 'lib', 'app'):
                return part
        
        return "root"
    
    def _make_file_node_id(self, file_path: str) -> str:
        """Generate a unique ID for a file node"""
        return f"file:{file_path}"
    
    def _make_symbol_node_id(self, symbol: SymbolInfo) -> str:
        """Generate a unique ID for a symbol node"""
        # Use file path + name + line to ensure uniqueness
        components = [
            symbol.location.file_path if symbol.location else "unknown",
            symbol.type.value,
            symbol.name,
            str(symbol.location.line_start) if symbol.location else "0"
        ]
        unique_str = ":".join(components)
        return f"symbol:{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"
    
    def get_node(self, node_id: str) -> Optional[CodemapNode]:
        """Get a node by ID"""
        return self.node_map.get(node_id)
