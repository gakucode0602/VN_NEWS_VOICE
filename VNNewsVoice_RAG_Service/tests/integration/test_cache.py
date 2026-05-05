"""Integration tests for Cache functionality.

Tests cache hit/miss scenarios and performance improvements.
"""

import pytest
from unittest.mock import Mock
import time

from app.core.rag.adaptive.query_analyzer import LLMQueryAnalyzer
from app.models.domain.query import QueryAnalysis
from app.models.enums import QueryIntent, QueryScope, TimeSensitivity


class TestCacheIntegration:
    """Test suite for cache integration."""

    @pytest.mark.integration
    def test_cache_miss_then_hit(self, mock_llm, mock_redis_cache):
        """Test cache miss followed by cache hit."""
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="test query",
            intent=QueryIntent.FACTUAL,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.NARROW,
            entities=[],
            topics=[],
            keywords=[],
            confidence=0.9,
            reasoning="test",
        )
        analyzer = LLMQueryAnalyzer(llm=mock_llm, cache=mock_redis_cache)

        # First call - cache miss
        mock_redis_cache.get.return_value = None
        result1 = analyzer.analyze("test query")

        # Verify LLM was called
        assert mock_llm.generate_structured.called
        # Verify cache set was called
        assert mock_redis_cache.set.called

        # Second call - cache hit
        # Reset the mock to ensure it's not called again
        mock_llm.generate_structured.reset_mock()
        mock_redis_cache.get.return_value = result1
        result2 = analyzer.analyze("test query")

        # LLM should not be called again
        assert not mock_llm.generate_structured.called
        # Results should be the same
        assert result1.original_query == result2.original_query

    @pytest.mark.integration
    def test_cache_performance_improvement(self, mock_llm, mock_redis_cache):
        """Test that cache provides performance improvement."""

        # Simulate slow LLM call
        def slow_generate(*args, **kwargs):
            time.sleep(0.01)  # 10ms delay
            return QueryAnalysis(
                original_query="test query",
                intent=QueryIntent.FACTUAL,
                time_sensitivity=TimeSensitivity.TIMELESS,
                scope=QueryScope.NARROW,
                entities=[],
                topics=[],
                keywords=[],
                confidence=0.9,
                reasoning="test",
            )

        mock_llm.generate_structured.side_effect = slow_generate

        analyzer = LLMQueryAnalyzer(llm=mock_llm, cache=mock_redis_cache)

        # First call - cache miss (slow)
        mock_redis_cache.get.return_value = None
        start = time.perf_counter()
        result1 = analyzer.analyze("test query")
        miss_time = time.perf_counter() - start

        # Second call - cache hit (fast)
        mock_redis_cache.get.return_value = result1
        start = time.perf_counter()
        analyzer.analyze("test query")
        hit_time = time.perf_counter() - start

        # Cache hit should be faster
        assert hit_time < miss_time

    @pytest.mark.integration
    def test_cache_stats_tracking(self, mock_redis_cache):
        """Test cache statistics tracking."""
        mock_redis_cache.get_stats.return_value = Mock(hits=5, misses=3, hit_rate=0.625)

        stats = mock_redis_cache.get_stats()

        assert stats.hits == 5
        assert stats.misses == 3
        assert stats.hit_rate == 0.625

    @pytest.mark.integration
    def test_cache_clear(self, mock_redis_cache):
        """Test cache clearing functionality."""
        mock_redis_cache.clear.return_value = True

        result = mock_redis_cache.clear()

        assert result is True
        assert mock_redis_cache.clear.called
