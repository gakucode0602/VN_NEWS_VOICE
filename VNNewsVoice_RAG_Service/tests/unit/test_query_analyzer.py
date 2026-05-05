"""Unit tests for LLMQueryAnalyzer.

Migrated from scripts/test_query_analyzer.py
"""

import pytest

from app.core.rag.adaptive.query_analyzer import LLMQueryAnalyzer
from app.models.enums import QueryIntent, QueryScope, TimeSensitivity
from app.models.domain.query import QueryAnalysis


@pytest.fixture
def analyzer(mock_llm):
    """Create LLMQueryAnalyzer with mock LLM."""
    return LLMQueryAnalyzer(llm=mock_llm)


class TestQueryAnalyzer:
    """Test suite for LLMQueryAnalyzer."""

    @pytest.mark.unit
    def test_analyze_temporal_query(self, mock_llm):
        """Test analysis of temporal query."""
        # Mock LLM response for temporal query
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="Tin Ukraine hôm nay",
            intent=QueryIntent.TEMPORAL,
            time_sensitivity=TimeSensitivity.REALTIME,
            scope=QueryScope.MEDIUM,
            entities=["Ukraine"],
            topics=["quốc tế", "chiến tranh"],
            keywords=["tin", "Ukraine", "hôm nay"],
            confidence=0.9,
            reasoning="Temporal query with realtime requirement",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        result = analyzer.analyze("Tin Ukraine hôm nay")

        assert result.intent == QueryIntent.TEMPORAL
        assert result.time_sensitivity == TimeSensitivity.REALTIME
        assert result.scope == QueryScope.MEDIUM
        assert "Ukraine" in result.entities
        assert result.confidence == 0.9

    @pytest.mark.unit
    def test_analyze_factual_query(self, mock_llm):
        """Test analysis of factual query."""
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="Ai là tổng thống Mỹ?",
            intent=QueryIntent.FACTUAL,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.NARROW,
            entities=["Mỹ"],
            topics=["chính trị"],
            keywords=["tổng thống", "Mỹ"],
            confidence=0.95,
            reasoning="Factual query about current US president",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        result = analyzer.analyze("Ai là tổng thống Mỹ?")

        assert result.intent == QueryIntent.FACTUAL
        assert result.time_sensitivity == TimeSensitivity.TIMELESS
        assert result.scope == QueryScope.NARROW
        assert "Mỹ" in result.entities

    @pytest.mark.unit
    def test_analyze_comparative_query(self, mock_llm):
        """Test analysis of comparative query."""
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="So sánh GDP 2024 và 2025",
            intent=QueryIntent.COMPARATIVE,
            time_sensitivity=TimeSensitivity.RECENT,
            scope=QueryScope.NARROW,
            entities=["GDP", "2024", "2025"],
            topics=["kinh tế"],
            keywords=["so sánh", "GDP"],
            confidence=0.9,
            reasoning="Comparative analysis of GDP across years",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        result = analyzer.analyze("So sánh GDP 2024 và 2025")

        assert result.intent == QueryIntent.COMPARATIVE
        assert result.time_sensitivity == TimeSensitivity.RECENT
        assert "GDP" in result.entities

    @pytest.mark.unit
    def test_analyze_exploratory_query(self, mock_llm):
        """Test analysis of exploratory query."""
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="Tin thể thao",
            intent=QueryIntent.EXPLORATORY,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.BROAD,
            entities=[],
            topics=["thể thao"],
            keywords=["tin", "thể thao"],
            confidence=0.85,
            reasoning="Broad exploratory query about sports",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        result = analyzer.analyze("Tin thể thao")

        assert result.intent == QueryIntent.EXPLORATORY
        assert result.scope == QueryScope.BROAD
        assert "thể thao" in result.topics

    @pytest.mark.unit
    def test_analyze_with_cache(self, mock_llm, mock_redis_cache):
        """Test query analysis with cache integration."""
        analyzer = LLMQueryAnalyzer(llm=mock_llm, cache=mock_redis_cache)

        # First call - cache miss
        mock_redis_cache.get.return_value = None
        analyzer.analyze("Test query")

        # Verify LLM was called
        assert mock_llm.generate_structured.called
        # Verify cache set was called
        assert mock_redis_cache.set.called

    @pytest.mark.unit
    def test_fallback_on_invalid_json(self, mock_llm):
        """Test fallback to default analysis when LLM returns invalid JSON."""
        # Mock invalid JSON response
        mock_llm.generate_structured.side_effect = ValueError("LLM Error")

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        result = analyzer.analyze("Test query")

        # Should return default analysis
        assert result is not None
        assert result.intent == QueryIntent.EXPLORATORY  # Default intent
        assert result.original_query == "Test query"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "query,expected_intent",
        [
            ("Tin Ukraine hôm nay", QueryIntent.TEMPORAL),
            ("Ai là tổng thống Mỹ?", QueryIntent.FACTUAL),
            ("So sánh GDP 2024 và 2025", QueryIntent.COMPARATIVE),
            ("Tin thể thao", QueryIntent.EXPLORATORY),
            ("Vinicius giành Quả bóng vàng", QueryIntent.FACTUAL),
            ("Phân tích xu hướng lạm phát", QueryIntent.ANALYTICAL),
        ],
    )
    def test_analyze_parametrized(self, mock_llm, query, expected_intent):
        """Parametrized test for different query types."""
        # Mock response based on expected intent
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query=query,
            intent=expected_intent,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.MEDIUM,
            entities=[],
            topics=[],
            keywords=[],
            confidence=0.9,
            reasoning="Test",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        result = analyzer.analyze(query)

        assert result.intent == expected_intent
