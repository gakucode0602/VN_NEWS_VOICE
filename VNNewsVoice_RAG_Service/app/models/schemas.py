from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SourceInfo(BaseModel):
    article_id: str
    title: str
    url: Optional[str]
    published_at: Optional[datetime]
    relevance_score: float
    chunk_preview: Optional[str] = None  # Preview of retrieved chunk content


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID of the conversation thread, if any. Providing this will append the message to the conversation history.",
    )
    top_k: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Number of top results to retrieve (optimized: 15)",
    )
    filters: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    query: str
    answer: str
    conversation_id: str
    sources: List[SourceInfo]
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
