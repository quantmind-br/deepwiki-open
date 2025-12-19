"""
JavaScript/TypeScript analyzer using regex-based parsing.

Note: For production use, consider using tree-sitter for more accurate parsing.
This implementation uses regex patterns for simplicity.
"""

import os
import re
import logging
from typing import List, Dict, Optional

from ..models import SourceLocation, NodeType
from .base import BaseAnalyzer, SymbolInfo, ImportInfo, CallInfo, AnalysisResult

logger = logging.getLogger(__name__)


class JavaScriptAnalyzer(BaseAnalyzer):
    """
    Analyzes JavaScript/TypeScript source code using regex patterns.
    
    Extracts:
    - Classes, functions, arrow functions
    - Import/export statements
    - Function calls
    """
    
    # Regex patterns for JavaScript/TypeScript
    PATTERNS = {
        # Class declarations: class Name extends Base implements Interface
        'class': re.compile(
            r'(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?',
            re.MULTILINE
        ),
        # Function declarations: function name(params)
        'function': re.compile(
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)',
            re.MULTILINE
        ),
        # Arrow functions assigned to const/let/var: const name = (params) =>
        'arrow_function': re.compile(
            r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
            re.MULTILINE
        ),
        # Method definitions in classes: name(params) { or async name(params) {
        'method': re.compile(
            r'^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*{',
            re.MULTILINE
        ),
        # ES6 imports: import { x, y } from 'module'
        'import_named': re.compile(
            r"import\s+{([^}]+)}\s+from\s+['\"]([^'\"]+)['\"]",
            re.MULTILINE
        ),
        # Default imports: import Name from 'module'
        'import_default': re.compile(
            r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
            re.MULTILINE
        ),
        # Side-effect imports: import 'module'
        'import_side_effect': re.compile(
            r"import\s+['\"]([^'\"]+)['\"]",
            re.MULTILINE
        ),
        # CommonJS require: const x = require('module')
        'require': re.compile(
            r"(?:const|let|var)\s+(?:{([^}]+)}|(\w+))\s*=\s*require\s*\(['\"]([^'\"]+)['\"]\)",
            re.MULTILINE
        ),
        # Named exports: export { x, y }
        'export_named': re.compile(
            r'export\s+{([^}]+)}',
            re.MULTILINE
        ),
        # Interface declarations (TypeScript)
        'interface': re.compile(
            r'(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?',
            re.MULTILINE
        ),
        # Type alias declarations (TypeScript)
        'type_alias': re.compile(
            r'(?:export\s+)?type\s+(\w+)\s*=',
            re.MULTILINE
        ),
        # Function calls: name(args)
        'function_call': re.compile(
            r'(\w+(?:\.\w+)*)\s*\([^)]*\)',
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
        js_extensions = ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')
        
        for doc in documents:
            file_path = doc.meta_data.get("file_path", "")
            if not file_path.endswith(js_extensions):
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
        """Analyze a single JavaScript/TypeScript file"""
        self.current_file = relative_path
        
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        return self.analyze_code(source, relative_path)
    
    def analyze_code(self, source: str, relative_path: str) -> AnalysisResult:
        """Analyze JavaScript/TypeScript code from an in-memory string"""
        self.current_file = relative_path
        
        # Determine language from extension
        if relative_path.endswith(('.ts', '.tsx')):
            language = "typescript"
        else:
            language = "javascript"
        
        result = AnalysisResult(file_path=relative_path, language=language)
        
        result.symbols = self._extract_symbols(source)
        result.imports = self._extract_imports(source)
        result.calls = self._extract_calls(source)
        
        return result
    
    def _extract_symbols(self, source: str) -> List[SymbolInfo]:
        """Extract class, function, and interface definitions"""
        symbols = []
        lines = source.split('\n')
        
        # Find classes
        for match in self.PATTERNS['class'].finditer(source):
            name = match.group(1)
            extends = match.group(2)
            implements = match.group(3)
            line_num = source[:match.start()].count('\n') + 1
            
            bases = []
            if extends:
                bases.append(extends)
            if implements:
                bases.extend([i.strip() for i in implements.split(',')])
            
            is_exported = 'export' in source[max(0, match.start()-20):match.start()]
            
            symbols.append(SymbolInfo(
                name=name,
                type=NodeType.CLASS,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                bases=bases,
                is_exported=is_exported
            ))
        
        # Find functions
        for match in self.PATTERNS['function'].finditer(source):
            name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            is_async = 'async' in source[max(0, match.start()-10):match.start()+20]
            is_exported = 'export' in source[max(0, match.start()-20):match.start()]
            
            symbols.append(SymbolInfo(
                name=name,
                type=NodeType.FUNCTION,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                is_async=is_async,
                is_exported=is_exported
            ))
        
        # Find arrow functions
        for match in self.PATTERNS['arrow_function'].finditer(source):
            name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            is_async = 'async' in source[max(0, match.start()-10):match.start()+50]
            is_exported = 'export' in source[max(0, match.start()-20):match.start()]
            
            symbols.append(SymbolInfo(
                name=name,
                type=NodeType.FUNCTION,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                is_async=is_async,
                is_exported=is_exported
            ))
        
        # Find interfaces (TypeScript)
        for match in self.PATTERNS['interface'].finditer(source):
            name = match.group(1)
            extends = match.group(2)
            line_num = source[:match.start()].count('\n') + 1
            
            bases = []
            if extends:
                bases = [e.strip() for e in extends.split(',')]
            
            is_exported = 'export' in source[max(0, match.start()-20):match.start()]
            
            symbols.append(SymbolInfo(
                name=name,
                type=NodeType.INTERFACE,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                bases=bases,
                is_exported=is_exported
            ))
        
        # Find type aliases (TypeScript)
        for match in self.PATTERNS['type_alias'].finditer(source):
            name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            is_exported = 'export' in source[max(0, match.start()-20):match.start()]
            
            symbols.append(SymbolInfo(
                name=name,
                type=NodeType.TYPE,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                is_exported=is_exported
            ))
        
        return symbols
    
    def _extract_imports(self, source: str) -> List[ImportInfo]:
        """Extract import statements"""
        imports = []
        
        # Named imports: import { x, y } from 'module'
        for match in self.PATTERNS['import_named'].finditer(source):
            names_str = match.group(1)
            module = match.group(2)
            line_num = source[:match.start()].count('\n') + 1
            
            names = [n.strip().split(' as ')[0].strip() for n in names_str.split(',')]
            
            imports.append(ImportInfo(
                module=module,
                names=names,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                is_relative=module.startswith('.')
            ))
        
        # Default imports: import Name from 'module'
        for match in self.PATTERNS['import_default'].finditer(source):
            name = match.group(1)
            module = match.group(2)
            line_num = source[:match.start()].count('\n') + 1
            
            # Skip if this is part of a named import (already captured)
            if '{' in source[max(0, match.start()-5):match.end()+5]:
                continue
            
            imports.append(ImportInfo(
                module=module,
                names=[name],
                alias=name,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                is_relative=module.startswith('.')
            ))
        
        # CommonJS require
        for match in self.PATTERNS['require'].finditer(source):
            destructured = match.group(1)
            single = match.group(2)
            module = match.group(3)
            line_num = source[:match.start()].count('\n') + 1
            
            if destructured:
                names = [n.strip() for n in destructured.split(',')]
            else:
                names = [single] if single else []
            
            imports.append(ImportInfo(
                module=module,
                names=names,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                is_relative=module.startswith('.')
            ))
        
        return imports
    
    def _extract_calls(self, source: str) -> List[CallInfo]:
        """Extract function calls"""
        calls = []
        
        # Simple regex-based call extraction
        # This is a simplified approach; a proper implementation would use AST
        for match in self.PATTERNS['function_call'].finditer(source):
            callee = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            
            # Skip common keywords and built-ins that look like function calls
            skip_names = {'if', 'for', 'while', 'switch', 'catch', 'function', 'class', 
                         'import', 'export', 'return', 'new', 'typeof', 'instanceof'}
            if callee.split('.')[0] in skip_names:
                continue
            
            calls.append(CallInfo(
                caller="<module>",  # Without AST, we can't determine the enclosing function
                callee=callee,
                location=SourceLocation(
                    file_path=self.current_file,
                    line_start=line_num,
                    line_end=line_num
                ),
                is_method_call='.' in callee
            ))
        
        return calls
    
    def _resolve_imports(self, results: Dict[str, AnalysisResult], repo_path: str):
        """Resolve relative imports to actual file paths"""
        import os
        
        for file_path, result in results.items():
            file_dir = os.path.dirname(file_path)
            
            for imp in result.imports:
                if not imp.is_relative:
                    continue
                
                # Resolve relative path
                module = imp.module
                if module.startswith('./'):
                    module = module[2:]
                elif module.startswith('../'):
                    parts = module.split('/')
                    up_count = 0
                    for part in parts:
                        if part == '..':
                            up_count += 1
                        else:
                            break
                    
                    dir_parts = file_dir.split('/')
                    if up_count <= len(dir_parts):
                        resolved_dir = '/'.join(dir_parts[:-up_count]) if up_count > 0 else file_dir
                        module = resolved_dir + '/' + '/'.join(parts[up_count:])
                else:
                    module = file_dir + '/' + module
                
                # Try to find the actual file
                for ext in ['', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.ts']:
                    candidate = module + ext
                    if candidate in results:
                        imp.resolved_path = candidate
                        break
