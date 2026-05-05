from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ArticleBlock:
    """Structured block of article content (paragraph, heading, image)."""

    order: int
    type: str  # "paragraph" | "heading" | "image"
    content: str = ""
    text: str = ""
    tag: str = ""  # for headings: "h1", "h2", etc.
    src: str = ""  # for images: URL
    alt: str = ""  # for images: alt text
    caption: str = ""  # for images: caption


@dataclass
class Article:
    """Crawled article ready for downstream processing."""

    title: str
    top_image: str
    url: str
    blocks: list[ArticleBlock] = field(default_factory=list)
    published_at: Optional[str] = None
    sapo: Optional[str] = None  # human-written lead paragraph
