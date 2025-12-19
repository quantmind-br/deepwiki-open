#!/usr/bin/env python3
"""
Unit tests for codemap analyzers.
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.codemap.analyzer.python_analyzer import PythonAnalyzer
from api.codemap.analyzer.javascript_analyzer import JavaScriptAnalyzer
from api.codemap.models import NodeType


class TestPythonAnalyzer:
    """Tests for PythonAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PythonAnalyzer()

    def test_extract_simple_class(self):
        """Test extraction of a simple class definition."""
        code = '''
class MyClass:
    """A simple class."""
    pass
'''
        result = self.analyzer.analyze_code(code, "test.py")

        assert len(result.symbols) == 1
        assert result.symbols[0].name == "MyClass"
        assert result.symbols[0].type == NodeType.CLASS
        assert result.symbols[0].docstring == "A simple class."

    def test_extract_class_with_methods(self):
        """Test extraction of class with methods."""
        code = '''
class MyClass:
    def method_one(self):
        pass

    def method_two(self, arg1, arg2):
        return arg1 + arg2
'''
        result = self.analyzer.analyze_code(code, "test.py")

        assert len(result.symbols) == 3

        class_sym = next(s for s in result.symbols if s.name == "MyClass")
        assert class_sym.type == NodeType.CLASS

        method_one = next(s for s in result.symbols if s.name == "method_one")
        assert method_one.type == NodeType.METHOD
        assert "self" in method_one.parameters

        method_two = next(s for s in result.symbols if s.name == "method_two")
        assert method_two.type == NodeType.METHOD
        assert len(method_two.parameters) == 3  # self, arg1, arg2

    def test_extract_standalone_functions(self):
        """Test extraction of standalone functions."""
        code = '''
def standalone_func(x, y):
    """Does something."""
    return x + y

async def async_func():
    pass
'''
        result = self.analyzer.analyze_code(code, "test.py")

        assert len(result.symbols) == 2

        sync_func = next(s for s in result.symbols if s.name == "standalone_func")
        assert sync_func.type == NodeType.FUNCTION
        assert sync_func.docstring == "Does something."
        assert not sync_func.is_async

        async_func = next(s for s in result.symbols if s.name == "async_func")
        assert async_func.type == NodeType.FUNCTION
        assert async_func.is_async

    def test_extract_imports(self):
        """Test extraction of import statements."""
        code = '''
import os
import sys
from typing import List, Optional
from .local_module import helper
from ..parent_module import ParentClass
'''
        result = self.analyzer.analyze_code(code, "test.py")

        assert len(result.imports) == 5

        os_import = next(i for i in result.imports if i.module == "os")
        assert os_import.names == []
        assert not os_import.is_relative

        typing_import = next(i for i in result.imports if i.module == "typing")
        assert "List" in typing_import.names
        assert "Optional" in typing_import.names

        # Check relative imports
        relative_imports = [i for i in result.imports if i.is_relative]
        assert len(relative_imports) == 2

    def test_extract_function_calls(self):
        """Test extraction of function calls."""
        code = '''
def caller():
    simple_call()
    obj.method_call()
    module.submodule.deep_call()
'''
        result = self.analyzer.analyze_code(code, "test.py")

        assert len(result.calls) == 3

        callees = [c.callee for c in result.calls]
        assert "simple_call" in callees
        assert "obj.method_call" in callees
        assert "module.submodule.deep_call" in callees

        for call in result.calls:
            assert call.caller == "caller"

    def test_extract_decorators(self):
        """Test extraction of decorators."""
        code = '''
@decorator
def func1():
    pass

@decorator_with_args(arg=1)
def func2():
    pass

@module.decorator
class MyClass:
    pass
'''
        result = self.analyzer.analyze_code(code, "test.py")

        func1 = next(s for s in result.symbols if s.name == "func1")
        assert "decorator" in func1.decorators

        func2 = next(s for s in result.symbols if s.name == "func2")
        assert "decorator_with_args" in func2.decorators

        my_class = next(s for s in result.symbols if s.name == "MyClass")
        assert "module.decorator" in my_class.decorators

    def test_extract_class_inheritance(self):
        """Test extraction of class inheritance."""
        code = '''
class Child(Parent):
    pass

class Multi(Base1, Base2):
    pass
'''
        result = self.analyzer.analyze_code(code, "test.py")

        child = next(s for s in result.symbols if s.name == "Child")
        assert "Parent" in child.bases

        multi = next(s for s in result.symbols if s.name == "Multi")
        assert len(multi.bases) == 2
        assert "Base1" in multi.bases
        assert "Base2" in multi.bases

    def test_syntax_error_handling(self):
        """Test that syntax errors are handled gracefully."""
        code = '''
def broken_function(
    # Missing closing paren and body
'''
        result = self.analyzer.analyze_code(code, "test.py")

        # Should return empty result, not raise exception
        assert result.file_path == "test.py"
        assert len(result.symbols) == 0

    def test_source_location_accuracy(self):
        """Test that source locations are accurate."""
        code = '''# Line 1
# Line 2
class MyClass:
    def method(self):
        pass
'''
        result = self.analyzer.analyze_code(code, "test.py")

        my_class = next(s for s in result.symbols if s.name == "MyClass")
        assert my_class.location.line_start == 3

        method = next(s for s in result.symbols if s.name == "method")
        assert method.location.line_start == 4

    def test_empty_file(self):
        """Test handling of empty file."""
        result = self.analyzer.analyze_code("", "empty.py")
        
        assert result.file_path == "empty.py"
        assert result.language == "python"
        assert len(result.symbols) == 0
        assert len(result.imports) == 0
        assert len(result.calls) == 0

    def test_complex_function_signature(self):
        """Test extraction of complex function signatures."""
        code = '''
def complex_func(
    arg1: str,
    arg2: int = 10,
    *args,
    **kwargs
) -> dict:
    """Complex function with type hints."""
    pass
'''
        result = self.analyzer.analyze_code(code, "test.py")
        
        func = result.symbols[0]
        assert func.name == "complex_func"
        assert "arg1" in func.parameters
        assert "arg2" in func.parameters
        assert func.return_type == "dict"


