from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import QueryIntent, QueryScope, TimeSensitivity


class DateRange(BaseModel):
    """Date range for temporal queries."""

    start: Optional[datetime] = None
    end: Optional[datetime] = None


class QueryAnalysis(BaseModel):
    """Result of query analysis for adaptive RAG."""

    original_query: str
    intent: QueryIntent
    time_sensitivity: TimeSensitivity
    scope: QueryScope
    entities: List[str] = Field(
        default_factory=list, description="Named entities extracted from query"
    )
    topics: List[str] = Field(
        default_factory=list, description="Topic tags (e.g., 'thể thao', 'chính trị')"
    )
    keywords: List[str] = Field(
        default_factory=list, description="Key terms for matching"
    )
    date_range: Optional[DateRange] = Field(
        default=None, description="Extracted date range if temporal"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score of analysis"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Explanation of analysis (for debugging)"
    )
    is_clear: bool = Field(
        default=True,
        description="Indicates if the user's question is clear and answerable.",
    )
    rewritten_queries: List[str] = Field(
        default_factory=list, description="List of rewritten, self-contained questions."
    )
    clarification_needed: Optional[str] = Field(
        default=None, description="Explanation if the question is unclear."
    )


class RetrievalStrategy(BaseModel):
    """Retrieval strategy built from query analysis."""

    top_k: int = Field(ge=1, le=50, description="Number of results to retrieve")
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata filters for vector search"
    )
    boosting_rules: Dict[str, float] = Field(
        default_factory=dict,
        description="Score boosting rules (e.g., {'recent': 0.2, 'entity_match': 0.3})",
    )
    rerank: bool = Field(default=False, description="Whether to apply reranking")

    # Backward compatibility aliases
    @property
    def metadata_filters(self) -> Dict[str, Any]:
        """Alias for backward compatibility."""
        return self.filters

    @property
    def use_reranking(self) -> bool:
        """Alias for backward compatibility."""
        return self.rerank

    @property
    def boost_recent(self) -> bool:
        """Alias for backward compatibility."""
        return "recent" in self.boosting_rules
