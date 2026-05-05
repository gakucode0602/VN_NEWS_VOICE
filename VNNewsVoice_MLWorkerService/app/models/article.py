from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


class ArticleBlock(BaseModel):
    order: int
    type: str
    content: Optional[str] = None
    text: Optional[str] = None
    tag: Optional[str] = None
    src: Optional[str] = None
    alt: Optional[str] = None
    caption: Optional[str] = None


class Article(BaseModel):
    title: str
    url: HttpUrl
    published_at: Optional[datetime] = None
    blocks: List[ArticleBlock]
    top_image: Optional[str] = None

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat() if v else None}}
