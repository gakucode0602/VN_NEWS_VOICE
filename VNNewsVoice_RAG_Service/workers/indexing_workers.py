import asyncio
from datetime import datetime
import logging
from typing import List, Optional
from app.core.indexing.chunker import Chunker
from app.core.indexing.embedder import LocalSentenceTransformerEmbedder
from app.models.domain.article import Article
from app.models.db.parent_chunk import ParentChunk
from app.repositories.vector_store import QdrantVectorStore
from app.repositories.parent_chunk_repository import ParentChunkRepository

logger = logging.getLogger(__name__)


class IndexingWorker:
    def __init__(
        self,
        chunker: Chunker,
        embedder: LocalSentenceTransformerEmbedder,
        vector_store: QdrantVectorStore,
        parent_chunk_repository: ParentChunkRepository,
        async_loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.parent_chunk_repository = parent_chunk_repository
        # Loop dùng cho pika sync context — phải là loop đang chạy liên tục
        # (không phải loop do asyncio.run() tạo, vì nó tự đóng sau mỗi call)
        self._async_loop = async_loop

    def index_article(self, article_data: dict) -> int:
        try:
            # Handle both formats before logging
            data = article_data.get("result", article_data)
            article_title = data.get("article", {}).get("title", "unknown")
            logger.info(
                f"Upserting article with title '{article_title}' to vector store"
            )
            # Convert data to Article domain
            article = self._convert_dict_to_article(article_data)

            # Chunk the data
            chunk_results = self.chunker.chunk_hierarchical(article)

            child_chunks = chunk_results[1]
            parent_chunks_list = chunk_results[0]

            # Guard: bài không có content/blocks → 0 chunks → Qdrant 400 "Empty update request"
            if not child_chunks:
                logger.warning(
                    f"Article '{article_title}' produced 0 chunks (no content). Skipping."
                )
                return 0

            chunk_results_content = [c.content for c in child_chunks]

            # Create embeddings
            embedding_results = self.embedder.embed(texts=chunk_results_content)

            # Upsert to Qdrant
            upsert_result = self.vector_store.upsert_chunks(
                chunks=child_chunks, embeddings=embedding_results
            )
            logger.info("Successfully upsert new article to vector store")

            # Flush parent chunks to Postgres
            pg_chunks = [
                ParentChunk(
                    id=chunk.chunk_id,
                    article_id=chunk.article_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                )
                for chunk in parent_chunks_list
            ]

            self._schedule_pg_flush(pg_chunks)

            return upsert_result
        except Exception as e:
            logger.error(f"Error when indexing the article: {e}")
            raise

    def _schedule_pg_flush(self, pg_chunks: list):
        """
        Schedule _flush_to_postgres theo context:
        - FastAPI async context: create_task() (non-blocking)
        - Pika sync context: run_coroutine_threadsafe() vào persistent loop (blocking đợi done)

        KHÔNG dùng asyncio.run() vì nó tạo loop mới rồi ĐÓNG lại — asyncpg pool
        references loop đã đóng → 'Event loop is closed' crash.
        """
        try:
            # Đang trong async context (FastAPI) — running loop tồn tại trong thread này
            asyncio.get_running_loop()
            asyncio.create_task(self._flush_to_postgres(pg_chunks))
        except RuntimeError:
            # Pika sync context — không có running loop trong thread này
            if self._async_loop and self._async_loop.is_running():
                # Dùng persistent loop từ background thread
                future = asyncio.run_coroutine_threadsafe(
                    self._flush_to_postgres(pg_chunks), self._async_loop
                )
                try:
                    future.result(timeout=30)  # chờ done, max 30s
                except Exception as e:
                    logger.error(f"[PG flush] run_coroutine_threadsafe failed: {e}")
            else:
                logger.warning(
                    "[PG flush] No async loop available. Skipping postgres flush."
                )

    def delete_article(self, article_id: str):
        try:
            if not article_id:
                logger.warning("Delete requested without article_id. Skipping.")
                return

            logger.info(f"Deleting article {article_id} from vector store")
            self.vector_store.delete_by_article_id(article_id)
            self._schedule_pg_delete(article_id)
            logger.info(f"Successfully deleted article {article_id}")
        except Exception as e:
            logger.error(f"Error when deleting article {article_id}: {e}")
            raise

    def _schedule_pg_delete(self, article_id: str):
        """
        Schedule parent chunk deletion using the same async strategy as PG flush.
        """
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self._delete_parent_chunks(article_id))
        except RuntimeError:
            if self._async_loop and self._async_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self._delete_parent_chunks(article_id), self._async_loop
                )
                try:
                    future.result(timeout=30)
                except Exception as e:
                    logger.error(f"[PG delete] run_coroutine_threadsafe failed: {e}")
                    raise
            else:
                logger.warning(
                    "[PG delete] No async loop available. Skipping parent chunk deletion."
                )

    def _convert_dict_to_article(self, message: dict) -> Article:
        # Auto-detect message format:
        # Format 1 (direct):  { "article": {...}, "blocks": [...] }
        # Format 2 (wrapped): { "result": { "article": {...}, "blocks": [...] } }
        if "result" in message:
            message = message["result"]

        article = message["article"]
        blocks = message["blocks"]

        # Bug fix 1: backend uses "id" not "article_id"
        article_id = str(article["id"])
        title = article["title"]

        # Bug fix 2: use fromisoformat() to handle ISO 8601 with timezone
        # Format: "2025-09-07T17:15:20.909+00:00"
        published_at = datetime.fromisoformat(article["publishedDate"])

        source = article["generatorIdName"]
        url = article["originalUrl"]
        topic = article["categoryIdName"]

        content = ""

        # Bug fix 3: blocks is at top level, not inside article
        # Bug fix 4: paragraph uses "content", heading uses "text"
        for b in blocks:
            if b["type"] == "paragraph" and b.get("content"):
                content += b["content"] + " "
            elif b["type"] == "heading" and b.get("text"):
                content += b["text"] + " "

        content = " ".join(content.strip().split())

        return Article(
            article_id=article_id,
            title=title,
            content=content,
            published_at=published_at,
            source=source,
            url=url,
            topic=topic,
        )

    async def _flush_to_postgres(self, parent_chunks: List[ParentChunk]) -> None:
        from app.config.database import AsyncSessionLocal
        from app.repositories.parent_chunk_repository import ParentChunkRepository

        try:
            async with AsyncSessionLocal() as session:
                repo = ParentChunkRepository(session)
                await repo.save_all(parent_chunks)

        except Exception as e:
            logger.error(f"[PG flush] Failed to persist parent chunk {e}")

    async def _delete_parent_chunks(self, article_id: str) -> None:
        from app.config.database import AsyncSessionLocal
        from app.repositories.parent_chunk_repository import ParentChunkRepository

        try:
            async with AsyncSessionLocal() as session:
                repo = ParentChunkRepository(session)
                await repo.delete_by_article_id(article_id)
                logger.info(
                    "[PG delete] Deleted parent chunks for article %s", article_id
                )
        except Exception as e:
            logger.error(
                "[PG delete] Failed to delete parent chunks for article %s: %s",
                article_id,
                e,
            )
            raise
