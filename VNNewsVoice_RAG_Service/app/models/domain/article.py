from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class Article(BaseModel):
    article_id: str
    title: str
    content: str
    published_at: datetime
    source: Optional[str] = None
    url: Optional[str] = None
    topic: Optional[str] = None


class DocumentChunk(BaseModel):
    chunk_id: str
    article_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    parent_id: Optional[str] = None
