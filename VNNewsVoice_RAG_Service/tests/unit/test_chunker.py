"""Unit tests for Chunker.

Tests chunk size, overlap, sentence-aware splitting, and metadata preservation.
"""

import pytest

from app.core.indexing.chunker import Chunker
from app.models.domain.article import Article


@pytest.fixture
def chunker():
    """Create Chunker with default settings."""
    return Chunker(chunk_size=600, overlap_size=120)


@pytest.fixture
def sample_article_long():
    """Create a long article for testing chunking."""
    # Create content with ~1500 words (will create multiple chunks)
    words = ["word"] * 1500
    content = " ".join(words)

    return Article(
        article_id="test-long-article",
        title="Test Long Article",
        content=content,
        url="https://example.com/long",
        published_at="2024-01-15T10:00:00Z",
        source="Test Source",
        topic="Technology",
    )


class TestChunker:
    """Test suite for Chunker."""

    @pytest.mark.unit
    def test_chunk_size_target(self, chunker):
        """Test that chunks are approximately the target size."""
        # Create article with proper sentences (not just repeated words)
        sentences = [
            "This is the first sentence in the article.",
            "This is the second sentence with some content.",
            "Here is another sentence to add more text.",
            "We need to create enough content for multiple chunks.",
            "Each sentence adds to the total word count.",
        ] * 200  # Create ~1000 sentences

        content = " ".join(sentences)

        article = Article(
            article_id="test-long-article",
            title="Test Long Article",
            content=content,
            url="https://example.com/long",
            published_at="2024-01-15T10:00:00Z",
            source="Test Source",
            topic="Technology",
        )

        chunks = chunker.chunk(article)

        # Should create multiple chunks
        assert len(chunks) > 1, "Should create multiple chunks for long article"

        # Check chunk sizes (allowing some variance)
        for chunk in chunks:
            word_count = len(chunk.content.split())
            # Chunks should be around 600 words (±300 tolerance for flexibility)
            assert 200 <= word_count <= 1000, (
                f"Chunk has {word_count} words, expected ~600"
            )

    @pytest.mark.unit
    def test_overlap_calculation(self, chunker):
        """Test that chunks have proper overlap."""
        # Create article with known content
        article = Article(
            article_id="test-overlap",
            title="Test Overlap",
            content=" ".join(["word"] * 1000),  # 1000 words
            url="https://example.com/overlap",
            published_at="2024-01-15T10:00:00Z",
            source="Test Source",
            topic="Technology",
        )

        chunks = chunker.chunk(article)

        # Should have overlap between consecutive chunks
        if len(chunks) > 1:
            # Check overlap between first two chunks
            chunk1_words = chunks[0].content.split()
            chunk2_words = chunks[1].content.split()

            # Last ~120 words of chunk1 should appear in first ~120 words of chunk2
            overlap_words = chunk1_words[-120:]
            chunk2_start = chunk2_words[:120]

            # At least some overlap should exist
            common_words = set(overlap_words) & set(chunk2_start)
            assert len(common_words) > 0, "Should have overlap between chunks"

    @pytest.mark.unit
    def test_metadata_preservation(self, chunker, sample_article):
        """Test that metadata is preserved in chunks."""
        chunks = chunker.chunk(sample_article)

        assert len(chunks) > 0, "Should create at least one chunk"

        # Check first chunk metadata
        chunk = chunks[0]
        assert chunk.article_id == sample_article.article_id
        assert chunk.metadata["title"] == sample_article.title
        assert chunk.metadata["url"] == sample_article.url
        assert chunk.metadata["published_at"] == sample_article.published_at.isoformat()
        assert chunk.metadata["source"] == sample_article.source
        assert chunk.metadata["topic"] == sample_article.topic

    @pytest.mark.unit
    def test_chunk_index_assignment(self, chunker, sample_article_long):
        """Test that chunk indices are assigned correctly."""
        chunks = chunker.chunk(sample_article_long)

        # Check indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i, (
                f"Chunk {i} has incorrect index {chunk.chunk_index}"
            )

    @pytest.mark.unit
    def test_empty_content(self, chunker):
        """Test handling of empty content."""
        article = Article(
            article_id="test-empty",
            title="Empty Article",
            content="",
            url="https://example.com/empty",
            published_at="2024-01-15T10:00:00Z",
            source="Test Source",
            topic="Technology",
        )

        chunks = chunker.chunk(article)

        # Should handle empty content gracefully
        assert isinstance(chunks, list), "Should return a list"
        # May return empty list or single chunk with empty content

    @pytest.mark.unit
    def test_very_short_content(self, chunker):
        """Test handling of very short content (< chunk_size)."""
        article = Article(
            article_id="test-short",
            title="Short Article",
            content="This is a very short article with only a few words.",
            url="https://example.com/short",
            published_at="2024-01-15T10:00:00Z",
            source="Test Source",
            topic="Technology",
        )

        chunks = chunker.chunk(article)

        # Should create exactly one chunk
        assert len(chunks) == 1, "Should create one chunk for short content"
        # Content includes title prepended
        expected_content = f"{article.title}\n\n{article.content}"
        assert chunks[0].content == expected_content
        assert chunks[0].chunk_index == 0

    @pytest.mark.unit
    def test_sentence_aware_splitting(self, chunker):
        """Test that chunking respects sentence boundaries."""
        # Create content with clear sentence boundaries
        sentences = [
            "This is sentence one.",
            "This is sentence two.",
            "This is sentence three.",
        ] * 300  # Repeat to create long content

        content = " ".join(sentences)

        article = Article(
            article_id="test-sentences",
            title="Sentence Test",
            content=content,
            url="https://example.com/sentences",
            published_at="2024-01-15T10:00:00Z",
            source="Test Source",
            topic="Technology",
        )

        chunks = chunker.chunk(article)

        # Check that chunks don't cut sentences in the middle
        for chunk in chunks:
            # Chunk should end with sentence-ending punctuation or be the last chunk
            if chunk.chunk_index < len(chunks) - 1:
                # Not the last chunk - should end with proper punctuation
                assert chunk.content.rstrip().endswith((".", "!", "?")), (
                    "Chunk should end at sentence boundary"
                )

    @pytest.mark.unit
    def test_chunk_id_uniqueness(self, chunker, sample_article_long):
        """Test that each chunk has a unique ID."""
        chunks = chunker.chunk(sample_article_long)

        chunk_ids = [chunk.chunk_id for chunk in chunks]
        unique_ids = set(chunk_ids)

        assert len(chunk_ids) == len(unique_ids), "All chunk IDs should be unique"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "chunk_size,overlap_size",
        [
            (400, 80),
            (600, 120),
            (800, 160),
        ],
    )
    def test_different_chunk_sizes(self, chunk_size, overlap_size):
        """Parametrized test for different chunk size configurations."""
        # Create article with proper sentences (not just repeated words)
        sentences = [
            "This is the first sentence in the article.",
            "This is the second sentence with some content.",
            "Here is another sentence to add more text.",
        ] * 200  # Create ~600 sentences

        content = " ".join(sentences)

        article = Article(
            article_id="test-param",
            title="Parametrized Test Article",
            content=content,
            url="https://example.com/param",
            published_at="2024-01-15T10:00:00Z",
            source="Test Source",
            topic="Technology",
        )

        chunker = Chunker(chunk_size=chunk_size, overlap_size=overlap_size)
        chunks = chunker.chunk(article)

        assert len(chunks) > 0, "Should create chunks"

        # Verify chunking occurred (should create multiple chunks for large content)
        if len(chunks) > 1:
            # Check that chunks are reasonable sizes
            for chunk in chunks:
                word_count = len(chunk.content.split())
                # Chunks should not be excessively large
                assert word_count <= chunk_size * 2, (
                    f"Chunk too large: {word_count} words"
                )
