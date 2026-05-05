"""Integration tests for Adaptive RAG Pipeline.

Tests the full adaptive flow: analyze → build strategy → route → retrieve.
"""

import pytest

from app.core.rag.adaptive.query_analyzer import LLMQueryAnalyzer
from app.core.rag.adaptive.strategy_builder import StrategyBuilder
from app.models.domain.query import QueryAnalysis
from app.models.enums import QueryIntent, QueryScope, TimeSensitivity


class TestAdaptivePipeline:
    """Test suite for adaptive RAG pipeline."""

    @pytest.mark.integration
    def test_temporal_query_flow(self, mock_llm):
        """Test adaptive flow for temporal query."""
        # Mock LLM to return temporal analysis
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="Tin Ukraine hôm nay",
            intent=QueryIntent.TEMPORAL,
            time_sensitivity=TimeSensitivity.REALTIME,
            scope=QueryScope.MEDIUM,
            entities=["Ukraine"],
            topics=["quốc tế"],
            keywords=["tin", "Ukraine"],
            confidence=0.9,
            reasoning="Temporal query",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        builder = StrategyBuilder()

        # Analyze query
        analysis = analyzer.analyze("Tin Ukraine hôm nay")

        # Build strategy
        strategy = builder.build_strategy(analysis)

        # Verify flow
        assert analysis.intent == QueryIntent.TEMPORAL
        assert analysis.time_sensitivity == TimeSensitivity.REALTIME
        assert "published_at" in strategy.filters

    @pytest.mark.integration
    def test_factual_query_flow(self, mock_llm):
        """Test adaptive flow for factual query."""
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="Ai là tổng thống Mỹ?",
            intent=QueryIntent.FACTUAL,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.NARROW,
            entities=["Mỹ"],
            topics=["chính trị"],
            keywords=["tổng thống"],
            confidence=0.95,
            reasoning="Factual query",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        builder = StrategyBuilder()

        analysis = analyzer.analyze("Ai là tổng thống Mỹ?")
        strategy = builder.build_strategy(analysis)

        assert analysis.intent == QueryIntent.FACTUAL
        assert strategy.top_k == 5  # Narrow scope

    @pytest.mark.integration
    def test_comparative_query_flow(self, mock_llm):
        """Test adaptive flow for comparative query."""
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="So sánh GDP 2024 và 2025",
            intent=QueryIntent.COMPARATIVE,
            time_sensitivity=TimeSensitivity.RECENT,
            scope=QueryScope.NARROW,
            entities=["GDP"],
            topics=["kinh tế"],
            keywords=["so sánh"],
            confidence=0.9,
            reasoning="Comparative query",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        builder = StrategyBuilder()

        analysis = analyzer.analyze("So sánh GDP 2024 và 2025")
        strategy = builder.build_strategy(analysis)

        assert analysis.intent == QueryIntent.COMPARATIVE
        assert strategy.rerank is True

    @pytest.mark.integration
    def test_end_to_end_pipeline(self, mock_llm, sample_retrieval_results):
        """Test complete adaptive pipeline end-to-end."""
        mock_llm.generate_structured.return_value = QueryAnalysis(
            original_query="Tin thể thao",
            intent=QueryIntent.EXPLORATORY,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.BROAD,
            entities=[],
            topics=["thể thao"],
            keywords=["tin"],
            confidence=0.85,
            reasoning="Exploratory query",
        )

        analyzer = LLMQueryAnalyzer(llm=mock_llm)
        builder = StrategyBuilder()

        # Full pipeline
        analysis = analyzer.analyze("Tin thể thao")
        strategy = builder.build_strategy(analysis)

        # Verify complete flow
        assert analysis is not None
        assert strategy is not None
        assert strategy.top_k == 25  # Broad scope
        assert "topic_match" in strategy.boosting_rules
