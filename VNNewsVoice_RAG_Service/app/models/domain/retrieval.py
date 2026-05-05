from typing import List

from pydantic import BaseModel

from app.models.domain.article import DocumentChunk


class RetrievalResult(BaseModel):
    chunk: DocumentChunk
    score: float
    rank: int


class RetrievalResponse(BaseModel):
    query: str
    results: List[RetrievalResult]
    total_results: int
    retrieval_time_ms: float
