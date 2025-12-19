"""
Base analyzer interface and common data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

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
    is_async: bool = False
    is_exported: bool = False


@dataclass
class ImportInfo:
    """Information about an import statement"""
    module: str
    names: List[str]  # Imported names (empty for 'import module')
    alias: Optional[str] = None
    location: Optional[SourceLocation] = None
    is_relative: bool = False
    resolved_path: Optional[str] = None


@dataclass
class CallInfo:
    """Information about a function call"""
    caller: str  # Function making the call
    callee: str  # Function being called
    location: Optional[SourceLocation] = None
    arguments: List[str] = field(default_factory=list)
    is_method_call: bool = False


@dataclass
class AnalysisResult:
    """Complete analysis result for a file or set of files"""
    symbols: List[SymbolInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    calls: List[CallInfo] = field(default_factory=list)
    file_path: str = ""
    language: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAnalyzer(ABC):
    """
    Abstract base class for code analyzers.
    
    Analyzers extract structural information from source code,
    including symbols, imports, and function calls.
    """
    
    @abstractmethod
    async def analyze(
        self,
        documents: List,
        repo_path: str,
        excluded_dirs: Optional[List[str]] = None,
        excluded_files: Optional[List[str]] = None,
        included_dirs: Optional[List[str]] = None,
        included_files: Optional[List[str]] = None,
        depth: int = 3
    ) -> Dict[str, AnalysisResult]:
        """
        Analyze multiple documents from a repository.
        
        Args:
            documents: List of Document objects from RAG
            repo_path: Path to cloned repository
            excluded_dirs: Directories to exclude
            excluded_files: File patterns to exclude
            included_dirs: Directories to include exclusively
            included_files: File patterns to include exclusively
            depth: Analysis depth
            
        Returns:
            Dict mapping file paths to AnalysisResult
        """
        pass
    
    @abstractmethod
    def analyze_file(self, full_path: str, relative_path: str) -> AnalysisResult:
        """Analyze a single file"""
        pass
    
    @abstractmethod
    def analyze_code(self, source: str, relative_path: str) -> AnalysisResult:
        """Analyze code from an in-memory string"""
        pass
    
    def _should_skip(
        self,
        path: str,
        excluded_dirs: Optional[List[str]],
        excluded_files: Optional[List[str]],
        included_dirs: Optional[List[str]],
        included_files: Optional[List[str]]
    ) -> bool:
        """Check if path should be skipped based on include/exclude rules"""
        if included_dirs or included_files:
            if included_dirs:
                for pattern in included_dirs:
                    if pattern in path:
                        return False
            if included_files:
                for pattern in included_files:
                    if pattern in path:
                        return False
            return True

        if excluded_dirs:
            for pattern in excluded_dirs:
                if pattern in path:
                    return True

        if excluded_files:
            for pattern in excluded_files:
                if pattern in path:
                    return True

        return False
