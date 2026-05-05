from typing import Type, Dict
from app.services.crawlers.base_crawler import BaseCrawler
from app.services.crawlers.vnexpress_crawler import VnExpressCrawler
from app.services.crawlers.thanhnien_crawler import ThanhNienCrawler
from app.services.crawlers.dantri_crawler import DanTriCrawler
from app.services.crawlers.tuoitre_crawler import TuoiTreCrawler


class CrawlerFactory:
    _crawlers: Dict[str, Type[BaseCrawler]] = {
        "vnexpress": VnExpressCrawler,
        "thanhnien": ThanhNienCrawler,
        "dantri": DanTriCrawler,
        "tuoitre": TuoiTreCrawler,
    }

    @classmethod
    def create_crawler(cls, source_name: str) -> BaseCrawler:
        if source_name not in cls._crawlers:
            raise ValueError(f"Crawler for source '{source_name}' not found.")
        return cls._crawlers[source_name]()

    @classmethod
    def get_available_sources(cls) -> list:
        return list(cls._crawlers.keys())
