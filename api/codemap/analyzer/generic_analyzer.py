"""
Generic analyzer for languages without specific support.

Uses simple heuristics and regex patterns to extract basic structure.
"""

import os
import re
import logging
from typing import List, Dict, Optional

from ..models import SourceLocation, NodeType
from .base import BaseAnalyzer, SymbolInfo, ImportInfo, CallInfo, AnalysisResult

logger = logging.getLogger(__name__)


class GenericAnalyzer(BaseAnalyzer):
    """
    Generic analyzer that works with any text-based source file.
    
    Uses regex patterns to find common code structures:
    - Function/method definitions
    - Class definitions
    - Import statements
    """
    
    # Language detection by extension
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.cs': 'csharp',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.sql': 'sql',
        '.sh': 'bash',
        '.md': 'markdown',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
    }
    
    # Generic patterns that work across many languages
    PATTERNS = {
        # Function-like patterns: func name(, function name(, def name(, fn name(
        'function': re.compile(
            r'(?:^|\s)(?:pub(?:lic)?\s+)?(?:static\s+)?(?:async\s+)?'
            r'(?:def|func|function|fn|fun|sub|proc|method)\s+'
            r'(\w+)\s*\(',
            re.MULTILINE
        ),
        # Class-like patterns: class Name, struct Name, type Name struct
        'class': re.compile(
            r'(?:^|\s)(?:pub(?:lic)?\s+)?(?:abstract\s+)?'
            r'(?:class|struct|interface|trait|enum|type)\s+'
            r'(\w+)',
            re.MULTILINE
        ),
        # Import-like patterns: import, include, require, use, from...import
        'import': re.compile(
            r'(?:^|\s)(?:import|include|require|use|using|from)\s+'
            r'["\']?([^\s"\';\n]+)',
            re.MULTILINE
        ),
    }
    
    def __init__(self):
        self.current_file: str = ""
    
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
        """Analyze multiple documents from a repository."""
        results = {}
        
        for doc in documents:
            file_path = doc.meta_data.get("file_path", "")
            
            if self._should_skip(file_path, excluded_dirs, excluded_files, included_dirs, included_files):
                continue
            
            full_path = os.path.join(repo_path, file_path)
            if os.path.exists(full_path):
                try:
                    result = self.analyze_file(full_path, file_path)
                    results[file_path] = result
                except Exception as e:
                    logger.warning(f"Error analyzing {file_path}: {e}")
                    continue
        
        return results
    
    def analyze_file(self, full_path: str, relative_path: str) -> AnalysisResult:
        """Analyze a single file"""
        self.current_file = relative_path
        
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        return self.analyze_code(source, relative_path)
    
    def analyze_code(self, source: str, relative_path: str) -> AnalysisResult:
        """Analyze code from an in-memory string"""
        self.current_file = relative_path
        
        # Detect language from extension
        ext = os.path.splitext(relative_path)[1].lower()
        language = self.LANGUAGE_MAP.get(ext, 'unknown')
        
        result = AnalysisResult(file_path=relative_path, language=language)
        
        result.symbols = self._extract_symbols(source)
        result.imports = self._extract_imports(source)
        result.calls = self._extract_calls(source)
        
        return result
    
    def _extract_symbols(self, source: str) -> List[SymbolInfo]:
        """Extract symbol definitions using generic patterns"""
        symbols = []
        
        # Find functions
        for match in self.PATTERNS['function'].finditer(source):
            name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            
            symbols.append(SymbolInfo(
                name=name,
                type=NodeType.FUNCTION,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                )
            ))
        
        # Find classes/structs
        for match in self.PATTERNS['class'].finditer(source):
            name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            
            # Determine if it's a class or interface based on keyword
            match_text = match.group(0).lower()
            if 'interface' in match_text or 'trait' in match_text:
                node_type = NodeType.INTERFACE
            elif 'enum' in match_text:
                node_type = NodeType.TYPE
            else:
                node_type = NodeType.CLASS
            
            symbols.append(SymbolInfo(
                name=name,
                type=node_type,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                )
            ))
        
        return symbols
    
    def _extract_imports(self, source: str) -> List[ImportInfo]:
        """Extract import statements using generic patterns"""
        imports = []
        
        for match in self.PATTERNS['import'].finditer(source):
            module = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            
            # Clean up the module name
            module = module.strip('"\'<>;')
            
            imports.append(ImportInfo(
                module=module,
                names=[],
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                is_relative=module.startswith('.')
            ))
        
        return imports
    
    def _extract_calls(self, source: str) -> List[CallInfo]:
        """Extract function calls - limited in generic mode"""
        # Generic call extraction is unreliable without proper parsing
        # Return empty list to avoid noise
        return []
