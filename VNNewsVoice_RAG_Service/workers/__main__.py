import logging
import asyncio
import threading
from app.config.settings import get_settings
from app.api.deps import get_embedder, get_vector_store
from app.core.indexing.chunker import Chunker
from app.services.message_consumer import MessageConsumer
from workers.indexing_workers import IndexingWorker


logger = logging.getLogger(__name__)


def _start_background_loop(loop: asyncio.AbstractEventLoop):
    """Chạy event loop mãi mãi trong background thread.
    Loop này dùng cho asyncpg — không bao giờ đóng nên connection pool không crash.
    """
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main():
    try:
        settings = get_settings()  # Also sets up logging
        logger.info("=== RAG Indexing Worker Starting ===")

        # Tạo persistent event loop trong background thread
        # Pika consumer chạy blocking trong main thread — cần loop riêng cho async DB ops
        async_loop = asyncio.new_event_loop()
        loop_thread = threading.Thread(
            target=_start_background_loop,
            args=(async_loop,),
            daemon=True,  # tự dừng khi main thread kết thúc
            name="AsyncPGLoop",
        )
        loop_thread.start()
        logger.info("Background async event loop started (thread: AsyncPGLoop)")

        embedder = get_embedder()

        vector_store = get_vector_store()

        chunker = Chunker()

        worker = IndexingWorker(
            chunker=chunker,
            embedder=embedder,
            vector_store=vector_store,
            parent_chunk_repository=None,  # _flush_to_postgres() tự tạo session riêng
            async_loop=async_loop,  # persistent loop cho pika sync callbacks
        )

        consumer = MessageConsumer(settings.rabbitmq_url, worker=worker)
        logger.info("Consumer initialized successfully")
        logger.info("Starting message consumption... (Press Ctrl+C to stop)")

        # Start — blocking
        consumer.start_consuming()
    except Exception as e:
        logger.error(f"Error when initialize consumer: {e}")
        raise


if __name__ == "__main__":
    main()
