"""Shared pytest fixtures for testing."""

import pytest
from typing import List
from unittest.mock import Mock

from app.models.domain.article import Article, DocumentChunk
from app.models.domain.retrieval import RetrievalResult
from app.models.domain.query import QueryAnalysis
from app.models.enums import QueryIntent, QueryScope, TimeSensitivity


@pytest.fixture
def mock_llm():
    """Mock LLM adapter with predictable responses."""
    llm = Mock()

    # Default response for query analysis
    llm.generate.return_value = """
    {
        "intent": "factual",
        "time_sensitivity": "timeless",
        "scope": "narrow",
        "entities": ["test"],
        "topics": ["technology"],
        "keywords": ["test", "query"],
        "confidence": 0.9,
        "reasoning": "Test query analysis"
    }
    """

    return llm


@pytest.fixture
def mock_vector_store():
    """Mock vector store with in-memory storage."""
    store = Mock()

    # Mock search results
    store.search.return_value = []
    store.upsert_chunks.return_value = None
    store.delete_by_article_id.return_value = None

    return store


@pytest.fixture
def mock_redis_cache():
    """Mock Redis cache."""
    cache = Mock()

    cache.get.return_value = None
    cache.set.return_value = True
    cache.clear.return_value = True
    cache.get_stats.return_value = Mock(hits=0, misses=0, hit_rate=0.0)

    return cache


@pytest.fixture
def sample_article() -> Article:
    """Sample article for testing."""
    return Article(
        article_id="test-article-123",
        title="Test Article Title",
        content="This is a test article content for testing purposes.",
        url="https://example.com/test-article",
        published_at="2024-01-15T10:00:00Z",
        source="Test Source",
        topic="Technology",
    )


@pytest.fixture
def sample_chunk() -> DocumentChunk:
    """Sample document chunk for testing."""
    return DocumentChunk(
        chunk_id="test-chunk-123",
        article_id="test-article-123",
        content="This is a test chunk content.",
        chunk_index=0,
        metadata={
            "title": "Test Article Title",
            "url": "https://example.com/test-article",
            "published_at": "2024-01-15T10:00:00Z",
            "source": "Test Source",
            "topic": "Technology",
        },
    )


@pytest.fixture
def sample_chunks(sample_chunk) -> List[DocumentChunk]:
    """Multiple sample chunks for testing."""
    chunks = []
    for i in range(5):
        chunk = DocumentChunk(
            chunk_id=f"test-chunk-{i}",
            article_id=f"test-article-{i}",
            content=f"This is test chunk {i} content.",
            chunk_index=i,
            metadata={
                "title": f"Test Article {i}",
                "url": f"https://example.com/article-{i}",
                "published_at": "2024-01-15T10:00:00Z",
                "source": "Test Source",
                "topic": "Technology",
            },
        )
        chunks.append(chunk)
    return chunks


@pytest.fixture
def sample_retrieval_results(sample_chunks) -> List[RetrievalResult]:
    """Sample retrieval results for testing."""
    results = []
    for i, chunk in enumerate(sample_chunks):
        result = RetrievalResult(
            chunk=chunk,
            score=0.9 - (i * 0.1),  # Decreasing scores
            rank=i + 1,
        )
        results.append(result)
    return results


@pytest.fixture
def sample_query_analysis() -> QueryAnalysis:
    """Sample query analysis for testing."""
    return QueryAnalysis(
        original_query="Test query",
        intent=QueryIntent.FACTUAL,
        time_sensitivity=TimeSensitivity.TIMELESS,
        scope=QueryScope.NARROW,
        entities=["test"],
        topics=["technology"],
        keywords=["test", "query"],
        confidence=0.9,
        reasoning="Test query analysis",
    )


@pytest.fixture
def test_settings():
    """Test settings override."""
    from app.config.settings import Settings

    return Settings(
        debug_mode=True,
        llm_provider="ollama",
        ollama_base_url="http://localhost:11434",
        ollama_model_name="gemma2:2b",
        embedding_provider="local",
        embedding_dimension=384,
        dense_local_embed_model_name="sentence-transformers/all-MiniLM-L6-v2",
        sparse_local_embed_model_name="Qdrant/bm25",
        qdrant_host="localhost",
        qdrant_port=6333,
        qdrant_collection_name="test_collection",
        api_host="0.0.0.0",
        api_port=8000,
        log_level="INFO",
        adaptive_mode=False,
        iterative_mode=False,
        max_iterations=3,
        redis_host="localhost",
        redis_port=6379,
        redis_ttl_seconds=3600,
        gemini_api_key="",
        gemini_model_name="gemini-1.5-flash",
        nvidia_base_url="",
        nvidia_api_key="",
        nvidia_model_name="meta/llama-3.1-8b-instruct",
    )
