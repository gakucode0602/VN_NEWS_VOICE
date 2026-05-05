import logging
from typing import Any, Dict, List, Optional

from app.core.rag.retrieval.base import BaseRetrieval
from app.models.domain.retrieval import RetrievalResult
from underthesea import word_tokenize
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


@DeprecationWarning
class SparseRetriever(BaseRetrieval):
    """Sparse retriever using BM25 keyword search (STUB)."""

    def __init__(self, embedder, vector_store):
        """Initialize sparse retriever stub."""
        super().__init__(embedder, vector_store)
        self._chunks_cache = None
        self._tokenize_corpus = None
        self._bm25 = None

    def retrieve(
        self, query: str, top_k: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve using BM25 keyword search.

        Args:
            query: User query string
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of RetrievalResult sorted by BM25 score descending
        """
        # Ensure corpus is loaded and BM25 index built
        self._ensure_corpus_loaded()

        if self._chunks_cache is None:
            logger.warning("Vector database is empty")
            return []

        # Handle empty query
        if not query or not query.strip():
            logger.warning("Empty query provided to SparseRetriever")
            return []

        # Tokenize query
        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            logger.warning(f"Query tokenization resulted in empty tokens: '{query}'")
            return []

        # Calculate BM25 scores for all chunks
        scores = self._bm25.get_scores(tokenized_query)

        # Zip chunks with scores and apply filters
        chunk_score_pairs = [
            (chunk, score)
            for chunk, score in zip(self._chunks_cache, scores)
            if self._match_filters(chunk.metadata, filters)
            and score > 0  # Filter out zero scores
        ]

        # Handle no matches
        if not chunk_score_pairs:
            logger.info(f"No matching chunks found for query: '{query[:50]}...'")
            return []

        # Sort by score descending
        sorted_pairs = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)

        # Take top-k
        top_k_pairs = sorted_pairs[:top_k]

        # Build RetrievalResult objects
        retrieval_results = [
            RetrievalResult(chunk=chunk, score=float(score), rank=rank)
            for rank, (chunk, score) in enumerate(top_k_pairs, start=1)
        ]

        logger.info(
            f"SparseRetriever found {len(retrieval_results)} results "
            f"(filtered from {len(chunk_score_pairs)} matches)"
        )

        return retrieval_results

    def _tokenize(self, text: str) -> List[str]:
        lowercase_list = " ".join(text.lower().strip().split())

        word_tokenzed_text = word_tokenize(lowercase_list)

        # Filters stop words (OPTIONAL)

        # =============================

        return [str(word) for word in word_tokenzed_text]

    def _ensure_corpus_loaded(self):
        """Lazy load chunks and build BM25 index (once)."""
        if self._chunks_cache is not None:
            return  # Already loaded

        logger.info("Loading corpus for BM25 indexing...")

        # Fetch all chunks from vector store
        self._chunks_cache = self.vector_store.get_all()

        # Tokenize all chunk contents
        self._tokenize_corpus = [
            self._tokenize(chunk.content) for chunk in self._chunks_cache
        ]

        # Build BM25 index
        self._bm25 = BM25Okapi(self._tokenize_corpus)

        logger.info(f"BM25 index built with {len(self._chunks_cache)} chunks")

    def _match_filters(
        self, metadata: Dict[str, Any], filters: Optional[Dict[str, Any]]
    ) -> bool:
        # No filters = match all
        if filters is None or not filters:
            return True

        for key, value in filters.items():
            if key not in metadata:
                return False

            if isinstance(value, (str, int)):
                if metadata[key] != value:
                    return False

            elif isinstance(value, dict):
                meta_value = metadata[key]

                # Normalize: convert ISO date string to float for numeric comparisons
                def _to_float(v):
                    if isinstance(v, (int, float)):
                        return float(v)
                    if isinstance(v, str):
                        try:
                            from datetime import datetime

                            return datetime.fromisoformat(
                                v.replace("Z", "+00:00")
                            ).timestamp()
                        except Exception:
                            try:
                                return float(v)
                            except Exception:
                                return None
                    return None

                if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                    meta_f = _to_float(meta_value)
                    if meta_f is None:
                        return False  # Cannot compare, skip

                    if "gte" in value:
                        filter_f = _to_float(value["gte"])
                        if filter_f is not None and meta_f < filter_f:
                            return False
                    if "lte" in value:
                        filter_f = _to_float(value["lte"])
                        if filter_f is not None and meta_f > filter_f:
                            return False
                    if "gt" in value:
                        filter_f = _to_float(value["gt"])
                        if filter_f is not None and meta_f <= filter_f:
                            return False
                    if "lt" in value:
                        filter_f = _to_float(value["lt"])
                        if filter_f is not None and meta_f >= filter_f:
                            return False

        return True
