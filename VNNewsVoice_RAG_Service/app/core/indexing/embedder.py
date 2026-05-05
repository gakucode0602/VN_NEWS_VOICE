import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from fastembed import SparseTextEmbedding
from app.config.settings import get_settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseEmbedder(ABC):
    """Abstract base class for embedding generation."""

    @abstractmethod
    def embed(self, texts: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors, one per input text
        """
        pass

    @abstractmethod
    def embed_single(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector for the input text
        """
        pass


class LocalSentenceTransformerEmbedder(BaseEmbedder):
    """Embedder using local sentence-transformers model."""

    def __init__(
        self,
        dense_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        sparse_model_name: str = "Qdrant/bm25",
    ):
        """
        Initialize the sentence-transformers embedder.

        Args:
            model_name: Name of the sentence-transformers model to use
        """

        try:
            logger.info(f"Loading dense model {dense_model_name}")
            logger.info(f"Loading sparse model {sparse_model_name}")
            self.dense_model = SentenceTransformer(
                settings.dense_local_embed_model_name
            ) or SentenceTransformer(dense_model_name)
            self.sparse_model = SparseTextEmbedding(
                model_name=settings.sparse_local_embed_model_name
            )
            logger.info(f"Successfully loaded dense model {dense_model_name}")
            logger.info(f"Successfully loaded sparse model {sparse_model_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def embed(self, texts: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors, one per input text
        """

        # Generate dense vectors
        dense_vectors = self.dense_model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True
        )

        # Generate spaese vectors
        sparse_generators = self.sparse_model.embed(documents=texts)

        sparse_vectors = []
        for v in sparse_generators:
            sparse_vectors.append(
                {"indices": v.indices.tolist(), "values": v.values.tolist()}
            )

        return [
            {"dense": dense, "sparse": sparse}
            for dense, sparse in zip(dense_vectors, sparse_vectors)
        ]

    def embed_single(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector for the input text
        """

        return self.embed([text])[0]
