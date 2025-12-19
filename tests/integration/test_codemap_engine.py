#!/usr/bin/env python3
"""
Integration tests for codemap engine.

These tests verify the end-to-end flow of codemap generation.
Some tests require API keys and may make external calls.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.codemap.models import (
    CodemapGenerateRequest, CodemapStatus, CodemapProgress,
    NodeType, EdgeType, Importance
)
from api.codemap.storage import CodemapStorage


class TestCodemapStorageIntegration:
    """Integration tests for CodemapStorage."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create a CodemapStorage with temporary directory."""
        with patch('api.codemap.storage.get_adalflow_default_root_path', return_value=str(tmp_path)):
            return CodemapStorage()

    @pytest.fixture
    def sample_codemap_data(self):
        """Create sample codemap data for testing."""
        from api.codemap.models import (
            Codemap, CodemapGraph, CodemapNode, CodemapEdge,
            TraceGuide, TraceSection, CodemapRenderOutput
        )
        from datetime import datetime

        return Codemap(
            id="test-codemap-123",
            repo_url="https://github.com/test/repo",
            repo_owner="test",
            repo_name="repo",
            query="How does authentication work?",
            title="Authentication Flow",
            description="Overview of authentication system",
            graph=CodemapGraph(
                nodes=[
                    CodemapNode(
                        id="node1",
                        label="AuthService",
                        type=NodeType.CLASS,
                        importance=Importance.HIGH,
                        metadata={}
                    )
                ],
                edges=[],
                root_nodes=["node1"],
                clusters={}
            ),
            trace_guide=TraceGuide(
                title="Authentication Guide",
                summary="How auth works",
                sections=[
                    TraceSection(
                        id="s1",
                        title="Overview",
                        content="Auth overview content",
                        node_ids=["node1"],
                        order=0
                    )
                ]
            ),
            render=CodemapRenderOutput(
                mermaid="flowchart TB\n  A-->B",
                json_graph={"nodes": [], "edges": []},
                html=None
            ),
            status=CodemapStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_save_and_load_codemap(self, storage, sample_codemap_data):
        """Test saving and loading a codemap."""
        # Save
        success = await storage.save(sample_codemap_data)
        assert success is True

        # Load
        loaded = await storage.load(sample_codemap_data.id)
        assert loaded is not None
        assert loaded.id == sample_codemap_data.id
        assert loaded.title == sample_codemap_data.title
        assert loaded.repo_url == sample_codemap_data.repo_url

    @pytest.mark.asyncio
    async def test_delete_codemap(self, storage, sample_codemap_data):
        """Test deleting a codemap."""
        # Save first
        await storage.save(sample_codemap_data)

        # Delete
        success = await storage.delete(sample_codemap_data.id)
        assert success is True

        # Verify deleted
        loaded = await storage.load(sample_codemap_data.id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_list_codemaps(self, storage, sample_codemap_data):
        """Test listing codemaps."""
        # Save
        await storage.save(sample_codemap_data)

        # List
        codemaps = await storage.list_codemaps()
        assert len(codemaps) >= 1
        assert any(cm['id'] == sample_codemap_data.id for cm in codemaps)

    @pytest.mark.asyncio
    async def test_share_token_with_expiry(self, storage, sample_codemap_data):
        """Test share token functionality with expiry."""
        # Save
        await storage.save(sample_codemap_data)

        # Update share token
        share_token = "test-share-token"
        success = await storage.update_share_token(
            sample_codemap_data.id,
            share_token,
            is_public=True,
            ttl_days=30
        )
        assert success is True

        # Get by share token
        loaded = await storage.get_by_share_token(share_token)
        assert loaded is not None
        assert loaded.share_token == share_token
        assert loaded.is_public is True
        assert loaded.share_expires_at is not None

    @pytest.mark.asyncio
    async def test_expired_share_token(self, storage, sample_codemap_data):
        """Test that expired share tokens return None."""
        from datetime import timedelta

        # Save
        await storage.save(sample_codemap_data)

        # Update with very short TTL (already expired)
        share_token = "expired-token"
        success = await storage.update_share_token(
            sample_codemap_data.id,
            share_token,
            is_public=True,
            ttl_days=-1  # Negative days = already expired
        )
        assert success is True

        # Get by share token should return None
        loaded = await storage.get_by_share_token(share_token)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_get_by_repo(self, storage, sample_codemap_data):
        """Test getting codemaps by repository."""
        # Save
        await storage.save(sample_codemap_data)

        # Get by repo
        codemaps = await storage.get_by_repo(
            sample_codemap_data.repo_owner,
            sample_codemap_data.repo_name
        )
        assert len(codemaps) >= 1
        assert any(cm['id'] == sample_codemap_data.id for cm in codemaps)


class TestCodemapGenerationFlow:
    """Integration tests for codemap generation flow."""

    @pytest.fixture
    def mock_rag_system(self):
        """Create a mock RAG system."""
        mock = MagicMock()
        mock.retrieve_documents = AsyncMock(return_value=[
            MagicMock(
                meta_data={"file_path": "test.py"},
                text="def test_function():\n    pass"
            )
        ])
        return mock

    def test_generate_request_validation(self):
        """Test that CodemapGenerateRequest validates correctly."""
        # Valid request
        request = CodemapGenerateRequest(
            repo_url="https://github.com/test/repo",
            query="How does it work?"
        )
        assert request.repo_url == "https://github.com/test/repo"
        assert request.depth == 3  # Default
        assert request.max_nodes == 50  # Default

        # Request with custom values
        request = CodemapGenerateRequest(
            repo_url="https://github.com/test/repo",
            query="Show architecture",
            depth=5,
            max_nodes=100,
            excluded_dirs=["node_modules", ".git"]
        )
        assert request.depth == 5
        assert request.max_nodes == 100
        assert "node_modules" in request.excluded_dirs

    def test_progress_model(self):
        """Test CodemapProgress model."""
        progress = CodemapProgress(
            codemap_id="test-123",
            status=CodemapStatus.ANALYZING,
            progress_percent=50,
            current_step="Analyzing Python files...",
            nodes_found=10,
            edges_found=5,
            files_analyzed=3,
            total_files=10
        )

        assert progress.progress_percent == 50
        assert progress.status == CodemapStatus.ANALYZING


class TestSecurityUtilsIntegration:
    """Integration tests for security utilities."""

    def test_redact_sensitive_data(self):
        """Test that sensitive data is properly redacted."""
        from api.codemap.utils.security import redact_sensitive_data

        data = {
            "repo_url": "https://github.com/test/repo",
            "token": "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            "query": "How does auth work?",
            "nested": {
                "api_key": "sk-1234567890abcdef",
                "normal_field": "value"
            }
        }

        redacted = redact_sensitive_data(data)

        assert redacted["repo_url"] == "https://github.com/test/repo"
        assert redacted["query"] == "How does auth work?"
        # Token should be partially redacted (shows first 4 and last 4 chars)
        assert "..." in redacted["token"]
        # Full token should not appear
        assert redacted["token"] != data["token"]
        # API key should be partially redacted
        assert "..." in redacted["nested"]["api_key"]
        assert redacted["nested"]["api_key"] != data["nested"]["api_key"]
        assert redacted["nested"]["normal_field"] == "value"

    def test_redact_token_from_url(self):
        """Test redacting tokens from URLs."""
        from api.codemap.utils.security import redact_token_from_url

        url = "https://example.com/api?token=secret123&other=value"
        redacted = redact_token_from_url(url)

        assert "secret123" not in redacted
        assert "other=value" in redacted


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limiter_allows_within_limit(self):
        """Test that requests within limit are allowed."""
        from api.codemap.rate_limit import RateLimiter

        limiter = RateLimiter()

        # Should allow first few requests
        for i in range(5):
            allowed, _ = limiter.is_allowed("test_key", max_requests=10, window_seconds=60)
            assert allowed is True

    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over limit are blocked."""
        from api.codemap.rate_limit import RateLimiter

        limiter = RateLimiter()

        # Make requests up to limit
        for i in range(5):
            limiter.is_allowed("test_key", max_requests=5, window_seconds=60)

        # Next request should be blocked
        allowed, retry_after = limiter.is_allowed("test_key", max_requests=5, window_seconds=60)
        assert allowed is False
        assert retry_after > 0

    def test_rate_limiter_independent_keys(self):
        """Test that different keys have independent limits."""
        from api.codemap.rate_limit import RateLimiter

        limiter = RateLimiter()

        # Exhaust limit for key1
        for i in range(5):
            limiter.is_allowed("key1", max_requests=5, window_seconds=60)

        # key2 should still work
        allowed, _ = limiter.is_allowed("key2", max_requests=5, window_seconds=60)
        assert allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
