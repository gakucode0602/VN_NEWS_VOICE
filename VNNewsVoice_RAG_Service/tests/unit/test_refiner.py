"""Unit tests for LLMQueryRefiner.

Tests query refinement logic, JSON parsing, and error handling.
"""

import pytest

from app.core.rag.iterative.refiner import LLMQueryRefiner
from app.models.domain.iteration import RetrievalQuality
from app.models.enums import RefinementType


@pytest.fixture
def refiner(mock_llm):
    """Create LLMQueryRefiner with mock LLM."""
    return LLMQueryRefiner(llm=mock_llm)


class TestLLMQueryRefiner:
    """Test suite for LLMQueryRefiner."""

    @pytest.mark.unit
    def test_refine_successful(self, mock_llm, sample_retrieval_results):
        """Test successful query refinement."""
        # Mock LLM response with valid JSON
        mock_llm.generate.return_value = """
        {
            "refined_query": "tin tức Việt Nam mới nhất",
            "refinement_type": "expand",
            "reasoning": "Expanded query to get more results",
            "entities_added": ["Việt Nam"],
            "filters_changed": false
        }
        """

        refiner = LLMQueryRefiner(llm=mock_llm)

        quality = RetrievalQuality(
            is_good_enough=False,
            avg_score=0.3,
            top_score=0.5,
            total_chunks=2,
            confidence=0.4,
            score_variance=0.1,
            reasons=["Low average score"],
            threshold_config={},
        )

        refinement = refiner.refine(
            original_query="tin Việt Nam",
            current_query="tin Việt Nam",
            retrieval_results=sample_retrieval_results,
            quality=quality,
        )

        assert refinement.refined_query == "tin tức việt nam mới nhất"
        assert refinement.refinement_type == RefinementType.EXPAND
        assert "Việt Nam" in refinement.entities_added
        assert refinement.filters_changed is False

    @pytest.mark.unit
    def test_refine_with_invalid_json(self, mock_llm, sample_retrieval_results):
        """Test refinement when LLM returns invalid JSON."""
        # Mock LLM response with invalid JSON
        mock_llm.generate.return_value = "This is not valid JSON"

        refiner = LLMQueryRefiner(llm=mock_llm)

        quality = RetrievalQuality(
            is_good_enough=False,
            avg_score=0.3,
            top_score=0.5,
            total_chunks=2,
            confidence=0.4,
            score_variance=0.1,
            reasons=["Low score"],
            threshold_config={},
        )

        refinement = refiner.refine(
            original_query="test query",
            current_query="test query",
            retrieval_results=sample_retrieval_results,
            quality=quality,
        )

        # Should return default refinement
        assert refinement.refined_query == "test query"
        assert refinement.refinement_type == RefinementType.NONE

    @pytest.mark.unit
    def test_refine_with_missing_fields(self, mock_llm, sample_retrieval_results):
        """Test refinement when JSON is missing required fields."""
        # Mock LLM response with incomplete JSON
        mock_llm.generate.return_value = """
        {
            "refined_query": "better query",
            "refinement_type": "expand"
        }
        """

        refiner = LLMQueryRefiner(llm=mock_llm)

        quality = RetrievalQuality(
            is_good_enough=False,
            avg_score=0.3,
            top_score=0.5,
            total_chunks=2,
            confidence=0.4,
            score_variance=0.1,
            reasons=["Low score"],
            threshold_config={},
        )

        refinement = refiner.refine(
            original_query="test query",
            current_query="test query",
            retrieval_results=sample_retrieval_results,
            quality=quality,
        )

        # Should fallback to default
        assert refinement.refinement_type == RefinementType.NONE

    @pytest.mark.unit
    def test_extract_llm_response_with_markdown(self, refiner):
        """Test JSON extraction from markdown code blocks."""
        response = """
        Here is the JSON:
        ```json
        {"key": "value"}
        ```
        """

        extracted = refiner._extract_llm_response(response)

        assert extracted == '{"key": "value"}'

    @pytest.mark.unit
    def test_extract_llm_response_nested_json(self, refiner):
        """Test JSON extraction with nested objects."""
        response = """
        Some text before
        {"outer": {"inner": "value"}, "array": [1, 2, 3]}
        Some text after
        """

        extracted = refiner._extract_llm_response(response)

        assert '"outer"' in extracted
        assert '"inner"' in extracted

    @pytest.mark.unit
    def test_parse_response_valid_json(self, refiner):
        """Test parsing of valid JSON response."""
        response = """
        {
            "refined_query": "test",
            "refinement_type": "expand",
            "reasoning": "reason",
            "entities_added": ["entity1"],
            "filters_changed": true
        }
        """

        parsed = refiner._parse_response(response)

        assert parsed is not None
        assert parsed["refined_query"] == "test"
        assert parsed["refinement_type"] == "expand"
        assert parsed["filters_changed"] is True

    @pytest.mark.unit
    def test_parse_response_invalid_json(self, refiner):
        """Test parsing of invalid JSON."""
        response = "not valid json"

        parsed = refiner._parse_response(response)

        assert parsed is None

    @pytest.mark.unit
    def test_build_refine_prompt(self, refiner):
        """Test prompt building for refinement."""
        prompt = refiner._build_refine_prompt(
            original_query="tin Việt Nam",
            current_query="tin Việt Nam hôm nay",
            reasons=["Low average score", "Not enough chunks"],
            context_snippets=["Title 1", "Title 2"],
        )

        assert "tin Việt Nam" in prompt
        assert "tin Việt Nam hôm nay" in prompt
        assert "Low average score" in prompt
        assert "Title 1" in prompt

    @pytest.mark.unit
    def test_get_default_query_refinement(self, refiner):
        """Test default refinement fallback."""
        default = refiner._get_default_query_refinement("test query")

        assert default.original_query == "test query"
        assert default.refined_query == "test query"
        assert default.refinement_type == RefinementType.NONE
        assert default.filters_changed is False

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "refinement_type",
        [
            "expand",
            "narrow",
            "clarify",
            "add_context",
        ],
    )
    def test_different_refinement_types(
        self, mock_llm, sample_retrieval_results, refinement_type
    ):
        """Parametrized test for different refinement types."""
        mock_llm.generate.return_value = f"""
        {{
            "refined_query": "refined test query",
            "refinement_type": "{refinement_type}",
            "reasoning": "Test reasoning",
            "entities_added": [],
            "filters_changed": false
        }}
        """

        refiner = LLMQueryRefiner(llm=mock_llm)

        quality = RetrievalQuality(
            is_good_enough=False,
            avg_score=0.3,
            top_score=0.5,
            total_chunks=2,
            confidence=0.4,
            score_variance=0.1,
            reasons=["Test reason"],
            threshold_config={},
        )

        refinement = refiner.refine(
            original_query="test query",
            current_query="test query",
            retrieval_results=sample_retrieval_results,
            quality=quality,
        )

        assert refinement.refinement_type == RefinementType(refinement_type)
