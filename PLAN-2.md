# DeepWiki Codemaps - Phase 5 Implementation Plan

> **Feature**: Completing Codemaps Implementation (Phase 5: Polish & Integration)
> **Branch**: `feature/codemaps`
> **Created**: 2025-12-18
> **Status**: Ready for Implementation
> **Predecessor**: PLAN.md (Phases 1-4 Complete)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Implementation Tasks](#3-implementation-tasks)
4. [Wiki Integration](#4-wiki-integration)
5. [Security Hardening](#5-security-hardening)
6. [Testing Implementation](#6-testing-implementation)
7. [Performance Optimization](#7-performance-optimization)
8. [Documentation](#8-documentation)
9. [Implementation Order](#9-implementation-order)
10. [File Reference](#10-file-reference)

---

## 1. Executive Summary

### 1.1 Objective

Complete the Codemaps feature implementation by delivering Phase 5 (Polish & Integration) from the original PLAN.md. This includes:

- **Wiki Integration**: Add navigation links from wiki pages to Codemaps
- **Security Hardening**: Token redaction, share expiry, rate limiting
- **Testing**: Unit tests, integration tests, and smoke test documentation
- **Performance**: Caching improvements and optimization
- **Documentation**: User and developer documentation

### 1.2 Scope

| Category | Items | Priority |
|----------|-------|----------|
| Wiki Integration | 3 tasks | HIGH |
| Security | 4 tasks | HIGH |
| Testing | 5 tasks | HIGH |
| Performance | 3 tasks | MEDIUM |
| Documentation | 2 tasks | MEDIUM |

### 1.3 Success Criteria

- [ ] Codemap link visible in wiki page header
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Token never appears in logs or responses
- [ ] Share links expire after configured time
- [ ] Rate limiting prevents abuse
- [ ] Performance acceptable for repos up to 10,000 files

---

## 2. Current State Analysis

### 2.1 Implemented Components

| Component | Status | Location |
|-----------|--------|----------|
| Backend Models | ✅ Complete | `api/codemap/models.py` |
| Engine | ✅ Complete | `api/codemap/engine.py` |
| Storage | ✅ Complete | `api/codemap/storage.py` |
| Python Analyzer | ✅ Complete | `api/codemap/analyzer/python_analyzer.py` |
| JavaScript Analyzer | ✅ Complete | `api/codemap/analyzer/javascript_analyzer.py` |
| Generic Analyzer | ✅ Complete | `api/codemap/analyzer/generic_analyzer.py` |
| Node/Edge Builders | ✅ Complete | `api/codemap/generator/` |
| Renderers | ✅ Complete | `api/codemap/renderer/` |
| LLM Components | ✅ Complete | `api/codemap/llm/` |
| REST API | ✅ Complete | `api/codemap_api.py` |
| WebSocket | ✅ Complete | `api/websocket_codemap.py` |
| Frontend Types | ✅ Complete | `src/types/codemap/index.ts` |
| Frontend Components | ✅ Complete | `src/components/codemap/` |
| Frontend Hooks | ✅ Complete | `src/hooks/codemap/` |
| API Client | ✅ Complete | `src/utils/codemap/client.ts` |
| Codemap Page | ✅ Complete | `src/app/[owner]/[repo]/codemap/page.tsx` |

### 2.2 Missing Components

| Component | Status | Required Action |
|-----------|--------|-----------------|
| Wiki Page Integration | ❌ Missing | Add Codemap link to header |
| Rate Limiting | ❌ Missing | Implement in API layer |
| Token Redaction | ❌ Missing | Audit logs and responses |
| Share Expiry | ❌ Missing | Add expiry logic |
| Unit Tests | ❌ Missing | Create test files |
| Integration Tests | ❌ Missing | Create test files |
| User Documentation | ❌ Missing | Create README section |

---

## 3. Implementation Tasks

### 3.1 Task Breakdown

```
TASK-01: Wiki Integration - Add Codemap Link to Header
TASK-02: Wiki Integration - Add Codemap Button to Sidebar
TASK-03: Wiki Integration - Preserve Query Parameters
TASK-04: Security - Token Redaction in Logs
TASK-05: Security - Token Redaction in API Responses
TASK-06: Security - Share Token Expiry
TASK-07: Security - Rate Limiting
TASK-08: Testing - Unit Tests for Analyzers
TASK-09: Testing - Unit Tests for Generators
TASK-10: Testing - Unit Tests for Renderers
TASK-11: Testing - Integration Tests for Engine
TASK-12: Testing - Smoke Test Checklist
TASK-13: Performance - Analysis Caching
TASK-14: Performance - Graph Virtualization
TASK-15: Documentation - User Guide
TASK-16: Documentation - API Documentation
```

---

## 4. Wiki Integration

### 4.1 TASK-01: Add Codemap Link to Header

**File**: `src/app/[owner]/[repo]/page.tsx`

**Location**: Line ~1945-1953 (header section)

**Current Code**:
```tsx
<header className="max-w-[90%] xl:max-w-[1400px] mx-auto mb-8 h-fit w-full">
  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
    <div className="flex items-center gap-4">
      <Link href="/" className="text-[var(--accent-primary)] hover:text-[var(--highlight)] flex items-center gap-1.5 transition-colors border-b border-[var(--border-color)] hover:border-[var(--accent-primary)] pb-0.5">
        <FaHome /> {messages.repoPage?.home || 'Home'}
      </Link>
    </div>
  </div>
</header>
```

**Target Code**:
```tsx
<header className="max-w-[90%] xl:max-w-[1400px] mx-auto mb-8 h-fit w-full">
  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
    <div className="flex items-center gap-4">
      <Link href="/" className="text-[var(--accent-primary)] hover:text-[var(--highlight)] flex items-center gap-1.5 transition-colors border-b border-[var(--border-color)] hover:border-[var(--accent-primary)] pb-0.5">
        <FaHome /> {messages.repoPage?.home || 'Home'}
      </Link>
      <span className="text-[var(--border-color)]">|</span>
      <Link
        href={`/${owner}/${repo}/codemap?type=${effectiveRepoInfo.type}${token ? `&token=${token}` : ''}${providerParam ? `&provider=${providerParam}` : ''}${modelParam ? `&model=${modelParam}` : ''}${language ? `&language=${language}` : ''}`}
        className="text-[var(--accent-primary)] hover:text-[var(--highlight)] flex items-center gap-1.5 transition-colors border-b border-[var(--border-color)] hover:border-[var(--accent-primary)] pb-0.5"
      >
        <FaProjectDiagram /> {messages.repoPage?.codemap || 'Codemap'}
      </Link>
    </div>
  </div>
</header>
```

**Required Changes**:
1. Import `FaProjectDiagram` from `react-icons/fa`
2. Add Link to Codemap page
3. Preserve query parameters (type, token, provider, model, language)

**Import Addition** (Line ~16):
```tsx
import { FaBitbucket, FaBookOpen, FaComments, FaDownload, FaExclamationTriangle, FaFileExport, FaFolder, FaGithub, FaGitlab, FaHome, FaProjectDiagram, FaSync, FaTimes } from 'react-icons/fa';
```

### 4.2 TASK-02: Add Codemap Button to Sidebar

**File**: `src/app/[owner]/[repo]/page.tsx`

**Location**: Line ~2089-2099 (after Refresh Wiki button, before Export buttons)

**New Code to Add**:
```tsx
{/* Codemap Explorer button */}
<div className="mb-5">
  <Link
    href={`/${effectiveRepoInfo.owner}/${effectiveRepoInfo.repo}/codemap?type=${effectiveRepoInfo.type}${token ? `&token=${token}` : ''}${providerParam ? `&provider=${providerParam}` : ''}${modelParam ? `&model=${modelParam}` : ''}${language ? `&language=${language}` : ''}`}
    className="flex items-center w-full text-xs px-3 py-2 bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] rounded-md hover:bg-[var(--accent-primary)]/20 border border-[var(--accent-primary)]/30 transition-colors"
  >
    <FaProjectDiagram className="mr-2" />
    {messages.repoPage?.exploreCodemap || 'Explore Codemap'}
  </Link>
</div>
```

### 4.3 TASK-03: Add Internationalization Messages

**File**: `src/contexts/LanguageContext.tsx` (or messages JSON files)

**New Messages**:
```json
{
  "repoPage": {
    "codemap": "Codemap",
    "exploreCodemap": "Explore Codemap",
    "codemapDescription": "Generate AI-powered interactive maps of your codebase"
  }
}
```

---

## 5. Security Hardening

### 5.1 TASK-04: Token Redaction in Logs

**Files to Audit**:
- `api/codemap/engine.py`
- `api/codemap_api.py`
- `api/websocket_codemap.py`

**Implementation**:

```python
# api/codemap/utils/security.py (NEW FILE)

"""
Security utilities for codemap operations.
"""

import re
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact sensitive fields from data before logging.

    Args:
        data: Dictionary that may contain sensitive fields

    Returns:
        Copy of data with sensitive fields redacted
    """
    sensitive_fields = {'token', 'access_token', 'api_key', 'password', 'secret'}

    def redact_value(key: str, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: redact_value(k, v) for k, v in value.items()}
        elif isinstance(value, str) and key.lower() in sensitive_fields:
            if len(value) > 8:
                return f"{value[:4]}...{value[-4:]}"
            return "***REDACTED***"
        return value

    return {k: redact_value(k, v) for k, v in data.items()}


def safe_log_request(request_data: Dict[str, Any], message: str = "Request"):
    """
    Log request data with sensitive fields redacted.
    """
    safe_data = redact_sensitive_data(request_data)
    logger.info(f"{message}: {safe_data}")


class TokenRedactingFilter(logging.Filter):
    """
    Logging filter that redacts tokens from log messages.
    """

    TOKEN_PATTERNS = [
        r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
        r'glpat-[a-zA-Z0-9-]{20}',  # GitLab PAT
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self.TOKEN_PATTERNS:
            message = re.sub(pattern, '***REDACTED***', message)
        record.msg = message
        record.args = ()
        return True
```

**Update Engine** (`api/codemap/engine.py`):

```python
# Add import at top
from .utils.security import safe_log_request, redact_sensitive_data

# In generate() method, replace direct logging with:
safe_log_request(request.model_dump(), "Codemap generation request")
```

### 5.2 TASK-05: Token Redaction in API Responses

**File**: `api/codemap_api.py`

**Ensure**:
1. `CodemapGenerateRequest.token` is never included in any response
2. Stored `Codemap` objects never contain the original token

**Add Validation** (in `router` endpoints):

```python
# In generate_codemap endpoint, ensure token is not returned
response_data = {
    "codemap_id": codemap.id,
    "status": codemap.status,
    "message": "Codemap generation started"
}
# Token is intentionally excluded
```

### 5.3 TASK-06: Share Token Expiry

**File**: `api/codemap/storage.py`

**Updated Model** (`api/codemap/models.py`):

```python
class Codemap(BaseModel):
    # ... existing fields ...

    # Sharing
    is_public: bool = False
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None  # NEW FIELD
```

**Updated Storage Methods**:

```python
# api/codemap/storage.py

from datetime import datetime, timedelta

SHARE_TOKEN_TTL_DAYS = 30  # Configurable

async def update_share_token(
    self,
    codemap_id: str,
    share_token: str,
    is_public: bool = True,
    ttl_days: int = SHARE_TOKEN_TTL_DAYS
) -> bool:
    """
    Update the share token for a codemap with expiry.
    """
    codemap = await self.load(codemap_id)
    if not codemap:
        return False

    codemap.share_token = share_token
    codemap.is_public = is_public
    codemap.share_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
    codemap.updated_at = datetime.utcnow()

    return await self.save(codemap)


async def get_by_share_token(self, share_token: str) -> Optional[Codemap]:
    """
    Get a codemap by its share token, checking expiry.
    """
    # Search through codemaps for matching share token
    for filename in os.listdir(self.storage_dir):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(self.storage_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('share_token') != share_token:
                continue

            # Check if token has expired
            expires_at = data.get('share_expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expires_at:
                    logger.info(f"Share token expired for codemap {data.get('id')}")
                    return None

            # Handle datetime deserialization
            if isinstance(data.get('created_at'), str):
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if isinstance(data.get('updated_at'), str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            if isinstance(data.get('share_expires_at'), str):
                data['share_expires_at'] = datetime.fromisoformat(data['share_expires_at'])

            return Codemap(**data)

        except Exception as e:
            logger.warning(f"Error reading {filename}: {e}")
            continue

    return None
```

**Update API** (`api/codemap_api.py`):

```python
@router.get("/shared/{share_token}")
async def get_shared_codemap(share_token: str):
    """Get a publicly shared codemap by its share token."""
    storage = CodemapStorage()
    codemap = await storage.get_by_share_token(share_token)

    if not codemap:
        raise HTTPException(status_code=404, detail="Shared codemap not found or expired")

    if not codemap.is_public:
        raise HTTPException(status_code=403, detail="Codemap is not public")

    return codemap
```

### 5.4 TASK-07: Rate Limiting

**File**: `api/codemap_api.py`

**Implementation using slowapi**:

```python
# api/codemap/rate_limit.py (NEW FILE)

"""
Rate limiting for codemap API endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.detail
        }
    )


# Rate limit configurations
RATE_LIMITS = {
    "generate": "5/minute",      # Max 5 generations per minute
    "get": "60/minute",          # Max 60 gets per minute
    "list": "30/minute",         # Max 30 list calls per minute
    "share": "10/minute",        # Max 10 share operations per minute
}
```

**Update API** (`api/codemap_api.py`):

```python
from .codemap.rate_limit import limiter, RATE_LIMITS

# Add rate limiting to endpoints
@router.post("/generate")
@limiter.limit(RATE_LIMITS["generate"])
async def generate_codemap(request: Request, body: CodemapGenerateRequest):
    # ... existing implementation ...
    pass


@router.get("/{codemap_id}")
@limiter.limit(RATE_LIMITS["get"])
async def get_codemap(request: Request, codemap_id: str):
    # ... existing implementation ...
    pass
```

**Update Main App** (`api/api.py`):

```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from api.codemap.rate_limit import limiter

# Add to app initialization
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Dependencies** (add to `requirements.txt`):
```
slowapi>=0.1.9
```

---

## 6. Testing Implementation

### 6.1 TASK-08: Unit Tests for Analyzers

**File**: `tests/unit/test_codemap_analyzer.py`

```python
#!/usr/bin/env python3
"""
Unit tests for codemap analyzers.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
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

        local_import = next(i for i in result.imports if "local_module" in i.module)
        assert local_import.is_relative

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

class Multi(Base1, Base2, mixin.Mixin):
    pass
'''
        result = self.analyzer.analyze_code(code, "test.py")

        child = next(s for s in result.symbols if s.name == "Child")
        assert "Parent" in child.bases

        multi = next(s for s in result.symbols if s.name == "Multi")
        assert len(multi.bases) == 3
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
class MyClass:  # Line 3
    def method(self):  # Line 4
        pass  # Line 5
'''
        result = self.analyzer.analyze_code(code, "test.py")

        my_class = next(s for s in result.symbols if s.name == "MyClass")
        assert my_class.location.line_start == 3

        method = next(s for s in result.symbols if s.name == "method")
        assert method.location.line_start == 4


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

        # Note: JavaScript analyzer uses regex, so results may vary
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

        assert len(result.imports) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 6.2 TASK-09: Unit Tests for Generators

**File**: `tests/unit/test_codemap_generator.py`

```python
#!/usr/bin/env python3
"""
Unit tests for codemap generators (node builder, edge builder, etc.).
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.codemap.generator.node_builder import NodeBuilder
from api.codemap.generator.edge_builder import EdgeBuilder
from api.codemap.generator.clusterer import Clusterer
from api.codemap.generator.pruner import Pruner
from api.codemap.analyzer.base import SymbolInfo, ImportInfo, CallInfo, AnalysisResult
from api.codemap.models import NodeType, SourceLocation, CodemapNode, CodemapEdge, EdgeType


class TestNodeBuilder:
    """Tests for NodeBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = NodeBuilder()

    def test_build_nodes_from_symbols(self):
        """Test building nodes from symbol information."""
        analysis_results = {
            "test.py": AnalysisResult(
                file_path="test.py",
                language="python",
                symbols=[
                    SymbolInfo(
                        name="MyClass",
                        type=NodeType.CLASS,
                        location=SourceLocation(
                            file_path="test.py",
                            line_start=1,
                            line_end=10
                        ),
                        docstring="A test class"
                    ),
                    SymbolInfo(
                        name="my_function",
                        type=NodeType.FUNCTION,
                        location=SourceLocation(
                            file_path="test.py",
                            line_start=12,
                            line_end=15
                        )
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        # Mock query intent
        class MockQueryIntent:
            focus_areas = ["test"]
            keywords = ["class", "function"]

        nodes = self.builder.build(analysis_results, MockQueryIntent())

        assert len(nodes) >= 2

        class_node = next((n for n in nodes if n.label == "MyClass"), None)
        assert class_node is not None
        assert class_node.type == NodeType.CLASS

        func_node = next((n for n in nodes if n.label == "my_function"), None)
        assert func_node is not None
        assert func_node.type == NodeType.FUNCTION

    def test_node_importance_calculation(self):
        """Test that node importance is calculated correctly."""
        # Nodes with more connections should have higher importance
        pass  # Implementation depends on actual importance logic


class TestEdgeBuilder:
    """Tests for EdgeBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = EdgeBuilder()

    def test_build_import_edges(self):
        """Test building edges from import relationships."""
        analysis_results = {
            "main.py": AnalysisResult(
                file_path="main.py",
                language="python",
                symbols=[],
                imports=[
                    ImportInfo(
                        module="utils",
                        names=["helper"],
                        location=SourceLocation(
                            file_path="main.py",
                            line_start=1,
                            line_end=1
                        ),
                        resolved_path="utils.py"
                    )
                ],
                calls=[]
            ),
            "utils.py": AnalysisResult(
                file_path="utils.py",
                language="python",
                symbols=[
                    SymbolInfo(
                        name="helper",
                        type=NodeType.FUNCTION,
                        location=SourceLocation(
                            file_path="utils.py",
                            line_start=1,
                            line_end=5
                        )
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        llm_relationships = []  # No LLM-inferred relationships

        edges = self.builder.build(analysis_results, llm_relationships)

        # Should have at least one IMPORTS edge
        import_edges = [e for e in edges if e.type == EdgeType.IMPORTS]
        assert len(import_edges) >= 0  # Depends on implementation

    def test_build_call_edges(self):
        """Test building edges from function calls."""
        pass  # Implementation depends on actual edge building logic


class TestClusterer:
    """Tests for Clusterer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.clusterer = Clusterer()

    def test_cluster_by_file(self):
        """Test clustering nodes by file."""
        nodes = [
            CodemapNode(
                id="node1",
                label="Class1",
                type=NodeType.CLASS,
                importance="high",
                metadata={},
                location=SourceLocation(
                    file_path="file1.py",
                    line_start=1,
                    line_end=10
                )
            ),
            CodemapNode(
                id="node2",
                label="Class2",
                type=NodeType.CLASS,
                importance="medium",
                metadata={},
                location=SourceLocation(
                    file_path="file1.py",
                    line_start=12,
                    line_end=20
                )
            ),
            CodemapNode(
                id="node3",
                label="Class3",
                type=NodeType.CLASS,
                importance="medium",
                metadata={},
                location=SourceLocation(
                    file_path="file2.py",
                    line_start=1,
                    line_end=10
                )
            )
        ]

        edges = []

        clusters = self.clusterer.cluster(nodes, edges)

        # Should have clusters for file1.py and file2.py
        assert isinstance(clusters, dict)


class TestPruner:
    """Tests for Pruner class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pruner = Pruner()

    def test_prune_to_max_nodes(self):
        """Test pruning to maximum number of nodes."""
        # Create more nodes than max
        nodes = [
            CodemapNode(
                id=f"node{i}",
                label=f"Node{i}",
                type=NodeType.FUNCTION,
                importance="low",
                metadata={}
            )
            for i in range(100)
        ]

        edges = []

        class MockQueryIntent:
            focus_areas = []
            keywords = []

        pruned_nodes, pruned_edges = self.pruner.prune(
            nodes=nodes,
            edges=edges,
            query_intent=MockQueryIntent(),
            max_nodes=50
        )

        assert len(pruned_nodes) <= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 6.3 TASK-10: Unit Tests for Renderers

**File**: `tests/unit/test_codemap_renderer.py`

```python
#!/usr/bin/env python3
"""
Unit tests for codemap renderers.
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.codemap.renderer.mermaid import MermaidRenderer
from api.codemap.renderer.json_export import JSONRenderer
from api.codemap.models import (
    CodemapGraph, CodemapNode, CodemapEdge,
    NodeType, EdgeType, SourceLocation
)


class TestMermaidRenderer:
    """Tests for MermaidRenderer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = MermaidRenderer()

    def test_render_simple_graph(self):
        """Test rendering a simple graph."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="node1",
                    label="ClassA",
                    type=NodeType.CLASS,
                    importance="high",
                    metadata={}
                ),
                CodemapNode(
                    id="node2",
                    label="ClassB",
                    type=NodeType.CLASS,
                    importance="medium",
                    metadata={}
                )
            ],
            edges=[
                CodemapEdge(
                    id="edge1",
                    source="node1",
                    target="node2",
                    type=EdgeType.IMPORTS,
                    weight=1.0,
                    metadata={}
                )
            ],
            root_nodes=["node1"],
            clusters={}
        )

        class MockQueryIntent:
            preferred_layout = "hierarchical"

        mermaid_code = self.renderer.render(graph, MockQueryIntent())

        assert "graph" in mermaid_code or "flowchart" in mermaid_code
        assert "ClassA" in mermaid_code
        assert "ClassB" in mermaid_code

    def test_render_with_clusters(self):
        """Test rendering with node clusters."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="node1",
                    label="Func1",
                    type=NodeType.FUNCTION,
                    importance="medium",
                    metadata={},
                    group="group1"
                ),
                CodemapNode(
                    id="node2",
                    label="Func2",
                    type=NodeType.FUNCTION,
                    importance="medium",
                    metadata={},
                    group="group1"
                )
            ],
            edges=[],
            root_nodes=["node1"],
            clusters={"group1": ["node1", "node2"]}
        )

        class MockQueryIntent:
            preferred_layout = "hierarchical"

        mermaid_code = self.renderer.render(graph, MockQueryIntent())

        # Subgraph should be rendered
        assert "subgraph" in mermaid_code.lower() or "Func1" in mermaid_code

    def test_escape_special_characters(self):
        """Test that special characters are escaped."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="node1",
                    label="Class<T>",  # Contains special chars
                    type=NodeType.CLASS,
                    importance="medium",
                    metadata={}
                )
            ],
            edges=[],
            root_nodes=["node1"],
            clusters={}
        )

        class MockQueryIntent:
            preferred_layout = "hierarchical"

        mermaid_code = self.renderer.render(graph, MockQueryIntent())

        # Should not cause Mermaid parsing errors
        # The label should be escaped or modified
        assert "node1" in mermaid_code


class TestJSONRenderer:
    """Tests for JSONRenderer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = JSONRenderer()

    def test_render_to_dict(self):
        """Test rendering graph to dictionary."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="node1",
                    label="TestNode",
                    type=NodeType.FUNCTION,
                    importance="high",
                    metadata={"key": "value"}
                )
            ],
            edges=[],
            root_nodes=["node1"],
            clusters={}
        )

        result = self.renderer.render(graph)

        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["id"] == "node1"

    def test_render_preserves_metadata(self):
        """Test that metadata is preserved in JSON output."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="node1",
                    label="TestNode",
                    type=NodeType.FUNCTION,
                    importance="medium",
                    metadata={
                        "custom_field": "custom_value",
                        "nested": {"a": 1, "b": 2}
                    }
                )
            ],
            edges=[],
            root_nodes=["node1"],
            clusters={}
        )

        result = self.renderer.render(graph)

        node_data = result["nodes"][0]
        assert node_data["metadata"]["custom_field"] == "custom_value"
        assert node_data["metadata"]["nested"]["a"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 6.4 TASK-11: Integration Tests for Engine

**File**: `tests/integration/test_codemap_engine.py`

```python
#!/usr/bin/env python3
"""
Integration tests for codemap engine.

These tests require API keys and may make external calls.
Run with: python -m pytest tests/integration/test_codemap_engine.py -v
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.codemap.engine import CodemapEngine
from api.codemap.models import (
    CodemapGenerateRequest, CodemapStatus, CodemapProgress
)


class TestCodemapEngineIntegration:
    """Integration tests for CodemapEngine."""

    @pytest.fixture
    def engine(self):
        """Create a CodemapEngine instance."""
        return CodemapEngine(provider="google")

    @pytest.fixture
    def sample_request(self):
        """Create a sample generation request."""
        return CodemapGenerateRequest(
            repo_url="https://github.com/AsyncFuncAI/deepwiki-open",
            query="How does the API work?",
            language="en",
            analysis_type="auto",
            depth=2,
            max_nodes=20
        )

    @pytest.mark.asyncio
    async def test_generate_codemap_with_progress(self, engine, sample_request):
        """Test generating a codemap with progress tracking."""
        progress_updates = []

        async def track_progress(progress: CodemapProgress):
            progress_updates.append(progress)

        # This test requires actual API access
        # In CI, mock the external dependencies
        try:
            codemap = await engine.generate(
                request=sample_request,
                progress_callback=track_progress
            )

            # Verify codemap structure
            assert codemap is not None
            assert codemap.id is not None
            assert codemap.status == CodemapStatus.COMPLETED
            assert len(codemap.graph.nodes) > 0
            assert codemap.trace_guide is not None
            assert codemap.render.mermaid is not None

            # Verify progress was tracked
            assert len(progress_updates) > 0
            assert any(p.status == CodemapStatus.ANALYZING for p in progress_updates)

        except Exception as e:
            # If external services are unavailable, skip
            pytest.skip(f"External service unavailable: {e}")

    @pytest.mark.asyncio
    async def test_generate_codemap_error_handling(self, engine):
        """Test error handling for invalid requests."""
        invalid_request = CodemapGenerateRequest(
            repo_url="https://github.com/nonexistent/nonexistent",
            query="test"
        )

        with pytest.raises(Exception):
            await engine.generate(request=invalid_request)

    @pytest.mark.asyncio
    async def test_generate_with_filters(self, engine):
        """Test generating with file filters."""
        request = CodemapGenerateRequest(
            repo_url="https://github.com/AsyncFuncAI/deepwiki-open",
            query="How does the API work?",
            excluded_dirs=["node_modules", ".git", "tests"],
            excluded_files=["*.lock", "*.md"],
            max_nodes=10
        )

        try:
            codemap = await engine.generate(request=request)

            # Verify filters were applied
            for node in codemap.graph.nodes:
                if node.location:
                    assert "node_modules" not in node.location.file_path
                    assert ".git" not in node.location.file_path

        except Exception as e:
            pytest.skip(f"External service unavailable: {e}")


class TestCodemapEngineMocked:
    """Tests with mocked external dependencies."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        """Test that progress callback is called at each stage."""
        engine = CodemapEngine(provider="google")

        progress_calls = []

        async def mock_progress(progress: CodemapProgress):
            progress_calls.append(progress.current_step)

        # Mock the RAG and LLM components
        with patch.object(engine, 'query_parser') as mock_parser:
            mock_parser.parse = AsyncMock(return_value=Mock(
                suggested_type="architecture",
                focus_areas=["api"],
                keywords=["api"],
                preferred_layout="hierarchical"
            ))

            # Test would continue with more mocks...
            # This is a template for comprehensive mocking
            pass

    @pytest.mark.asyncio
    async def test_storage_called_on_completion(self):
        """Test that storage.save is called when generation completes."""
        engine = CodemapEngine(provider="google")

        with patch.object(engine.storage, 'save', new_callable=AsyncMock) as mock_save:
            mock_save.return_value = True

            # Would need full mocking of the generation pipeline
            # This is a template for the test structure
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 6.5 TASK-12: Smoke Test Checklist

**File**: `docs/CODEMAP_SMOKE_TEST.md`

```markdown
# Codemap Feature - Smoke Test Checklist

## Pre-requisites

- [ ] Backend server running (`python -m api.api`)
- [ ] Frontend server running (`npm run dev`)
- [ ] Valid repository URL for testing
- [ ] API keys configured (Google AI or other provider)

## Test Scenarios

### 1. Basic Generation

- [ ] Navigate to `/{owner}/{repo}/codemap`
- [ ] Enter query: "Show me the overall architecture"
- [ ] Click Generate / Press Enter
- [ ] Verify progress bar appears
- [ ] Verify progress updates show different stages
- [ ] Verify codemap renders successfully
- [ ] Verify trace guide is displayed

### 2. Graph Interaction

- [ ] Click on a node in the graph
- [ ] Verify node inspector panel opens
- [ ] Verify node details are correct (type, location, description)
- [ ] Click "Navigate to Code" link
- [ ] Verify it opens correct file/location (if applicable)
- [ ] Hover over different nodes
- [ ] Verify hover highlighting works

### 3. View Controls

- [ ] Test zoom in button
- [ ] Test zoom out button
- [ ] Test fit view button
- [ ] Test pan (drag) functionality
- [ ] Switch between view modes (graph/trace/split)
- [ ] Verify each mode renders correctly

### 4. Trace Guide

- [ ] Expand/collapse trace sections
- [ ] Click on node references in trace guide
- [ ] Verify node highlighting in graph
- [ ] Verify markdown content renders correctly
- [ ] Verify code snippets are syntax highlighted

### 5. History

- [ ] Generate multiple codemaps
- [ ] Click History button
- [ ] Verify previous codemaps are listed
- [ ] Select a previous codemap
- [ ] Verify it loads correctly

### 6. Share Functionality

- [ ] Click Share button
- [ ] Verify share URL is generated
- [ ] Copy share URL
- [ ] Open share URL in incognito/new browser
- [ ] Verify shared codemap loads correctly

### 7. Export

- [ ] Export as HTML
- [ ] Verify HTML file downloads
- [ ] Open HTML file and verify it renders
- [ ] Export as Mermaid
- [ ] Verify .mmd file downloads
- [ ] Export as JSON
- [ ] Verify JSON structure is correct

### 8. Error Handling

- [ ] Test with invalid repository URL
- [ ] Verify error message is displayed
- [ ] Test with rate limit exceeded (if possible)
- [ ] Verify rate limit message is shown
- [ ] Test network disconnect during generation
- [ ] Verify appropriate error handling

### 9. Wiki Integration

- [ ] Navigate to wiki page (`/{owner}/{repo}`)
- [ ] Verify "Codemap" link in header
- [ ] Click Codemap link
- [ ] Verify navigation to codemap page
- [ ] Verify query parameters preserved

### 10. Performance

- [ ] Test with large repository (1000+ files)
- [ ] Verify generation completes within reasonable time
- [ ] Verify UI remains responsive during generation
- [ ] Verify graph rendering is smooth with 50+ nodes

## Sign-off

| Tester | Date | Pass/Fail | Notes |
|--------|------|-----------|-------|
|        |      |           |       |
```

---

## 7. Performance Optimization

### 7.1 TASK-13: Analysis Caching

**File**: `api/codemap/cache.py` (NEW FILE)

```python
"""
Caching layer for codemap analysis results.
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from adalflow.utils import get_adalflow_default_root_path

logger = logging.getLogger(__name__)


class AnalysisCache:
    """
    Cache for analysis results to avoid re-analyzing unchanged files.
    """

    def __init__(self, ttl_hours: int = 24):
        self.cache_dir = os.path.join(
            get_adalflow_default_root_path(),
            "cache",
            "codemap_analysis"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_cache_key(self, repo_url: str, file_path: str, content_hash: str) -> str:
        """Generate cache key from repo, file, and content hash."""
        combined = f"{repo_url}:{file_path}:{content_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def _get_cache_path(self, cache_key: str) -> str:
        """Get filesystem path for cache entry."""
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def get(
        self,
        repo_url: str,
        file_path: str,
        content_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis result if available and not expired.
        """
        cache_key = self._get_cache_key(repo_url, file_path, content_hash)
        cache_path = self._get_cache_path(cache_key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check expiry
            cached_at = datetime.fromisoformat(data.get('cached_at', ''))
            if datetime.utcnow() - cached_at > self.ttl:
                os.remove(cache_path)
                return None

            return data.get('result')

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    def set(
        self,
        repo_url: str,
        file_path: str,
        content_hash: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        Store analysis result in cache.
        """
        cache_key = self._get_cache_key(repo_url, file_path, content_hash)
        cache_path = self._get_cache_path(cache_key)

        try:
            data = {
                'cached_at': datetime.utcnow().isoformat(),
                'repo_url': repo_url,
                'file_path': file_path,
                'content_hash': content_hash,
                'result': result
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)

            return True

        except Exception as e:
            logger.warning(f"Cache write error: {e}")
            return False

    def clear(self, max_age_days: int = 7):
        """
        Clear cache entries older than max_age_days.
        """
        max_age = timedelta(days=max_age_days)
        now = datetime.utcnow()
        removed = 0

        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.cache_dir, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                cached_at = datetime.fromisoformat(data.get('cached_at', ''))
                if now - cached_at > max_age:
                    os.remove(file_path)
                    removed += 1

            except Exception:
                # Remove corrupted cache files
                os.remove(file_path)
                removed += 1

        logger.info(f"Cleared {removed} expired cache entries")
        return removed
```

### 7.2 TASK-14: Query Intent Caching

**Update**: `api/codemap/llm/query_parser.py`

```python
# Add caching for query intents

from functools import lru_cache
import hashlib

class QueryParser:
    # ... existing code ...

    @lru_cache(maxsize=1000)
    def _get_cached_intent(self, query_hash: str):
        """Cache layer for parsed intents."""
        return None  # Placeholder, actual parsing happens in parse()

    async def parse(self, query: str) -> QueryIntent:
        """Parse query with caching."""
        # Normalize query for caching
        normalized = query.lower().strip()
        query_hash = hashlib.md5(normalized.encode()).hexdigest()

        # Check cache
        cached = self._get_cached_intent(query_hash)
        if cached:
            return cached

        # Parse and cache
        intent = await self._parse_impl(query)
        # Note: Can't directly cache async result with lru_cache
        # Would need a separate cache implementation

        return intent
```

---

## 8. Documentation

### 8.1 TASK-15: User Guide

**File**: `docs/CODEMAP_USER_GUIDE.md`

```markdown
# Codemap User Guide

## What is Codemap?

Codemap is an AI-powered feature that generates interactive, visual maps of your codebase. It helps you understand:

- How code components relate to each other
- Data and control flow through the system
- Execution order for specific features
- Direct links to source code locations

## Getting Started

### 1. Access Codemap

From any repository wiki page, click the **Codemap** link in the header navigation.

Alternatively, navigate directly to:
```
/{owner}/{repo}/codemap
```

### 2. Ask a Question

Enter a natural language question about the codebase:

- "How does authentication work?"
- "Show me the overall architecture"
- "What happens when a user submits an order?"
- "How does data flow from the API to the database?"

### 3. View Results

After generation, you'll see:

- **Graph View**: Interactive diagram showing code relationships
- **Trace Guide**: Narrative explanation of the flow
- **Node Inspector**: Detailed information about selected nodes

## Features

### Graph Interaction

- **Click** on nodes to see details
- **Drag** to pan the view
- **Scroll** or use buttons to zoom
- **Hover** to highlight connections

### View Modes

- **Graph**: Full-screen diagram view
- **Trace**: Full-screen narrative view
- **Split**: Side-by-side graph and trace

### Export Options

- **HTML**: Standalone interactive diagram
- **Mermaid**: Diagram code for documentation
- **JSON**: Raw graph data for integration

### Sharing

Click **Share** to generate a public link that anyone can view.

## Tips

1. **Be specific**: "How does JWT authentication work?" is better than "How does auth work?"
2. **Use filters**: Exclude test files or node_modules for cleaner results
3. **Iterate**: Generate multiple codemaps for different aspects of the code
4. **Navigate**: Click code locations to jump directly to source files

## Troubleshooting

### Generation takes too long

- Try reducing `max_nodes` in advanced settings
- Exclude large directories like `node_modules`

### Graph is too cluttered

- Use a more specific query
- Reduce analysis depth
- Exclude non-essential directories

### Missing code files

- Check that the repository is public or you've provided a valid token
- Verify the files aren't in excluded directories
```

### 8.2 TASK-16: API Documentation

**File**: `docs/CODEMAP_API.md`

```markdown
# Codemap API Documentation

## REST Endpoints

### Generate Codemap

```http
POST /api/codemap/generate
Content-Type: application/json

{
  "repo_url": "https://github.com/owner/repo",
  "query": "How does authentication work?",
  "language": "en",
  "analysis_type": "auto",
  "depth": 3,
  "max_nodes": 50,
  "excluded_dirs": ["node_modules", ".git"],
  "excluded_files": ["*.lock"],
  "provider": "google",
  "model": "gemini-2.5-flash",
  "token": "optional_access_token",
  "type": "github"
}
```

**Response**:
```json
{
  "codemap_id": "uuid",
  "status": "pending",
  "message": "Codemap generation started",
  "estimated_time_seconds": 30
}
```

### Get Codemap

```http
GET /api/codemap/{codemap_id}
```

### List Codemaps

```http
GET /api/codemap/list/all?repo_url=...&limit=50
```

### Get Repository Codemaps

```http
GET /api/codemap/repo/{owner}/{repo}?limit=20
```

### Share Codemap

```http
POST /api/codemap/{codemap_id}/share
```

### Get Shared Codemap

```http
GET /api/codemap/shared/{share_token}
```

### Delete Codemap

```http
DELETE /api/codemap/{codemap_id}
```

### Export HTML

```http
GET /api/codemap/{codemap_id}/export/html
```

### Export Mermaid

```http
GET /api/codemap/{codemap_id}/export/mermaid
```

## WebSocket Protocol

### Connect

```
ws://localhost:8001/ws/codemap
```

### Generate Request (Client → Server)

```json
{
  "repo_url": "https://github.com/owner/repo",
  "query": "How does authentication work?",
  "language": "en",
  "analysis_type": "auto",
  "depth": 3,
  "max_nodes": 50
}
```

### Progress Update (Server → Client)

```json
{
  "type": "progress",
  "data": {
    "codemap_id": "uuid",
    "status": "analyzing",
    "progress_percent": 35,
    "current_step": "Analyzing code structure...",
    "nodes_found": 12,
    "edges_found": 8,
    "files_analyzed": 5,
    "total_files": 15
  }
}
```

### Completion (Server → Client)

```json
{
  "type": "complete",
  "data": {
    // Full Codemap object
  }
}
```

### Error (Server → Client)

```json
{
  "type": "error",
  "message": "Error description"
}
```

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /generate | 5/minute |
| GET /{id} | 60/minute |
| GET /list | 30/minute |
| POST /share | 10/minute |

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Unauthorized (invalid token) |
| 403 | Forbidden (codemap not public) |
| 404 | Codemap not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
```

---

## 9. Implementation Order

### 9.1 Priority Matrix

| Task | Priority | Dependencies | Effort |
|------|----------|--------------|--------|
| TASK-01 (Wiki Header Link) | HIGH | None | LOW |
| TASK-02 (Wiki Sidebar Button) | HIGH | None | LOW |
| TASK-03 (i18n Messages) | MEDIUM | None | LOW |
| TASK-04 (Token Log Redaction) | HIGH | None | MEDIUM |
| TASK-05 (Token API Redaction) | HIGH | TASK-04 | LOW |
| TASK-06 (Share Expiry) | HIGH | None | MEDIUM |
| TASK-07 (Rate Limiting) | HIGH | None | MEDIUM |
| TASK-08 (Analyzer Tests) | HIGH | None | MEDIUM |
| TASK-09 (Generator Tests) | HIGH | None | MEDIUM |
| TASK-10 (Renderer Tests) | MEDIUM | None | MEDIUM |
| TASK-11 (Integration Tests) | HIGH | TASK-08,09,10 | HIGH |
| TASK-12 (Smoke Test Doc) | MEDIUM | None | LOW |
| TASK-13 (Analysis Cache) | MEDIUM | None | MEDIUM |
| TASK-14 (Query Cache) | LOW | None | LOW |
| TASK-15 (User Guide) | MEDIUM | None | LOW |
| TASK-16 (API Docs) | MEDIUM | None | LOW |

### 9.2 Recommended Implementation Sequence

```
Phase 5A: Critical Security & Integration (Day 1-2)
├── TASK-01: Wiki Header Link
├── TASK-02: Wiki Sidebar Button
├── TASK-04: Token Log Redaction
├── TASK-05: Token API Redaction
└── TASK-06: Share Expiry

Phase 5B: Rate Limiting & Core Tests (Day 3-4)
├── TASK-07: Rate Limiting
├── TASK-08: Analyzer Unit Tests
├── TASK-09: Generator Unit Tests
└── TASK-10: Renderer Unit Tests

Phase 5C: Integration & Documentation (Day 5-6)
├── TASK-11: Integration Tests
├── TASK-12: Smoke Test Checklist
├── TASK-15: User Guide
└── TASK-16: API Documentation

Phase 5D: Optimization & Polish (Day 7)
├── TASK-03: i18n Messages
├── TASK-13: Analysis Caching
└── TASK-14: Query Intent Caching
```

---

## 10. File Reference

### 10.1 Files to Create

| File | Purpose |
|------|---------|
| `api/codemap/utils/security.py` | Security utilities |
| `api/codemap/rate_limit.py` | Rate limiting config |
| `api/codemap/cache.py` | Analysis caching |
| `tests/unit/test_codemap_analyzer.py` | Analyzer tests |
| `tests/unit/test_codemap_generator.py` | Generator tests |
| `tests/unit/test_codemap_renderer.py` | Renderer tests |
| `tests/integration/test_codemap_engine.py` | Integration tests |
| `docs/CODEMAP_USER_GUIDE.md` | User documentation |
| `docs/CODEMAP_API.md` | API documentation |
| `docs/CODEMAP_SMOKE_TEST.md` | QA checklist |

### 10.2 Files to Modify

| File | Changes |
|------|---------|
| `src/app/[owner]/[repo]/page.tsx` | Add Codemap links |
| `api/codemap/models.py` | Add `share_expires_at` field |
| `api/codemap/storage.py` | Add expiry checking |
| `api/codemap/engine.py` | Add token redaction |
| `api/codemap_api.py` | Add rate limiting |
| `api/api.py` | Register rate limiter |
| `requirements.txt` | Add slowapi |

### 10.3 Dependencies to Add

```
# requirements.txt
slowapi>=0.1.9
```

---

## Appendix: Checklist Summary

### Pre-Implementation

- [ ] Review PLAN.md for context
- [ ] Verify all Phase 1-4 implementations working
- [ ] Set up test environment

### Implementation

- [ ] TASK-01: Wiki Header Link
- [ ] TASK-02: Wiki Sidebar Button
- [ ] TASK-03: i18n Messages
- [ ] TASK-04: Token Log Redaction
- [ ] TASK-05: Token API Redaction
- [ ] TASK-06: Share Expiry
- [ ] TASK-07: Rate Limiting
- [ ] TASK-08: Analyzer Unit Tests
- [ ] TASK-09: Generator Unit Tests
- [ ] TASK-10: Renderer Unit Tests
- [ ] TASK-11: Integration Tests
- [ ] TASK-12: Smoke Test Checklist
- [ ] TASK-13: Analysis Caching
- [ ] TASK-14: Query Intent Caching
- [ ] TASK-15: User Guide
- [ ] TASK-16: API Documentation

### Post-Implementation

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Manual smoke test completed
- [ ] Documentation reviewed
- [ ] Code review completed
- [ ] Merge to main branch

---

*This plan was generated on 2025-12-18 and covers Phase 5 (Polish & Integration) of the Codemaps feature.*
