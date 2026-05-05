"""
app/messaging/schemas.py
Pydantic schemas cho AMQP messages:
  - MlTaskMessage  (consumed from queue 'ml.tasks')
  - ArticleEventMessage (published to fanout exchange 'article.events')
"""

from pydantic import BaseModel, Field
from typing import List, Optional
import uuid


class ArticleBlockMsg(BaseModel):
    """Content block received from CrawlingService."""

    order: int
    type: str  # "paragraph" | "heading" | "image"
    content: str = ""
    text: str = ""
    tag: str = ""
    src: str = ""
    alt: str = ""
    caption: str = ""


class MlTaskMessage(BaseModel):
    """
    Message consumed from queue 'ml.tasks'.
    Published by CrawlingService (Phase 1.2).
    """

    sourceId: str
    sourceName: str
    title: str
    topImage: str
    url: str
    publishedAt: Optional[str] = None
    sapo: Optional[str] = None
    content: str = ""  # normalized full article body text from CrawlingService
    blocks: List[ArticleBlockMsg] = []


class ArticleEventMessage(BaseModel):
    """
    Message published to fanout exchange 'article.events'.
    Consumed by:
      - ArticleService (Phase 1.5) → saves to article_db
      - RAG Service (Phase 1.4) → indexes to Qdrant
    eventType values: "article.created" | "article.updated" | "video.generated"
    """

    articleId: str = Field(default_factory=lambda: str(uuid.uuid4()))  # UUID4
    sourceId: str = ""
    sourceName: str = ""
    title: str = ""
    topImage: str = ""
    url: str = ""
    publishedAt: Optional[str] = None
    summary: Optional[str] = None  # from ArticleSummarizationService
    audioUrl: Optional[str] = None  # from TTS service (Cloudinary/S3 URL)
    videoUrl: Optional[str] = None  # from Veo video generation
    blocks: List[ArticleBlockMsg] = []
    eventType: str = "article.created"


class VideoGenerationMessage(BaseModel):
    """
    Message consumed from queue 'ml.video.tasks'.
    Published by ArticleService when admin requests video generation.
    """

    articleId: str
    title: str
    topImageUrl: Optional[str] = None
    summary: Optional[str] = None
    videoStyle: Optional[str] = None  # e.g. "news", "tech", "documentary"
    durationSeconds: Optional[int] = None  # 4 | 6 | 8
