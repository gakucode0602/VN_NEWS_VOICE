from abc import ABC, abstractmethod
from typing import List, Optional
import asyncio
from datetime import datetime
import aiohttp
from dataclasses import dataclass
import logging

from app.models.article import ArticleBlock, Article

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    title: str
    top_image: str
    url: str
    published_at: Optional[str]
    blocks: List[ArticleBlock]
    success: bool
    error_message: Optional[str] = None
    sapo: Optional[str] = None  # human-written lead paragraph — used as training label

    def to_article(self) -> Article:
        return Article(
            title=self.title,
            top_image=self.top_image,
            url=self.url,
            published_at=self.published_at,
            blocks=self.blocks,
        )


class BaseCrawler(ABC):
    def __init__(self, source_name: str, base_url: str, rate_limit: int = 3):
        self.source_name = source_name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)

        self.session = aiohttp.ClientSession(
            headers=headers, timeout=timeout, connector=connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return " ".join(text.split())

    def select_best_content_container(self, soup, selectors: List[str]):
        """Select the most article-like container instead of first selector match."""
        best_candidate = None
        best_score = -1
        fallback_candidate = None

        for selector in selectors:
            candidates = soup.select(selector)
            if not candidates:
                continue

            if fallback_candidate is None:
                fallback_candidate = candidates[0]

            for candidate in candidates:
                paragraph_texts = []
                for paragraph in candidate.find_all("p"):
                    normalized = self._normalize_whitespace(
                        paragraph.get_text(" ", strip=True)
                    )
                    if len(normalized) >= 40:
                        paragraph_texts.append(normalized)

                if not paragraph_texts:
                    continue

                unique_paragraphs = list(dict.fromkeys(paragraph_texts))
                text_score = sum(len(text) for text in unique_paragraphs[:12])
                score = (len(unique_paragraphs) * 200) + text_score

                if score > best_score:
                    best_score = score
                    best_candidate = candidate

            if best_score >= 3000:
                break

        return best_candidate or fallback_candidate

    @abstractmethod
    async def get_rss_feed_urls(
        self,
        max_articles: int = 5,
        custom_rss_url: Optional[str] = None,
        last_crawl_time: Optional[datetime] = None,
    ) -> List[tuple[str, str]]:
        """Fetch and return a list of RSS feed URLs for the news source."""
        pass

    @abstractmethod
    async def crawl_article(
        self, url: str, title_hint: Optional[str] = None
    ) -> CrawlResult:
        """Crawl a single article URL and return structured content."""
        pass

    async def crawl_multiple_articles(
        self,
        max_articles: int,
        custom_rss_url: Optional[str] = None,
        last_crawl_time: Optional[datetime] = None,
    ) -> List[CrawlResult]:
        try:
            data = await self.get_rss_feed_urls(
                max_articles=max_articles,
                custom_rss_url=custom_rss_url,
                last_crawl_time=last_crawl_time,
            )

            semaphore = asyncio.Semaphore(self.rate_limit)

            async def crawl_with_rate_limit(url: str, title: str) -> CrawlResult:
                async with semaphore:
                    result = await self.crawl_article(url, title_hint=title)
                    if result.success:
                        await asyncio.sleep(1 / self.rate_limit)  # Simple rate limiting
                        return result
                    else:
                        raise Exception(
                            result.error_message or "Unknown error during crawling"
                        )

            tasks = [crawl_with_rate_limit(url, title) for url, title in data]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            valid_results = []
            for i, r in enumerate(results):
                if isinstance(r, CrawlResult):
                    valid_results.append(r)
                else:
                    logger.error(
                        "Crawl task failed for %s: %s",
                        data[i][0],
                        str(r),
                        exc_info=r if isinstance(r, Exception) else None,
                    )

            return valid_results
        except Exception:
            logger.exception("Error in crawl_multiple_articles")
            return []
