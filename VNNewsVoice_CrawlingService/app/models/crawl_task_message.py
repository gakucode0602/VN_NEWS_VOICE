from pydantic import BaseModel
from datetime import datetime


class CrawlTaskMessage(BaseModel):
    """
    Message consumed from queue 'crawl.task'.
    Published by SchedulerService (Phase 1.1).
    """

    sourceId: str  # e.g. "vnexpress", "tuoitre"
    sourceName: str  # e.g. "VnExpress", "Tuổi Trẻ"
    baseUrl: str  # e.g. "https://vnexpress.net"
    requestedAt: datetime  # Accept ISO-8601 string or Unix epoch number
