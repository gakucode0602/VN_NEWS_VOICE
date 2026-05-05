from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.domain.retrieval import RetrievalResult
from app.models.enums import RefinementType


class RetrievalQuality(BaseModel):
    is_good_enough: bool
    avg_score: float = Field(ge=0.0, le=1.0)
    top_score: float = Field(ge=0.0, le=1.0)
    total_chunks: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    score_variance: float = Field(ge=0.0)
    reasons: List[str] = Field(
        default_factory=list, description="Human readable reason"
    )
    threshold_config: Dict[str, float] = Field(
        default_factory=dict, description="Used for debugging"
    )


class QueryRefinement(BaseModel):
    original_query: str
    refined_query: str
    refinement_type: RefinementType  # "expand" | "narrow" | "clarify" | "add_context"
    reasoning: str  # LLMs explaination
    entities_added: List[str] = Field(
        default_factory=list, description="New entities extracted"
    )
    filters_changed: bool
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this refinement occurred",
    )


class IterationState(BaseModel):
    iteration_number: int
    query: str = Field(description="Current query for current iteration")
    retrieval_results: List[RetrievalResult] = Field(
        description="Current retrieval result"
    )
    quality: RetrievalQuality
    refinement: Optional[QueryRefinement]  # None for last iteration
    should_continue: bool
    cumulative_time_ms: int


class IterativeRetrievalResult(BaseModel):
    final_results: List[RetrievalResult] = Field(
        default_factory=list, description="Best chunks selected"
    )
    total_iterations: int
    converged: bool  # True if stopped early, False if hit max
    convergence_iteration: Optional[int] = Field(
        default=None, description="Which iteration converged (None if didn't converge)"
    )

    # History
    iteration_history: List[IterationState] = Field(
        default_factory=list,
    )
    refinement_chain: List[str] = Field(
        default_factory=list, description="['query1', 'query2', 'query3']"
    )

    # Metrics
    total_time_ms: int
    improvement_curve: List[float] = Field(
        default_factory=list, description="Quality scores per iteration"
    )
