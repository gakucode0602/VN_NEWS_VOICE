import logging
from typing import Any, Dict, List, Optional

from app.core.rag.retrieval.base import BaseRetrieval
from app.core.rag.retrieval.dense_retriever import DenseRetriever
from app.core.rag.retrieval.sparse_retriever import SparseRetriever
from app.models.domain.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


@DeprecationWarning
class HybridRetriever(BaseRetrieval):
    """Hybrid retriever combining dense + sparse"""

    def __init__(self, embedder, vector_store):
        """Initialize hybrid retriever with fallback to dense-only."""
        super().__init__(embedder, vector_store)
        # Create internal dense retriever for fallback
        self._dense = DenseRetriever(embedder, vector_store)
        self._sparse = SparseRetriever(embedder, vector_store)
        logger.info("Initilized Hybrid retriever!!!")

    def retrieve(
        self, query: str, top_k: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve using hybrid approach (dense + sparse).
        """
        # Retrieve from both retriever
        dense_results = self._dense.retrieve(
            query=query, top_k=2 * top_k, filters=filters
        )
        sparse_results = self._sparse.retrieve(
            query=query, top_k=2 * top_k, filters=filters
        )

        # Fuse:
        fused_lists = self._reciprocal_rank_fusion(dense_results, sparse_results)

        # Normalized list
        normalized_list = self._normalize_scores(fused_lists)

        # Top_k
        return normalized_list[:top_k]

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[RetrievalResult],
        sparse_results: List[RetrievalResult],
        k: int = 60,
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion (RRF).

        Formula: RRF_score(chunk) = Σ [ 1 / (k + rank) ]
        where rank comes from each retriever that contains the chunk.

        Args:
            dense_results: Results from dense retriever
            sparse_results: Results from sparse retriever
            k: RRF constant (default 60, standard value)

        Returns:
            List of RetrievalResult sorted by RRF score descending
        """
        # Build chunk_map: chunk_id -> {chunk, dense_rank, sparse_rank}
        chunk_map = {}

        # Add dense results
        for result in dense_results:
            chunk_id = result.chunk.chunk_id
            chunk_map[chunk_id] = {
                "chunk": result.chunk,
                "dense_rank": result.rank,
                "sparse_rank": None,
            }

        # Add sparse results (update if exists, create if new)
        for result in sparse_results:
            chunk_id = result.chunk.chunk_id
            if chunk_id in chunk_map:
                # Chunk exists in dense, update sparse_rank
                chunk_map[chunk_id]["sparse_rank"] = result.rank
            else:
                # Chunk only in sparse
                chunk_map[chunk_id] = {
                    "chunk": result.chunk,
                    "dense_rank": None,
                    "sparse_rank": result.rank,
                }

        # Calculate RRF score for each chunk
        rrf_results = []
        for chunk_id, data in chunk_map.items():
            rrf_score = 0.0

            # Add dense contribution if present
            if data["dense_rank"] is not None:
                rrf_score += 1.0 / (k + data["dense_rank"])

            # Add sparse contribution if present
            if data["sparse_rank"] is not None:
                rrf_score += 1.0 / (k + data["sparse_rank"])

            rrf_results.append({"chunk": data["chunk"], "rrf_score": rrf_score})

        # Sort by RRF score descending
        rrf_results.sort(key=lambda x: x["rrf_score"], reverse=True)

        # Build final RetrievalResult list with updated ranks
        final_results = []
        for rank, item in enumerate(rrf_results, start=1):
            final_results.append(
                RetrievalResult(chunk=item["chunk"], score=item["rrf_score"], rank=rank)
            )

        logger.info(
            f"RRF fusion: {len(dense_results)} dense + {len(sparse_results)} sparse "
            f"-> {len(final_results)} unique chunks"
        )

        return final_results

    def _normalize_scores(
        self, results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Min-max normalization: (score - min) / (max - min)
        Maps scores to [0, 1] range.

        Args:
            results: List of RetrievalResult with raw scores

        Returns:
            New list with normalized scores (immutable)
        """
        if not results:
            return []

        scores = [r.score for r in results]
        min_score = min(scores)
        max_score = max(scores)

        # Edge case: all scores same -> set all to 1.0 (all equally good)
        if max_score == min_score:
            return [
                RetrievalResult(chunk=r.chunk, score=1.0, rank=r.rank) for r in results
            ]

        # Normalize scores and create new RetrievalResult objects
        normalized_results = []
        for r in results:
            normalized_score = (r.score - min_score) / (max_score - min_score)
            normalized_results.append(
                RetrievalResult(chunk=r.chunk, score=normalized_score, rank=r.rank)
            )

        return normalized_results
