from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.indexing.embedder import BaseEmbedder
from app.models.domain.retrieval import RetrievalResult
from app.repositories.vector_store import QdrantVectorStore


class BaseRetrieval(ABC):
    def __init__(self, embedder: BaseEmbedder, vector_store: QdrantVectorStore) -> None:
        """
        Args:
            embedder: Embedding model for query encoding
            vector_store: Vector database for similarity search
        """

        self.embedder = embedder
        self.vector_store = vector_store

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query"""
        pass
