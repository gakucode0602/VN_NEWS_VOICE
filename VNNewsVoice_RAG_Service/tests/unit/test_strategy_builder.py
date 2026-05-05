"""Unit tests for StrategyBuilder.

Migrated from scripts/test_strategy_builder.py
"""

import pytest

from app.core.rag.adaptive.strategy_builder import StrategyBuilder
from app.models.domain.query import QueryAnalysis
from app.models.enums import QueryIntent, QueryScope, TimeSensitivity


@pytest.fixture
def builder():
    """Create StrategyBuilder instance."""
    return StrategyBuilder()


class TestStrategyBuilder:
    """Test suite for StrategyBuilder."""

    @pytest.mark.unit
    def test_temporal_realtime_query(self, builder):
        """Test strategy for realtime temporal query."""
        analysis = QueryAnalysis(
            original_query="Tin Ukraine hôm nay",
            intent=QueryIntent.TEMPORAL,
            time_sensitivity=TimeSensitivity.REALTIME,
            scope=QueryScope.MEDIUM,
            entities=["Ukraine"],
            topics=["quốc tế", "chiến tranh"],
            confidence=0.9,
            reasoning="Temporal query with realtime requirement",
        )

        strategy = builder.build_strategy(analysis)

        assert strategy.top_k == 15, f"Expected top_k=15, got {strategy.top_k}"
        assert not strategy.rerank, "Should not rerank for medium scope with top_k=15"
        assert "published_at" in strategy.filters, (
            "Should have date filter for REALTIME"
        )
        assert "gte" in strategy.filters["published_at"], "Should have gte bound"
        assert "recent" in strategy.boosting_rules, "Should boost recent for REALTIME"

    @pytest.mark.unit
    def test_factual_narrow_query(self, builder):
        """Test strategy for factual narrow query."""
        analysis = QueryAnalysis(
            original_query="Ai là tổng thống Mỹ?",
            intent=QueryIntent.FACTUAL,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.NARROW,
            entities=["Mỹ"],
            topics=["chính trị"],
            confidence=0.95,
            reasoning="Factual query, no time constraint",
        )

        strategy = builder.build_strategy(analysis)

        assert strategy.top_k == 5, f"Expected top_k=5 for NARROW, got {strategy.top_k}"
        assert not strategy.rerank, "Should not rerank for small top_k"
        assert "published_at" not in strategy.filters, (
            "Should not filter date for TIMELESS"
        )
        assert "entity_match" in strategy.boosting_rules, (
            "Should boost entity match for FACTUAL"
        )

    @pytest.mark.unit
    def test_comparative_query(self, builder):
        """Test strategy for comparative query."""
        analysis = QueryAnalysis(
            original_query="So sánh GDP 2024 và 2025",
            intent=QueryIntent.COMPARATIVE,
            time_sensitivity=TimeSensitivity.RECENT,
            scope=QueryScope.NARROW,
            entities=["GDP"],
            topics=["kinh tế"],
            confidence=0.9,
            reasoning="Comparative query with recent timeframe",
        )

        strategy = builder.build_strategy(analysis)

        assert strategy.top_k == 10, (
            f"Expected top_k=10 (5+5 for COMPARATIVE), got {strategy.top_k}"
        )
        assert strategy.rerank, "Should rerank for COMPARATIVE intent"
        assert "published_at" in strategy.filters, "Should filter date for RECENT"
        assert "gte" in strategy.filters["published_at"], "Should have gte bound"
        assert "entity_match" in strategy.boosting_rules, (
            "Should boost entity for COMPARATIVE"
        )

    @pytest.mark.unit
    def test_exploratory_broad_query(self, builder):
        """Test strategy for exploratory broad query."""
        analysis = QueryAnalysis(
            original_query="Tin thể thao",
            intent=QueryIntent.EXPLORATORY,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.BROAD,
            entities=[],
            topics=["thể thao"],
            confidence=0.85,
            reasoning="Exploratory topic query",
        )

        strategy = builder.build_strategy(analysis)

        assert strategy.top_k == 25, (
            f"Expected top_k=25 for BROAD, got {strategy.top_k}"
        )
        assert strategy.rerank, "Should rerank for BROAD scope"
        assert "entity_match" not in strategy.boosting_rules, (
            "Should not boost entity (no entities)"
        )
        assert "topic_match" in strategy.boosting_rules, "Should boost topic match"

    @pytest.mark.unit
    def test_analytical_broad_query(self, builder):
        """Test strategy for analytical query with top_k capping."""
        analysis = QueryAnalysis(
            original_query="Phân tích xu hướng lạm phát",
            intent=QueryIntent.ANALYTICAL,
            time_sensitivity=TimeSensitivity.HISTORICAL,
            scope=QueryScope.BROAD,
            entities=["lạm phát"],
            topics=["kinh tế"],
            confidence=0.88,
            reasoning="Analytical trend analysis",
        )

        strategy = builder.build_strategy(analysis)

        # BROAD (25) + ANALYTICAL (+10) = 35, capped at 30
        assert strategy.top_k == 30, f"Expected top_k=30 (capped), got {strategy.top_k}"
        assert strategy.rerank, "Should rerank for ANALYTICAL intent"
        assert "published_at" not in strategy.filters, (
            "Should not filter for HISTORICAL"
        )

    @pytest.mark.unit
    def test_recent_multi_topic_query(self, builder):
        """Test strategy for recent query with multiple topics."""
        analysis = QueryAnalysis(
            original_query="Tin trong tuần về công nghệ và AI",
            intent=QueryIntent.TEMPORAL,
            time_sensitivity=TimeSensitivity.RECENT,
            scope=QueryScope.MEDIUM,
            entities=["AI"],
            topics=["công nghệ", "AI"],
            confidence=0.92,
            reasoning="Recent news with multiple topics",
        )

        strategy = builder.build_strategy(analysis)

        assert strategy.top_k == 15, (
            f"Expected top_k=15 for MEDIUM, got {strategy.top_k}"
        )
        # Topics are no longer hard filtered
        # They are only used for boosting
        assert "recent" in strategy.boosting_rules, (
            "Should boost recent for RECENT time"
        )
        assert "topic_match" in strategy.boosting_rules, "Should boost topic match"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "scope,expected_top_k",
        [
            (QueryScope.NARROW, 5),
            (QueryScope.MEDIUM, 15),
            (QueryScope.BROAD, 25),
        ],
    )
    def test_top_k_by_scope(self, builder, scope, expected_top_k):
        """Parametrized test for top_k calculation by scope."""
        analysis = QueryAnalysis(
            original_query="Test query",
            intent=QueryIntent.FACTUAL,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=scope,
            entities=[],
            topics=[],
            confidence=0.9,
            reasoning="Test",
        )

        strategy = builder.build_strategy(analysis)
        assert strategy.top_k == expected_top_k
