import json
import logging
from collections import deque
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.config import settings
from app.models.crawl_task_message import CrawlTaskMessage
from app.models.ml_task_message import MlTaskMessage, ArticleBlockMessage
from app.publisher.ml_task_publisher import MlTaskPublisher
from app.services.article_claim_client import ArticleClaimClient
from app.services.crawlers.crawler_factory import CrawlerFactory

logger = logging.getLogger(__name__)


class CrawlTaskConsumer:
    """
    Consumes CrawlTaskMessage from queue 'crawl.task' (published by SchedulerService).
    For each message:
      1. Selects crawler by sourceId
      2. Crawls articles from that source
            3. Canonicalizes URL and checks duplicate (local cache + ArticleService claim)
            4. Publishes only new articles to queue 'ml.tasks' via MlTaskPublisher
    """

    def __init__(self, publisher: MlTaskPublisher):
        self._publisher = publisher
        self._claim_client = ArticleClaimClient.from_settings()
        self._recent_urls: set[str] = set()
        self._recent_url_order: deque[str] = deque()

    @staticmethod
    def _canonicalize_url(value: str | None) -> str:
        if not value:
            return ""

        trimmed = value.strip()
        if not trimmed:
            return ""

        try:
            parsed = urlparse(trimmed)
            scheme = (parsed.scheme or "https").lower()
            netloc = (parsed.netloc or "").lower()

            path = parsed.path or "/"
            if path != "/":
                path = path.rstrip("/") or "/"

            tracking_param_keys = {
                "fbclid",
                "gclid",
                "igshid",
                "mc_cid",
                "mc_eid",
                "spm",
            }
            query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
            filtered_pairs = [
                (key, val)
                for key, val in query_pairs
                if not key.lower().startswith("utm_")
                and key.lower() not in tracking_param_keys
            ]
            query = urlencode(filtered_pairs, doseq=True)

            return urlunparse((scheme, netloc, path, "", query, ""))
        except Exception:
            return trimmed

    def _is_recent_duplicate(self, canonical_url: str) -> bool:
        max_cache_size = max(settings.local_recent_url_cache_size, 0)
        if max_cache_size == 0:
            return False

        if canonical_url in self._recent_urls:
            return True

        self._recent_urls.add(canonical_url)
        self._recent_url_order.append(canonical_url)

        while len(self._recent_url_order) > max_cache_size:
            old_url = self._recent_url_order.popleft()
            self._recent_urls.discard(old_url)

        return False

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split()).strip().lower()

    def _build_blocks_and_content(self, raw_blocks, sapo: str | None):
        normalized_sapo = self._normalize_text(sapo) if sapo else ""
        seen_paragraphs = set()
        blocks: list[ArticleBlockMessage] = []
        paragraph_texts: list[str] = []

        for block in raw_blocks:
            block_content = (block.content or "").strip()
            block_text = (block.text or "").strip()

            if block.type == "paragraph":
                paragraph_text = block_text or block_content
                normalized_paragraph = self._normalize_text(paragraph_text)

                if not normalized_paragraph:
                    continue
                if normalized_sapo and normalized_paragraph == normalized_sapo:
                    continue
                if normalized_paragraph in seen_paragraphs:
                    continue

                seen_paragraphs.add(normalized_paragraph)
                paragraph_texts.append(paragraph_text)

                if not block_content:
                    block_content = paragraph_text
                if not block_text:
                    block_text = paragraph_text

            blocks.append(
                ArticleBlockMessage(
                    order=block.order,
                    type=block.type,
                    content=block_content,
                    text=block_text,
                    tag=block.tag,
                    src=block.src,
                    alt=block.alt,
                    caption=block.caption,
                )
            )

        return blocks, " ".join(paragraph_texts).strip()

    async def handle_message(self, message: Any) -> None:
        """Process a single crawl.task message (called by aio-pika listener)."""
        # We manually reject on errors to avoid bubbling exceptions into aio-pika
        # callback scheduler (which can log noisy "Task exception was never retrieved").
        async with message.process(requeue=False, ignore_processed=True):
            try:
                body = json.loads(message.body.decode("utf-8"))
                task = CrawlTaskMessage(**body)
                logger.info(
                    "Received crawl task: source=%s url=%s",
                    task.sourceId,
                    task.baseUrl,
                )
                await self._crawl_and_publish(task)
            except Exception:
                logger.exception("Error processing crawl task message")
                await message.reject(requeue=False)

    async def _crawl_and_publish(self, task: CrawlTaskMessage) -> None:
        """Run crawler for the source and publish results to ml.tasks."""
        source_id = task.sourceId.lower()

        crawler = CrawlerFactory.create_crawler(source_id)

        try:
            async with crawler:
                results = await crawler.crawl_multiple_articles(
                    max_articles=settings.max_articles_per_source
                )
        except Exception:
            logger.exception("Error crawling source '%s'", source_id)
            raise

        logger.info(
            "Crawled %d articles from %s — publishing to ml.tasks",
            len(results),
            source_id,
        )

        for result in results:
            if not result.success:
                logger.warning(
                    "Skip failed article: url=%s error=%s",
                    result.url,
                    result.error_message,
                )
                continue

            canonical_url = self._canonicalize_url(result.url)
            if not canonical_url:
                logger.warning(
                    "Skip article with invalid URL after canonicalization: source=%s raw_url=%s",
                    source_id,
                    result.url,
                )
                continue

            if self._is_recent_duplicate(canonical_url):
                logger.info(
                    "Skip recent duplicate before claim: source=%s url=%s",
                    source_id,
                    canonical_url,
                )
                continue

            claim_decision = await self._claim_client.claim(
                source_id=source_id,
                source_name=task.sourceName,
                title=result.title,
                url=canonical_url,
            )
            if not claim_decision.should_publish:
                logger.info(
                    "Skip duplicate before ml.tasks: source=%s url=%s reason=%s",
                    source_id,
                    canonical_url,
                    claim_decision.reason,
                )
                continue

            message_blocks, article_content = self._build_blocks_and_content(
                result.blocks,
                result.sapo,
            )

            if not article_content:
                logger.warning(
                    "Skip article with empty body after normalization: source=%s url=%s",
                    source_id,
                    result.url,
                )
                continue

            ml_message = MlTaskMessage(
                sourceId=source_id,
                sourceName=task.sourceName,
                title=result.title,
                topImage=result.top_image,
                url=claim_decision.canonical_url,
                publishedAt=str(result.published_at) if result.published_at else None,
                sapo=result.sapo,
                content=article_content,
                blocks=message_blocks,
            )
            await self._publisher.publish(ml_message)
