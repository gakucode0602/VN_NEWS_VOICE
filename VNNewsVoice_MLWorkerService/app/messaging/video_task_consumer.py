"""
app/messaging/video_task_consumer.py

Consumes from queue 'ml.video.tasks', generates video via Veo API,
then publishes 'video.generated' event back to fanout exchange 'article.events'.

Flow:
  1. Receive VideoGenerationMessage from ArticleService
  2. Call VideoGenerationService.generate_and_upload() in thread pool (1-3 min)
  3. On success: publish ArticleEventMessage(eventType="video.generated", videoUrl=...)
  4. ArticleService listener saves videoUrl to article DB automatically
"""

import asyncio
import json
import logging
from typing import Optional

from aio_pika import IncomingMessage

from app.messaging.schemas import ArticleEventMessage, VideoGenerationMessage
from app.messaging.publisher import ArticleEventsPublisher

logger = logging.getLogger(__name__)


class VideoTaskConsumer:
    def __init__(self, publisher: ArticleEventsPublisher):
        self._publisher = publisher

    async def handle_message(self, message: IncomingMessage) -> None:
        """Process one ml.video.tasks message from ArticleService."""
        async with message.process():  # auto-ack on success, nack on exception
            try:
                body = json.loads(message.body.decode("utf-8"))
                task = VideoGenerationMessage(**body)
                logger.info(
                    "[VideoTask] Received: articleId=%s title=%s...",
                    task.articleId,
                    task.title[:60],
                )
                await self._process(task)
            except Exception:
                logger.exception("[VideoTask] Error processing ml.video.tasks message")
                raise  # triggers nack → requeue

    async def _process(self, task: VideoGenerationMessage) -> None:
        """Run Veo generation in thread pool (blocking ~1-3 min), then publish result."""
        from app.services.video_generation_service import VideoGenerationService

        result: Optional[dict] = await asyncio.get_event_loop().run_in_executor(
            None,
            VideoGenerationService.generate_and_upload,
            task.articleId,
            task.title,
            task.topImageUrl,
            task.summary,
            None,  # model — use default from config
            task.durationSeconds,
            task.videoStyle,
        )

        if not result or not result.get("video_url"):
            logger.error(
                "[VideoTask] Video generation failed or returned no URL for articleId=%s",
                task.articleId,
            )
            # Do NOT raise — we ack the message so it doesn't loop infinitely
            # (Veo failures are usually billing/quota, not transient errors)
            return

        video_url: str = result["video_url"]
        logger.info(
            "[VideoTask] Video generated: articleId=%s url=%s",
            task.articleId,
            video_url,
        )

        event = ArticleEventMessage(
            articleId=task.articleId,
            title=task.title,
            videoUrl=video_url,
            eventType="video.generated",
        )
        await self._publisher.publish(event.model_dump_json())
        logger.info(
            "[VideoTask] Published video.generated event: articleId=%s",
            task.articleId,
        )
