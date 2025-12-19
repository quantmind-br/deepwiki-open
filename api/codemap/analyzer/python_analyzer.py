"""
Python AST analyzer for extracting code structure.
"""

import ast
import os
import logging
from typing import List, Dict, Optional

from ..models import SourceLocation, NodeType
from .base import BaseAnalyzer, SymbolInfo, ImportInfo, CallInfo, AnalysisResult

logger = logging.getLogger(__name__)


class PythonAnalyzer(BaseAnalyzer):
    """
    Analyzes Python source code using AST.
    
    Extracts:
    - Classes, functions, methods
    - Import relationships
    - Function calls
    - Inheritance hierarchies
    """
    
    def __init__(self):
        self.current_file: str = ""
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
    
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
        """
        results = {}
        
        for doc in documents:
            file_path = doc.meta_data.get("file_path", "")
            if not file_path.endswith(".py"):
                continue
            
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
        
        self._resolve_imports(results, repo_path)
        
        return results
    
    def analyze_file(self, full_path: str, relative_path: str) -> AnalysisResult:
        """Analyze a single Python file"""
        self.current_file = relative_path
        
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        return self.analyze_code(source, relative_path)
    
    def analyze_code(self, source: str, relative_path: str) -> AnalysisResult:
        """Analyze Python code from an in-memory string"""
        self.current_file = relative_path
        
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {relative_path}: {e}")
            return AnalysisResult(file_path=relative_path, language="python")
        
        result = AnalysisResult(file_path=relative_path, language="python")
        
        result.symbols = self._extract_symbols(tree)
        result.imports = self._extract_imports(tree)
        result.calls = self._extract_calls(tree)
        
        return result
    
    def _extract_symbols(self, tree: ast.AST) -> List[SymbolInfo]:
        """Extract class and function definitions"""
        symbols = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append(SymbolInfo(
                    name=node.name,
                    type=NodeType.CLASS,
                    location=SourceLocation(
                        file_path=self.current_file,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        column_start=node.col_offset,
                        column_end=node.end_col_offset
                    ),
                    docstring=ast.get_docstring(node),
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    bases=[self._get_name(b) for b in node.bases]
                ))
                
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_method = self._is_inside_class(node, tree)
                is_async = isinstance(node, ast.AsyncFunctionDef)
                
                symbols.append(SymbolInfo(
                    name=node.name,
                    type=NodeType.METHOD if is_method else NodeType.FUNCTION,
                    location=SourceLocation(
                        file_path=self.current_file,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        column_start=node.col_offset,
                        column_end=node.end_col_offset
                    ),
                    docstring=ast.get_docstring(node),
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    parameters=[arg.arg for arg in node.args.args],
                    return_type=self._get_annotation(node.returns),
                    is_async=is_async
                ))
        
        return symbols
    
    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """Extract import statements"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[],
                        alias=alias.asname,
                        location=SourceLocation(
                            file_path=self.current_file,
                            line_start=node.lineno,
                            line_end=node.lineno
                        )
                    ))
                    
            elif isinstance(node, ast.ImportFrom):
                imports.append(ImportInfo(
                    module=node.module or "",
                    names=[alias.name for alias in node.names],
                    alias=node.names[0].asname if len(node.names) == 1 else None,
                    location=SourceLocation(
                        file_path=self.current_file,
                        line_start=node.lineno,
                        line_end=node.lineno
                    ),
                    is_relative=node.level > 0
                ))
        
        return imports
    
    def _extract_calls(self, tree: ast.AST) -> List[CallInfo]:
        """Extract function calls"""
        calls = []
        
        class CallVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.current_func = None
            
            def visit_FunctionDef(self, node):
                old_func = self.current_func
                self.current_func = node.name
                self.generic_visit(node)
                self.current_func = old_func
            
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)
            
            def visit_Call(self, node):
                if self.current_func:
                    callee = self.analyzer._get_call_name(node)
                    if callee:
                        calls.append(CallInfo(
                            caller=self.current_func,
                            callee=callee,
                            location=SourceLocation(
                                file_path=self.analyzer.current_file,
                                line_start=node.lineno,
                                line_end=node.lineno
                            ),
                            is_method_call="." in callee
                        ))
                self.generic_visit(node)
        
        visitor = CallVisitor(self)
        visitor.visit(tree)
        
        return calls
    
    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Get the name of a called function"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None
    
    def _get_decorator_name(self, node) -> str:
        """Get decorator name as string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return ""
    
    def _get_name(self, node) -> str:
        """Get name from various node types"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        return ""
    
    def _get_annotation(self, node) -> Optional[str]:
        """Get type annotation as string"""
        if node is None:
            return None
        return self._get_name(node)
    
    def _is_inside_class(self, func_node, tree) -> bool:
        """Check if a function is a method inside a class"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item is func_node:
                        return True
        return False
    
    def _resolve_imports(self, results: Dict[str, AnalysisResult], repo_path: str):
        """Resolve imports to actual file paths"""
        module_map = {}
        for file_path in results.keys():
            module_name = file_path.replace("/", ".").replace(".py", "")
            module_map[module_name] = file_path
        
        for result in results.values():
            for imp in result.imports:
                if imp.module in module_map:
                    imp.resolved_path = module_map[imp.module]
