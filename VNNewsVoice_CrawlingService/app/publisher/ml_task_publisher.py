import asyncio
import logging
import random

import aio_pika
from aio_pika import Channel

from app.config import settings
from app.models.ml_task_message import MlTaskMessage

logger = logging.getLogger(__name__)


class MlTaskPublisher:
    """
    Publishes crawled articles to queue 'ml.tasks'.
    ML Service (Phase 1.3) is the consumer.
    """

    def __init__(self, channel: Channel):
        self._channel = channel

    async def publish(self, message: MlTaskMessage) -> None:
        """Publish a single crawled article to ml.tasks with retry/backoff."""
        body = message.model_dump_json().encode("utf-8")
        max_attempts = max(1, settings.ml_publish_max_retries)
        base_delay = max(0.0, settings.ml_publish_backoff_initial_seconds)
        max_delay = max(base_delay, settings.ml_publish_backoff_max_seconds)
        jitter = max(0.0, settings.ml_publish_jitter_seconds)

        for attempt in range(1, max_attempts + 1):
            try:
                await self._channel.default_exchange.publish(
                    aio_pika.Message(
                        body=body,
                        content_type="application/json",
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key=settings.ml_tasks_queue,
                )
                logger.info(
                    "Published to ml.tasks: source=%s title=%s...",
                    message.sourceId,
                    message.title[:60],
                )
                return
            except Exception as exc:
                if attempt >= max_attempts:
                    logger.exception(
                        "Publish to ml.tasks failed after %d attempts: source=%s url=%s",
                        max_attempts,
                        message.sourceId,
                        message.url,
                    )
                    raise

                delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                if jitter > 0:
                    delay += random.uniform(0.0, jitter)

                logger.warning(
                    "Publish failed (attempt %d/%d), retry in %.2fs: %s",
                    attempt,
                    max_attempts,
                    delay,
                    str(exc),
                )
                await asyncio.sleep(delay)

    @classmethod
    async def declare_queue(cls, channel: Channel) -> None:
        """Declare ml.tasks queue (idempotent — safe to call on startup)."""
        await channel.declare_queue(settings.ml_tasks_queue, durable=True)
