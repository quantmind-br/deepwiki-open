"""
Code analyzers for extracting structural information from source code.
"""

from .base import BaseAnalyzer, SymbolInfo, ImportInfo, CallInfo, AnalysisResult
from .python_analyzer import PythonAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer
from .generic_analyzer import GenericAnalyzer


def get_analyzer(language: str = None) -> BaseAnalyzer:
    """
    Get the appropriate analyzer for a language.
    
    Args:
        language: Programming language (python, javascript, typescript, etc.)
                 If None, returns the generic analyzer.
    
    Returns:
        An analyzer instance
    """
    if language is None:
        return GenericAnalyzer()
    
    language = language.lower()
    
    if language in ("python", "py"):
        return PythonAnalyzer()
    elif language in ("javascript", "typescript", "js", "ts", "jsx", "tsx"):
        return JavaScriptAnalyzer()
    else:
        return GenericAnalyzer()


__all__ = [
    "BaseAnalyzer",
    "SymbolInfo",
    "ImportInfo", 
    "CallInfo",
    "AnalysisResult",
    "PythonAnalyzer",
    "JavaScriptAnalyzer",
    "GenericAnalyzer",
    "get_analyzer",
]
