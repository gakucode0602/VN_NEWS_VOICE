from pydantic import BaseModel
from typing import List, Optional


class ArticleBlockMessage(BaseModel):
    """Structured content block inside an article."""

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
    Message published to queue 'ml.tasks'.
    Consumed by ML Service (Phase 1.3) for summarization + TTS + UUID assignment.
    """

    sourceId: str  # origin source: "vnexpress", "tuoitre", etc.
    sourceName: str  # human-readable source name
    title: str
    topImage: str
    url: str
    publishedAt: Optional[str]  # ISO-8601 string, nullable
    sapo: Optional[str]  # human-written lead paragraph (label for training)
    content: str = ""  # full article body text assembled from paragraph blocks
    blocks: List[ArticleBlockMessage]
