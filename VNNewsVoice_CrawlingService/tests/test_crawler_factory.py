import pytest

from app.services.crawlers.base_crawler import BaseCrawler
from app.services.crawlers.crawler_factory import CrawlerFactory


def test_get_available_sources_contains_expected_defaults() -> None:
    sources = CrawlerFactory.get_available_sources()
    assert {"vnexpress", "thanhnien", "dantri", "tuoitre"}.issubset(set(sources))


def test_create_crawler_returns_instance_for_known_source() -> None:
    crawler = CrawlerFactory.create_crawler("vnexpress")
    assert isinstance(crawler, BaseCrawler)


def test_create_crawler_raises_for_unknown_source() -> None:
    with pytest.raises(ValueError, match="not found"):
        CrawlerFactory.create_crawler("unknown-source")
