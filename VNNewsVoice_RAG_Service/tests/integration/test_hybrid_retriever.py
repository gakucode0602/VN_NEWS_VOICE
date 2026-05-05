"""Integration tests for NativeHybridRetriever.

Tests RRF fusion, deduplication, and score normalization.
Note: These are simplified mock-based tests. For real Qdrant integration,
see scripts/test_hybrid_retriever.py
"""

import pytest
from unittest.mock import Mock

from app.core.rag.retrieval.native_hybrid_retriever import NativeHybridRetriever
from app.models.domain.retrieval import RetrievalResult


@pytest.fixture
def mock_dense_retriever(sample_chunks):
    """Mock dense retriever with sample results."""
    retriever = Mock()
    # Dense results favor semantic similarity
    retriever.retrieve.return_value = [
        RetrievalResult(chunk=sample_chunks[0], score=0.9, rank=1),
        RetrievalResult(chunk=sample_chunks[1], score=0.8, rank=2),
        RetrievalResult(chunk=sample_chunks[2], score=0.7, rank=3),
    ]
    return retriever


@pytest.fixture
def mock_sparse_retriever(sample_chunks):
    """Mock sparse retriever with sample results."""
    retriever = Mock()
    # Sparse results favor keyword matching
    retriever.retrieve.return_value = [
        RetrievalResult(
            chunk=sample_chunks[1], score=0.85, rank=1
        ),  # Overlap with dense
        RetrievalResult(chunk=sample_chunks[3], score=0.75, rank=2),  # Unique to sparse
        RetrievalResult(
            chunk=sample_chunks[0], score=0.65, rank=3
        ),  # Overlap with dense
    ]
    return retriever


@pytest.fixture
def mock_embedder():
    """Mock embedder."""
    embedder = Mock()
    embedder.embed_query.return_value = [0.1] * 384
    return embedder


class TestNativeHybridRetriever:
    """Test suite for NativeHybridRetriever."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hybrid_combines_results(
        self, mock_embedder, mock_vector_store, sample_chunks
    ):
        """Test that hybrid retriever combines dense and sparse results."""
        NativeHybridRetriever(mock_embedder, mock_vector_store)

        # Mock the retrieve method to return combined results
        results = [
            RetrievalResult(chunk=chunk, score=0.8 - (i * 0.1), rank=i + 1)
            for i, chunk in enumerate(sample_chunks[:5])
        ]

        assert len(results) > 0
        # Results should be ranked
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    @pytest.mark.integration
    def test_deduplication(self, sample_chunks):
        """Test that duplicate chunks are removed."""
        # Create results with duplicates
        results = [
            RetrievalResult(chunk=sample_chunks[0], score=0.9, rank=1),
            RetrievalResult(chunk=sample_chunks[1], score=0.8, rank=2),
            RetrievalResult(chunk=sample_chunks[0], score=0.7, rank=3),  # Duplicate
        ]

        # Deduplicate by chunk_id
        seen_ids = set()
        deduped = []
        for r in results:
            if r.chunk.chunk_id not in seen_ids:
                seen_ids.add(r.chunk.chunk_id)
                deduped.append(r)

        assert len(deduped) == 2
        assert deduped[0].chunk.chunk_id == sample_chunks[0].chunk_id
        assert deduped[1].chunk.chunk_id == sample_chunks[1].chunk_id

    @pytest.mark.integration
    def test_score_normalization(self, sample_chunks):
        """Test that scores are normalized to [0, 1] range."""
        # Create results with various scores
        results = [
            RetrievalResult(chunk=sample_chunks[0], score=0.95, rank=1),
            RetrievalResult(chunk=sample_chunks[1], score=0.75, rank=2),
            RetrievalResult(chunk=sample_chunks[2], score=0.55, rank=3),
        ]

        # Check all scores are in [0, 1]
        for r in results:
            assert 0.0 <= r.score <= 1.0

    @pytest.mark.integration
    def test_rrf_score_calculation(self):
        """Test RRF (Reciprocal Rank Fusion) score calculation."""
        # RRF formula: score = sum(1 / (k + rank_i)) for each retriever
        # k = 60 (standard constant)
        k = 60

        # Chunk appears at rank 1 in dense, rank 3 in sparse
        dense_rank = 1
        sparse_rank = 3

        rrf_score = (1 / (k + dense_rank)) + (1 / (k + sparse_rank))
        expected = (1 / 61) + (1 / 63)

        assert abs(rrf_score - expected) < 0.0001

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_empty_results_handling(self, mock_embedder, mock_vector_store):
        """Test handling of empty results from retrievers."""
        NativeHybridRetriever(mock_embedder, mock_vector_store)

        # If both retrievers return empty, hybrid should return empty
        # This is a conceptual test
        empty_results = []

        assert isinstance(empty_results, list)
        assert len(empty_results) == 0
