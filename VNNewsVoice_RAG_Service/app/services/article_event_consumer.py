"""
app/services/article_event_consumer.py

Async aio-pika consumer for queue 'article.events.rag-service'.
This queue is bound to fanout exchange 'article.events' (declared by MLService).

Replaces the blocking pika MessageConsumer for the fanout path.
The original MessageConsumer (article.created/updated/deleted) is KEPT for
backward compatibility with the old Backend REST-push workflow.
"""

import asyncio
import json
import logging
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage

logger = logging.getLogger(__name__)

FANOUT_QUEUE_NAME = "article.events.rag-service"
ARTICLE_EVENTS_EXCHANGE = "article.events"


class ArticleEventConsumer:
    """
    Consumes ArticleEventMessage from the fanout exchange queue.
    Converts the new flat format to the format expected by IndexingWorker.
    """

    def __init__(self, indexing_worker) -> None:
        self._worker = indexing_worker

    async def handle_message(self, message: IncomingMessage) -> None:
        """Process one article.events.rag-service message."""
        async with message.process():  # auto-ack / nack
            try:
                body = json.loads(message.body.decode("utf-8"))
                event_type = body.get("eventType")
                article_id = self._extract_article_id(body)
                logger.info(
                    "[RAG consumer] Received article.events: type=%s id=%s source=%s",
                    event_type,
                    article_id or "?",
                    body.get("sourceId", "?"),
                )

                if not article_id:
                    logger.warning("[RAG consumer] Skip message without articleId")
                    return

                # IndexingWorker methods are synchronous (CPU-bound) — run in executor.
                loop = asyncio.get_event_loop()

                if self._should_delete(body):
                    await loop.run_in_executor(
                        None, self._worker.delete_article, article_id
                    )
                    logger.info("[RAG consumer] Deleted article id=%s", article_id)
                    return

                if self._should_reindex(body):
                    # For active updates, delete first to avoid stale leftover chunks.
                    if event_type == "article.updated":
                        await loop.run_in_executor(
                            None, self._worker.delete_article, article_id
                        )

                    adapted = self._adapt_to_worker_format(body)
                    await loop.run_in_executor(
                        None, self._worker.index_article, adapted
                    )
                    logger.info("[RAG consumer] Indexed article id=%s", article_id)
                    return

                logger.info(
                    "[RAG consumer] Skip unsupported lifecycle event: type=%s id=%s status=%s isActive=%s",
                    event_type,
                    article_id,
                    body.get("status"),
                    body.get("isActive"),
                )
            except json.JSONDecodeError as e:
                logger.error("[RAG consumer] Invalid JSON: %s", e)
                raise  # nack, no requeue
            except Exception:
                logger.exception("[RAG consumer] Failed to process message")
                raise  # nack + requeue (temporary error)

    @staticmethod
    def _extract_article_id(event: dict) -> str:
        article_id = event.get("articleId") or event.get("id")
        return str(article_id) if article_id is not None else ""

    @staticmethod
    def _should_delete(event: dict) -> bool:
        event_type = (event.get("eventType") or "").lower()
        status = (event.get("status") or "").upper()

        if event_type in {"article.delete", "article.deleted"}:
            return True

        if event_type == "article.updated":
            return status == "DELETED"

        return False

    @staticmethod
    def _should_reindex(event: dict) -> bool:
        event_type = (event.get("eventType") or "").lower()

        if event_type == "article.created":
            return True

        if event_type == "article.updated":
            status = (event.get("status") or "").upper()
            is_active = event.get("isActive")
            return status == "PUBLISHED" and is_active is not False

        return False

    @staticmethod
    def _adapt_to_worker_format(event: dict) -> dict:
        """
        Convert flat ArticleEventMessage (from MLService) to the dict format
        expected by IndexingWorker._convert_dict_to_article().

        Old Backend format (IndexingWorker expects):
        {
            "article": {
                "id": "...",           ← articleId
                "title": "...",
                "publishedDate": "...",   ← publishedAt (ISO-8601)
                "generatorIdName": "...", ← sourceName
                "originalUrl": "...",     ← url
                "categoryIdName": "...",  ← default "Tin tức"
            },
            "blocks": [{"type": "paragraph", "content": "...", "text": "..."}, ...]
        }
        """
        published_at = event.get("publishedAt") or datetime.utcnow().isoformat()

        return {
            "article": {
                "id": event.get("articleId") or event.get("id", ""),
                "title": event.get("title", ""),
                "publishedDate": published_at,
                "generatorIdName": event.get("sourceName", event.get("sourceId", "")),
                "originalUrl": event.get("url", ""),
                "categoryIdName": "Tin tức",  # default — no category in pipeline yet
            },
            "blocks": event.get("blocks", []),
        }


async def start_fanout_consumer(
    rabbitmq_url: str,
    indexing_worker,
) -> aio_pika.RobustConnection:
    """
    Connect to RabbitMQ, bind queue to article.events fanout, start consuming.
    Returns the connection so caller can close it on shutdown.
    """
    logger.info("[RAG consumer] Connecting to RabbitMQ: %s", rabbitmq_url[:20] + "***")
    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    # Declare the fanout exchange (idempotent — MLService also declares it)
    exchange = await channel.declare_exchange(
        ARTICLE_EVENTS_EXCHANGE,
        aio_pika.ExchangeType.FANOUT,
        durable=True,
    )

    # Declare this service's dedicated queue and bind to fanout
    queue = await channel.declare_queue(FANOUT_QUEUE_NAME, durable=True)
    await queue.bind(exchange)

    consumer = ArticleEventConsumer(indexing_worker)
    await queue.consume(consumer.handle_message, no_ack=False)

    logger.info(
        "[RAG consumer] Ready — consuming '%s' (bound to '%s')",
        FANOUT_QUEUE_NAME,
        ARTICLE_EVENTS_EXCHANGE,
    )
    return connection
