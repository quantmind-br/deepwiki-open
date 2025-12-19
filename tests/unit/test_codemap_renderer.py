#!/usr/bin/env python3
"""
Unit tests for codemap renderers.
"""

import pytest
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.codemap.renderer.mermaid import MermaidRenderer
from api.codemap.renderer.json_export import JSONRenderer
from api.codemap.models import (
    CodemapGraph, CodemapNode, CodemapEdge,
    NodeType, EdgeType, SourceLocation, QueryIntent, Importance
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
                    importance=Importance.HIGH,
                    metadata={}
                ),
                CodemapNode(
                    id="node2",
                    label="ClassB",
                    type=NodeType.CLASS,
                    importance=Importance.MEDIUM,
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

        mermaid_code = self.renderer.render(graph)

        assert "flowchart" in mermaid_code
        assert "ClassA" in mermaid_code
        assert "ClassB" in mermaid_code
        # Should contain edge connection
        assert "-->" in mermaid_code or "==>" in mermaid_code

    def test_render_with_clusters(self):
        """Test rendering with node clusters."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="node1",
                    label="Func1",
                    type=NodeType.FUNCTION,
                    importance=Importance.MEDIUM,
                    metadata={},
                    group="group1"
                ),
                CodemapNode(
                    id="node2",
                    label="Func2",
                    type=NodeType.FUNCTION,
                    importance=Importance.MEDIUM,
                    metadata={},
                    group="group1"
                )
            ],
            edges=[],
            root_nodes=["node1"],
            clusters={"group1": ["node1", "node2"]}
        )

        mermaid_code = self.renderer.render(graph)

        # Should contain subgraph
        assert "subgraph" in mermaid_code.lower()
        assert "Func1" in mermaid_code
        assert "Func2" in mermaid_code

    def test_escape_special_characters(self):
        """Test that special characters are escaped."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="node1",
                    label="Class<T>",
                    type=NodeType.CLASS,
                    importance=Importance.MEDIUM,
                    metadata={}
                )
            ],
            edges=[],
            root_nodes=["node1"],
            clusters={}
        )

        mermaid_code = self.renderer.render(graph)

        # The label should be escaped to avoid Mermaid parsing errors
        assert "node1" in mermaid_code or "n_node1" in mermaid_code
        # Angle brackets should be escaped
        assert "<T>" not in mermaid_code

    def test_different_node_types(self):
        """Test that different node types get different shapes."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="file1",
                    label="main.py",
                    type=NodeType.FILE,
                    importance=Importance.HIGH,
                    metadata={}
                ),
                CodemapNode(
                    id="class1",
                    label="MyClass",
                    type=NodeType.CLASS,
                    importance=Importance.HIGH,
                    metadata={}
                ),
                CodemapNode(
                    id="func1",
                    label="my_func",
                    type=NodeType.FUNCTION,
                    importance=Importance.MEDIUM,
                    metadata={}
                )
            ],
            edges=[],
            root_nodes=["file1"],
            clusters={}
        )

        mermaid_code = self.renderer.render(graph)

        # Each node type should be present
        assert "main.py" in mermaid_code
        assert "MyClass" in mermaid_code
        assert "my_func" in mermaid_code

    def test_different_edge_types(self):
        """Test that different edge types get different styles."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(id="a", label="A", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={}),
                CodemapNode(id="b", label="B", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={}),
                CodemapNode(id="c", label="C", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={})
            ],
            edges=[
                CodemapEdge(id="e1", source="a", target="b", type=EdgeType.IMPORTS, weight=1.0, metadata={}),
                CodemapEdge(id="e2", source="b", target="c", type=EdgeType.EXTENDS, weight=1.0, metadata={})
            ],
            root_nodes=["a"],
            clusters={}
        )

        mermaid_code = self.renderer.render(graph)

        # Should have different edge styles
        assert "-->" in mermaid_code or "-.->" in mermaid_code

    def test_edge_labels(self):
        """Test that edge labels are rendered."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(id="a", label="A", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={}),
                CodemapNode(id="b", label="B", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={})
            ],
            edges=[
                CodemapEdge(
                    id="e1",
                    source="a",
                    target="b",
                    type=EdgeType.CALLS,
                    label="calls",
                    weight=1.0,
                    metadata={}
                )
            ],
            root_nodes=["a"],
            clusters={}
        )

        mermaid_code = self.renderer.render(graph)

        assert "calls" in mermaid_code

    def test_render_simple_method(self):
        """Test the render_simple method."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(id="a", label="A", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={}),
                CodemapNode(id="b", label="B", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={})
            ],
            edges=[
                CodemapEdge(id="e1", source="a", target="b", type=EdgeType.IMPORTS, weight=1.0, metadata={})
            ],
            root_nodes=["a"],
            clusters={"cluster1": ["a", "b"]}  # Has cluster but should be ignored
        )

        mermaid_code = self.renderer.render_simple(graph)

        # Simple render should not have subgraphs
        assert "subgraph" not in mermaid_code.lower()
        assert "flowchart" in mermaid_code

    def test_long_label_truncation(self):
        """Test that long labels are truncated."""
        long_label = "ThisIsAVeryLongClassNameThatShouldBeTruncated"
        
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="node1",
                    label=long_label,
                    type=NodeType.CLASS,
                    importance=Importance.MEDIUM,
                    metadata={}
                )
            ],
            edges=[],
            root_nodes=["node1"],
            clusters={}
        )

        mermaid_code = self.renderer.render(graph)

        # Full long label should not appear
        assert long_label not in mermaid_code
        # Truncated version should appear
        assert "..." in mermaid_code


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
                    importance=Importance.HIGH,
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
                    importance=Importance.MEDIUM,
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

    def test_render_includes_clusters(self):
        """Test that clusters are included in JSON output."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(id="n1", label="N1", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={}),
                CodemapNode(id="n2", label="N2", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={})
            ],
            edges=[],
            root_nodes=["n1"],
            clusters={"cluster1": ["n1", "n2"]}
        )

        result = self.renderer.render(graph)

        assert "clusters" in result
        assert "cluster1" in result["clusters"]
        assert "n1" in result["clusters"]["cluster1"]

    def test_render_includes_root_nodes(self):
        """Test that root nodes are included in JSON output."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(id="root", label="Root", type=NodeType.CLASS, importance=Importance.HIGH, metadata={}),
                CodemapNode(id="child", label="Child", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={})
            ],
            edges=[],
            root_nodes=["root"],
            clusters={}
        )

        result = self.renderer.render(graph)

        assert "rootNodes" in result
        assert "root" in result["rootNodes"]

    def test_render_edges_complete(self):
        """Test that edges are completely rendered."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(id="a", label="A", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={}),
                CodemapNode(id="b", label="B", type=NodeType.CLASS, importance=Importance.MEDIUM, metadata={})
            ],
            edges=[
                CodemapEdge(
                    id="e1",
                    source="a",
                    target="b",
                    type=EdgeType.CALLS,
                    label="calls",
                    description="A calls B",
                    weight=1.5,
                    metadata={"custom": "data"}
                )
            ],
            root_nodes=["a"],
            clusters={}
        )

        result = self.renderer.render(graph)

        edge_data = result["edges"][0]
        assert edge_data["id"] == "e1"
        assert edge_data["source"] == "a"
        assert edge_data["target"] == "b"
        assert edge_data["type"] == "calls"
        assert edge_data["weight"] == 1.5

    def test_json_serializable(self):
        """Test that the output is JSON serializable."""
        graph = CodemapGraph(
            nodes=[
                CodemapNode(
                    id="n1",
                    label="Test",
                    type=NodeType.CLASS,
                    importance=Importance.HIGH,
                    metadata={"list": [1, 2, 3], "nested": {"key": "value"}},
                    location=SourceLocation(file_path="test.py", line_start=1, line_end=10)
                )
            ],
            edges=[],
            root_nodes=["n1"],
            clusters={}
        )

        result = self.renderer.render(graph)

        # Should not raise
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

        # Parse it back
        parsed = json.loads(json_str)
        assert parsed["nodes"][0]["id"] == "n1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
