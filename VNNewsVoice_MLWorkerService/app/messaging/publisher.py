"""
app/messaging/publisher.py
Publishes ArticleEventMessage to fanout exchange 'article.events'.
Consumers:
  - Phase 1.4: RAG Service queue (article.events.rag-service)
  - Phase 1.5: ArticleService queue (article.events.article-service)
"""

import logging
from typing import Optional

import aio_pika
from aio_pika import Channel

from app.core.config import settings

logger = logging.getLogger(__name__)


class ArticleEventsPublisher:
    def __init__(self, channel: Channel):
        self._channel = channel
        self._exchange: Optional[aio_pika.Exchange] = None

    async def _get_exchange(self) -> aio_pika.Exchange:
        if self._exchange is None:
            self._exchange = await self._channel.declare_exchange(
                settings.ARTICLE_EVENTS_EXCHANGE,
                aio_pika.ExchangeType.FANOUT,
                durable=True,
            )
        return self._exchange

    async def publish(self, event_json: str) -> None:
        """Publish serialized ArticleEventMessage to the fanout exchange."""
        exchange = await self._get_exchange()
        await exchange.publish(
            aio_pika.Message(
                body=event_json.encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key="",  # fanout ignores routing key
        )
        logger.info("Published article.events fanout message")

    @classmethod
    async def declare_infrastructure(cls, channel: Channel) -> None:
        """Declare exchange + downstream queues (idempotent — call on startup)."""
        exchange = await channel.declare_exchange(
            settings.ARTICLE_EVENTS_EXCHANGE,
            aio_pika.ExchangeType.FANOUT,
            durable=True,
        )

        rag_queue_name = f"{settings.ARTICLE_EVENTS_EXCHANGE}.rag-service"
        article_queue_name = f"{settings.ARTICLE_EVENTS_EXCHANGE}.article-service"

        # Pre-declare consumer queues so messages are not lost before consumers start
        rag_queue = await channel.declare_queue(rag_queue_name, durable=True)
        article_queue = await channel.declare_queue(article_queue_name, durable=True)

        await rag_queue.bind(exchange)
        await article_queue.bind(exchange)

        # Declare ml.video.tasks so it exists before ArticleService publishes to it
        await channel.declare_queue(settings.ML_VIDEO_TASKS_QUEUE, durable=True)

        logger.info(
            "Declared fanout exchange '%s' + 2 bound queues + '%s'",
            settings.ARTICLE_EVENTS_EXCHANGE,
            settings.ML_VIDEO_TASKS_QUEUE,
        )
