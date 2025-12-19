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
from api.codemap.generator.edge_builder import EdgeBuilder, LLMRelationship
from api.codemap.analyzer.base import SymbolInfo, ImportInfo, CallInfo, AnalysisResult
from api.codemap.models import NodeType, SourceLocation, CodemapNode, CodemapEdge, EdgeType, Importance, QueryIntent


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

        nodes = self.builder.build(analysis_results)

        # Should have file node + 2 symbol nodes
        assert len(nodes) >= 3

        # Check file node
        file_node = next((n for n in nodes if n.type == NodeType.FILE), None)
        assert file_node is not None
        assert file_node.label == "test.py"

        # Check class node
        class_node = next((n for n in nodes if n.label == "MyClass"), None)
        assert class_node is not None
        assert class_node.type == NodeType.CLASS

        # Check function node
        func_node = next((n for n in nodes if n.label == "my_function"), None)
        assert func_node is not None
        assert func_node.type == NodeType.FUNCTION

    def test_node_importance_calculation(self):
        """Test that node importance is calculated correctly based on type and attributes."""
        analysis_results = {
            "test.py": AnalysisResult(
                file_path="test.py",
                language="python",
                symbols=[
                    SymbolInfo(
                        name="ImportantClass",
                        type=NodeType.CLASS,
                        location=SourceLocation(file_path="test.py", line_start=1, line_end=10),
                        docstring="Important class with docs",
                        is_exported=True,
                        bases=["BaseClass"]
                    ),
                    SymbolInfo(
                        name="helper",
                        type=NodeType.FUNCTION,
                        location=SourceLocation(file_path="test.py", line_start=15, line_end=18)
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        nodes = self.builder.build(analysis_results)

        important_node = next(n for n in nodes if n.label == "ImportantClass")
        helper_node = next(n for n in nodes if n.label == "helper")

        # ImportantClass should have higher importance due to class type, docstring, export, and inheritance
        assert important_node.importance.value in ["critical", "high"]
        # helper should have lower importance
        assert helper_node.importance.value in ["medium", "low"]

    def test_query_relevance_scoring(self):
        """Test that query keywords boost node importance."""
        analysis_results = {
            "auth.py": AnalysisResult(
                file_path="auth.py",
                language="python",
                symbols=[
                    SymbolInfo(
                        name="AuthenticationService",
                        type=NodeType.CLASS,
                        location=SourceLocation(file_path="auth.py", line_start=1, line_end=50)
                    ),
                    SymbolInfo(
                        name="validate_data",
                        type=NodeType.FUNCTION,
                        location=SourceLocation(file_path="auth.py", line_start=52, line_end=60)
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        query_intent = QueryIntent(
            intent="understand authentication",
            keywords=["auth", "authentication"],
            focus_areas=["auth"],
            analysis_type="architecture"
        )

        nodes = self.builder.build(analysis_results, query_intent)

        auth_node = next(n for n in nodes if n.label == "AuthenticationService")
        validate_node = next(n for n in nodes if n.label == "validate_data")

        # AuthenticationService should be boosted by query relevance
        assert auth_node.importance.value in ["critical", "high"]

    def test_group_extraction(self):
        """Test that nodes are grouped by directory."""
        analysis_results = {
            "api/handlers/user.py": AnalysisResult(
                file_path="api/handlers/user.py",
                language="python",
                symbols=[
                    SymbolInfo(
                        name="UserHandler",
                        type=NodeType.CLASS,
                        location=SourceLocation(file_path="api/handlers/user.py", line_start=1, line_end=20)
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        nodes = self.builder.build(analysis_results)

        user_node = next(n for n in nodes if n.label == "UserHandler")
        assert user_node.group is not None
        assert user_node.group in ["api", "handlers"]

    def test_metadata_preservation(self):
        """Test that symbol metadata is preserved in nodes."""
        analysis_results = {
            "test.py": AnalysisResult(
                file_path="test.py",
                language="python",
                symbols=[
                    SymbolInfo(
                        name="async_handler",
                        type=NodeType.FUNCTION,
                        location=SourceLocation(file_path="test.py", line_start=1, line_end=10),
                        parameters=["request", "response"],
                        return_type="dict",
                        is_async=True,
                        decorators=["route"]
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        nodes = self.builder.build(analysis_results)

        func_node = next(n for n in nodes if n.label == "async_handler")
        assert func_node.metadata["is_async"] is True
        assert func_node.metadata["parameters"] == ["request", "response"]
        assert func_node.metadata["return_type"] == "dict"
        assert "route" in func_node.metadata["decorators"]


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
                        location=SourceLocation(file_path="main.py", line_start=1, line_end=1),
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
                        location=SourceLocation(file_path="utils.py", line_start=1, line_end=5)
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        edges = self.builder.build(analysis_results)

        # Should have import edge from main.py to utils.py
        import_edges = [e for e in edges if e.type == EdgeType.IMPORTS]
        assert len(import_edges) >= 1

        # Check the import edge
        import_edge = import_edges[0]
        assert import_edge.source == "file:main.py"
        assert import_edge.target == "file:utils.py"

    def test_build_external_import_edges(self):
        """Test that external imports create external node references."""
        analysis_results = {
            "main.py": AnalysisResult(
                file_path="main.py",
                language="python",
                symbols=[],
                imports=[
                    ImportInfo(
                        module="requests",
                        names=["get", "post"],
                        location=SourceLocation(file_path="main.py", line_start=1, line_end=1)
                    )
                ],
                calls=[]
            )
        }

        edges = self.builder.build(analysis_results)

        import_edges = [e for e in edges if e.type == EdgeType.IMPORTS]
        assert len(import_edges) >= 1

        import_edge = import_edges[0]
        assert import_edge.target.startswith("external:")

    def test_build_containment_edges(self):
        """Test building edges showing file contains symbols."""
        analysis_results = {
            "module.py": AnalysisResult(
                file_path="module.py",
                language="python",
                symbols=[
                    SymbolInfo(
                        name="MyClass",
                        type=NodeType.CLASS,
                        location=SourceLocation(file_path="module.py", line_start=1, line_end=10)
                    ),
                    SymbolInfo(
                        name="my_func",
                        type=NodeType.FUNCTION,
                        location=SourceLocation(file_path="module.py", line_start=12, line_end=15)
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        edges = self.builder.build(analysis_results)

        containment_edges = [e for e in edges if e.type == EdgeType.CONTAINS]
        assert len(containment_edges) >= 2

        for edge in containment_edges:
            assert edge.source == "file:module.py"

    def test_build_inheritance_edges(self):
        """Test building edges from class inheritance."""
        analysis_results = {
            "models.py": AnalysisResult(
                file_path="models.py",
                language="python",
                symbols=[
                    SymbolInfo(
                        name="BaseModel",
                        type=NodeType.CLASS,
                        location=SourceLocation(file_path="models.py", line_start=1, line_end=10)
                    ),
                    SymbolInfo(
                        name="UserModel",
                        type=NodeType.CLASS,
                        location=SourceLocation(file_path="models.py", line_start=12, line_end=25),
                        bases=["BaseModel"]
                    )
                ],
                imports=[],
                calls=[]
            )
        }

        edges = self.builder.build(analysis_results)

        inheritance_edges = [e for e in edges if e.type == EdgeType.EXTENDS]
        assert len(inheritance_edges) >= 1

        ext_edge = inheritance_edges[0]
        assert ext_edge.type == EdgeType.EXTENDS

    def test_build_llm_edges(self):
        """Test building edges from LLM-inferred relationships."""
        analysis_results = {
            "api.py": AnalysisResult(
                file_path="api.py",
                language="python",
                symbols=[],
                imports=[],
                calls=[]
            )
        }

        llm_relationships = [
            LLMRelationship(
                source="file:api.py",
                target="file:db.py",
                type=EdgeType.DATA_FLOW,
                description="API reads data from database",
                importance="high"
            )
        ]

        edges = self.builder.build(analysis_results, llm_relationships)

        data_flow_edges = [e for e in edges if e.type == EdgeType.DATA_FLOW]
        assert len(data_flow_edges) >= 1

        df_edge = data_flow_edges[0]
        assert df_edge.source == "file:api.py"
        assert df_edge.target == "file:db.py"
        assert df_edge.metadata.get("source") == "llm"

    def test_edge_deduplication(self):
        """Test that duplicate edges are not created."""
        analysis_results = {
            "main.py": AnalysisResult(
                file_path="main.py",
                language="python",
                symbols=[],
                imports=[
                    ImportInfo(
                        module="utils",
                        names=["a"],
                        location=SourceLocation(file_path="main.py", line_start=1, line_end=1),
                        resolved_path="utils.py"
                    ),
                    ImportInfo(
                        module="utils",
                        names=["b"],
                        location=SourceLocation(file_path="main.py", line_start=2, line_end=2),
                        resolved_path="utils.py"
                    )
                ],
                calls=[]
            )
        }

        edges = self.builder.build(analysis_results)

        import_edges = [e for e in edges if e.type == EdgeType.IMPORTS and "utils" in e.target]
        # Should only have one import edge despite two imports
        assert len(import_edges) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
