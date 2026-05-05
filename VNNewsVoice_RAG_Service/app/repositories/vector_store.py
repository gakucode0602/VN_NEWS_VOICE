import logging
from typing import Any, Dict, List, Optional


from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    Range,
    VectorParams,
)
from qdrant_client.conversions.common_types import QueryResponse, SparseVectorParams
from app.models.domain.article import DocumentChunk
from app.models.domain.retrieval import RetrievalResult
from app.config.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Repository for vector database operations using Qdrant."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "vnnv_vector_db",
        api_key: Optional[str] = None,
    ):
        """
        Initialize Qdrant client and ensure collection exists.

        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Name of the collection to use
            api_key: Optional API key for Qdrant authentication
        """
        self.client = QdrantClient(
            host=host, port=port, api_key=api_key or None, https=False
        )
        self.collection_name = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        """
        Create collection if it doesn't exist.
        Uses vector size 384 for sentence-transformers/all-MiniLM-L6-v2 model.
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]

        if self.collection_name not in collection_names:
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "text": VectorParams(
                        size=settings.embedding_dimension,  # Dimension for all-MiniLM-L6-v2
                        distance=Distance.COSINE,
                    )
                },
                sparse_vectors_config={"sparse": SparseVectorParams()},
            )
            logger.info(f"Created collection: {self.collection_name}")
        else:
            logger.info(f"Collection already exists: {self.collection_name}")

    def upsert_chunks(
        self, chunks: List[DocumentChunk], embeddings: List[Dict[str, Any]]
    ) -> int:
        """
        Upsert document chunks with their embeddings into vector store.

        Args:
            chunks: List of DocumentChunk objects
            embeddings: List of embedding vectors (one per chunk)

        Returns:
            Number of chunks upserted
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
            )
        try:
            points = [
                PointStruct(
                    id=c.chunk_id,
                    vector={
                        "text": e["dense"],
                        "sparse": models.SparseVector(
                            indices=e["sparse"]["indices"], values=e["sparse"]["values"]
                        ),
                    },
                    payload={
                        "article_id": c.article_id,
                        "content": c.content,
                        "chunk_index": c.chunk_index,
                        **c.metadata,
                    },
                )
                for c, e in zip(chunks, embeddings)
            ]

            self.client.upsert(
                collection_name=self.collection_name, wait=True, points=points
            )

            return len(embeddings)
        except Exception as e:
            logger.error(f"Error when adding embedings: {e}")
            raise

    def search(
        self,
        query_embedding: Dict[str, Any],
        top_k: int,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        try:
            query_filters = None
            if metadata_filters is not None:
                query_filters = self._build_filters(metadata_filters)

            dense_query = query_embedding["dense"]

            sparse_query = models.SparseVector(
                indices=query_embedding["sparse"]["indices"],
                values=query_embedding["sparse"]["values"],
            )

            search_results = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    models.Prefetch(
                        query=dense_query,
                        using="text",
                        limit=top_k * 2,
                        filter=query_filters,
                    ),
                    models.Prefetch(
                        query=sparse_query,
                        using="sparse",
                        limit=top_k * 2,
                        filter=query_filters,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
            )
            retrieval_results = self._build_list_retrieval_result(search_results)

            if len(retrieval_results) == 0 and query_filters is not None:
                # Do NOT fall back to unfiltered search — that would return chunks from
                # unrelated articles and produce wrong/misleading LLM answers.
                # 0 results means the article is not indexed; surface that correctly.
                logger.warning(
                    "Filtered search returned 0 results. Article may not be indexed yet. Returning empty."
                )

            return retrieval_results
        except Exception as e:
            logger.error(f"Error when searching: {e}")
            raise

    def _build_filters(self, filters: Dict[str, Any]) -> Optional[Filter]:
        conditions = []
        for k, v in filters.items():
            if isinstance(v, str) or isinstance(v, int):
                conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
            elif isinstance(v, dict):
                range_params = {}
                if "gte" in v:
                    range_params["gte"] = v["gte"]
                if "lte" in v:
                    range_params["lte"] = v["lte"]
                if "gt" in v:
                    range_params["gt"] = v["gt"]
                if "lt" in v:
                    range_params["lt"] = v["lt"]

                if range_params:
                    conditions.append(
                        FieldCondition(key=k, range=Range(**range_params))
                    )
        return Filter(must=conditions) if conditions else None

    def get_all(self) -> List[DocumentChunk]:
        """
        Get all chunk from vector database (FOR SPARSE Retriever)

        Will implement an event to callback new data after update later
        """
        record_count = self.client.count(collection_name=self.collection_name)

        record = self.client.scroll(
            collection_name=self.collection_name, limit=record_count.count
        )

        points = record[0]

        list_document = []

        for point in points:
            chunk_id = point.id
            article_id = point.payload["article_id"]
            content = point.payload["content"]
            chunk_index = point.payload["chunk_index"]
            metadata = {
                k: v
                for k, v in point.payload.items()
                if k not in ["article_id", "content", "chunk_index"]
            }

            list_document.append(
                DocumentChunk(
                    chunk_id=str(chunk_id),
                    article_id=article_id,
                    content=content,
                    chunk_index=chunk_index,
                    metadata=metadata,
                )
            )

        logger.info(f"Retrieved {len(list_document)} chunks from vector store")
        return list_document

    def _build_list_retrieval_result(
        self, query_response: QueryResponse
    ) -> List[RetrievalResult]:
        retrieval_results = []
        for rank, result in enumerate(query_response.points, start=1):
            chunk_id = str(result.id)
            article_id = result.payload["article_id"]
            content = result.payload["content"]
            chunk_index = result.payload["chunk_index"]
            metadata = {
                k: v
                for k, v in result.payload.items()
                if k not in ["article_id", "content", "chunk_index"]
            }
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                article_id=article_id,
                content=content,
                chunk_index=chunk_index,
                metadata=metadata,
            )

            retrieval_results.append(
                RetrievalResult(chunk=chunk, score=result.score, rank=rank)
            )
        return retrieval_results

    def delete_by_article_id(self, article_id: str) -> bool:
        """
        Delete all chunks belonging to a specific article.

        Args:
            article_id: ID of the article to delete

        Returns:
            Number of chunks deleted
        """
        try:
            delete_filter = Filter(
                must=[
                    FieldCondition(key="article_id", match=MatchValue(value=article_id))
                ]
            )

            delete_result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(filter=delete_filter),
            )

            return delete_result.status == "ok"
        except Exception as e:
            logger.error(f"Error deleting chunks for article {article_id}: {e}")
            raise
