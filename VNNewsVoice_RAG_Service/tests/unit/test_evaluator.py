"""Unit tests for RetrievalQualityEvaluator.

Tests convergence criteria, quality assessment, and confidence scoring.
"""

import pytest

from app.core.rag.iterative.evaluator import RetrievalQualityEvaluator
from app.models.domain.retrieval import RetrievalResult


class TestRetrievalQualityEvaluator:
    """Test suite for RetrievalQualityEvaluator."""

    @pytest.mark.unit
    def test_evaluate_good_quality_results(self, sample_retrieval_results):
        """Test evaluation of high-quality retrieval results."""
        evaluator = RetrievalQualityEvaluator(
            convergence_threshold=0.7,
            min_chunks=3,
            min_avg_score=0.4,
        )

        quality = evaluator.evaluate(sample_retrieval_results, "test query")

        # Should pass all checks
        assert quality.is_good_enough is True
        assert quality.avg_score > 0.4
        assert quality.top_score >= 0.7
        assert quality.total_chunks >= 3
        assert quality.confidence > 0.5

    @pytest.mark.unit
    def test_evaluate_empty_results(self):
        """Test evaluation of empty results."""
        evaluator = RetrievalQualityEvaluator()

        quality = evaluator.evaluate([], "test query")

        assert quality.is_good_enough is False
        assert quality.avg_score == 0.0
        assert quality.top_score == 0.0
        assert quality.total_chunks == 0
        assert quality.confidence == 0.0
        assert "No results retrieved" in quality.reasons

    @pytest.mark.unit
    def test_evaluate_low_avg_score(self, sample_chunks):
        """Test evaluation when average score is too low."""
        # Create results with low scores
        results = [
            RetrievalResult(chunk=chunk, score=0.2 + (i * 0.05), rank=i + 1)
            for i, chunk in enumerate(sample_chunks[:5])
        ]

        evaluator = RetrievalQualityEvaluator(
            convergence_threshold=0.7,
            min_chunks=3,
            min_avg_score=0.4,
        )

        quality = evaluator.evaluate(results, "test query")

        assert quality.is_good_enough is False
        assert quality.avg_score < 0.4
        assert any("Average score" in reason for reason in quality.reasons)

    @pytest.mark.unit
    def test_evaluate_low_top_score(self, sample_chunks):
        """Test evaluation when top score doesn't meet threshold."""
        # Create results with decent avg but low top score
        results = [
            RetrievalResult(chunk=chunk, score=0.5, rank=i + 1)
            for i, chunk in enumerate(sample_chunks[:5])
        ]

        evaluator = RetrievalQualityEvaluator(
            convergence_threshold=0.7,
            min_chunks=3,
            min_avg_score=0.4,
        )

        quality = evaluator.evaluate(results, "test query")

        assert quality.is_good_enough is False
        assert quality.top_score < 0.7
        assert any("Top score" in reason for reason in quality.reasons)

    @pytest.mark.unit
    def test_evaluate_insufficient_chunks(self, sample_chunks):
        """Test evaluation when not enough chunks retrieved."""
        # Create only 2 results
        results = [
            RetrievalResult(chunk=chunk, score=0.8, rank=i + 1)
            for i, chunk in enumerate(sample_chunks[:2])
        ]

        evaluator = RetrievalQualityEvaluator(
            convergence_threshold=0.7,
            min_chunks=3,
            min_avg_score=0.4,
        )

        quality = evaluator.evaluate(results, "test query")

        assert quality.is_good_enough is False
        assert quality.total_chunks < 3
        assert any("Total chunks" in reason for reason in quality.reasons)

    @pytest.mark.unit
    def test_confidence_calculation(self, sample_chunks):
        """Test confidence score calculation."""
        # Create high-quality results
        results = [
            RetrievalResult(chunk=chunk, score=0.9 - (i * 0.1), rank=i + 1)
            for i, chunk in enumerate(sample_chunks[:5])
        ]

        evaluator = RetrievalQualityEvaluator(
            convergence_threshold=0.7,
            min_chunks=3,
            min_avg_score=0.4,
        )

        quality = evaluator.evaluate(results, "test query")

        # Confidence should be high for good results
        assert 0.0 <= quality.confidence <= 1.0
        assert quality.confidence > 0.7

    @pytest.mark.unit
    def test_score_variance_calculation(self, sample_chunks):
        """Test score variance calculation."""
        # Create results with varying scores
        results = [
            RetrievalResult(chunk=sample_chunks[0], score=0.9, rank=1),
            RetrievalResult(chunk=sample_chunks[1], score=0.5, rank=2),
            RetrievalResult(chunk=sample_chunks[2], score=0.3, rank=3),
        ]

        evaluator = RetrievalQualityEvaluator()
        quality = evaluator.evaluate(results, "test query")

        # Variance should be > 0 for varying scores
        assert quality.score_variance > 0.0

    @pytest.mark.unit
    def test_threshold_config_preservation(self, sample_retrieval_results):
        """Test that threshold config is preserved in quality result."""
        evaluator = RetrievalQualityEvaluator(
            convergence_threshold=0.8,
            min_chunks=5,
            min_avg_score=0.5,
        )

        quality = evaluator.evaluate(sample_retrieval_results, "test query")

        assert quality.threshold_config["convergence_threshold"] == 0.8
        assert quality.threshold_config["min_chunks"] == 5
        assert quality.threshold_config["min_avg_score"] == 0.5

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "convergence_threshold,min_chunks,min_avg_score",
        [
            (0.6, 2, 0.3),
            (0.7, 3, 0.4),
            (0.8, 5, 0.5),
        ],
    )
    def test_different_thresholds(
        self, sample_retrieval_results, convergence_threshold, min_chunks, min_avg_score
    ):
        """Parametrized test for different threshold configurations."""
        evaluator = RetrievalQualityEvaluator(
            convergence_threshold=convergence_threshold,
            min_chunks=min_chunks,
            min_avg_score=min_avg_score,
        )

        quality = evaluator.evaluate(sample_retrieval_results, "test query")

        # Quality should be evaluated based on provided thresholds
        assert (
            quality.threshold_config["convergence_threshold"] == convergence_threshold
        )
        assert quality.threshold_config["min_chunks"] == min_chunks
        assert quality.threshold_config["min_avg_score"] == min_avg_score