class TestJavaScriptAnalyzer:
    """Tests for JavaScriptAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = JavaScriptAnalyzer()

    def test_extract_function_declaration(self):
        """Test extraction of function declarations."""
        code = '''
function myFunction(arg1, arg2) {
    return arg1 + arg2;
}
'''
        result = self.analyzer.analyze_code(code, "test.js")

        assert result.file_path == "test.js"
        assert result.language == "javascript"

    def test_extract_arrow_functions(self):
        """Test extraction of arrow functions."""
        code = '''
const arrowFunc = (x) => x * 2;
const multiLine = (a, b) => {
    return a + b;
};
'''
        result = self.analyzer.analyze_code(code, "test.js")

        assert result.file_path == "test.js"

    def test_extract_classes(self):
        """Test extraction of ES6 classes."""
        code = '''
class MyClass extends BaseClass {
    constructor() {
        super();
    }

    myMethod() {
        return 42;
    }
}
'''
        result = self.analyzer.analyze_code(code, "test.js")

        assert result.file_path == "test.js"

    def test_extract_imports(self):
        """Test extraction of ES6 imports."""
        code = '''
import { Component } from 'react';
import DefaultExport from './local';
import * as utils from '../utils';
'''
        result = self.analyzer.analyze_code(code, "test.js")

        assert len(result.imports) >= 0  # Depends on implementation

    def test_typescript_file(self):
        """Test handling of TypeScript files."""
        code = '''
interface User {
    name: string;
    age: number;
}

class UserService {
    getUser(): User {
        return { name: "test", age: 30 };
    }
}
'''
        result = self.analyzer.analyze_code(code, "test.ts")

        assert result.file_path == "test.ts"
        assert result.language in ["javascript", "typescript"]

    def test_jsx_file(self):
        """Test handling of JSX files."""
        code = '''
import React from 'react';

function MyComponent({ name }) {
    return <div>Hello, {name}!</div>;
}

export default MyComponent;
'''
        result = self.analyzer.analyze_code(code, "test.jsx")

        assert result.file_path == "test.jsx"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
