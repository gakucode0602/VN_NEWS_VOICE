"""Dense retriever using vector similarity search."""

import logging
from typing import Any, Dict, List, Optional

from app.core.rag.retrieval.base import BaseRetrieval
from app.models.domain.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


@DeprecationWarning
class DenseRetriever(BaseRetrieval):
    """Retriever using dense vector embeddings."""

    # def __init__(self, embedder: BaseEmbedder, vector_store: QdrantVectorStore):
    #    """
    #   Initialize dense retriever.

    #   Args:
    #       embedder: Embedding model for query encoding
    #       vector_store: Vector database for similarity search
    #   """
    #   self.embedder = embedder
    #   self.vector_store = vector_store

    def retrieve(
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.

        Hints:
        - Use self.embedder.embed_single(query) to get query vector
        - Use self.vector_store.search(query_embedding, top_k, filters)
        - Return the list of RetrievalResult objects
        - Add logging for query and number of results
        - Handle exceptions gracefully
        """
        try:
            # Turn the query to embeddings
            logger.info(
                f"Retrieving top_{top_k} results for query: '{query[:100]}...' using dense retrive method"
            )
            embedded_result = self.embedder.embed_single(query)

            # Search the query
            logger.info("Searching query ...")
            search_result = self.vector_store.search(
                query_embedding=embedded_result, top_k=top_k, metadata_filters=filters
            )
            logger.info(f"Found {len(search_result)} results")

            if len(search_result) == 0:
                logger.warning(f"No results found for query: '{query}'")

            return search_result
        except Exception as e:
            logger.error(f"Error when retrieve document: {e}")
            raise

    def retrieve_with_scores(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve with minimum score threshold.

        Hints:
        - Call self.retrieve() first
        - Filter results where result.score >= score_threshold
        - Return filtered list
        """
        results = self.retrieve(query, top_k, filters)
        return [r for r in results if r.score >= score_threshold]
