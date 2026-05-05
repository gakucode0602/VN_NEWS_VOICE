import logging
from datetime import datetime, timedelta  # MODIFIED: Added timedelta
from typing import Any, Dict, Optional  # MODIFIED: Added type hints

from app.models.domain.query import DateRange, QueryAnalysis, RetrievalStrategy
from app.models.enums import QueryIntent, QueryScope, TimeSensitivity

logger = logging.getLogger(__name__)


class StrategyBuilder:
    """Build retrieval strategy from query analysis."""

    SCOPE_TOP_K_RANGE = {
        QueryScope.NARROW: 5,
        QueryScope.MEDIUM: 15,
        QueryScope.BROAD: 25,  # MODIFIED: Increased from 20 to 25 for broader exploration
    }

    # MODIFIED: Fixed time filter calculation - now uses days as offset
    TIME_FILTER_DAYS = {
        TimeSensitivity.REALTIME: 0,  # Today only
        TimeSensitivity.RECENT: 90,  # Last 3 months (90 days)
        TimeSensitivity.HISTORICAL: None,  # No automatic filter
        TimeSensitivity.TIMELESS: None,  # No filter
    }

    def __init__(self) -> None:  # MODIFIED: Removed unnecessary analyzer dependency
        """Initialize StrategyBuilder."""
        pass

    def build_strategy(self, query_result: QueryAnalysis) -> RetrievalStrategy:
        """Build retrieval strategy from query analysis."""
        try:
            logger.info(
                f"Building retrieval strategy for query: '{query_result.original_query[:50]}...'"
            )

            # Calculate top_k
            top_k = self._calculate_top_k(query_result.scope, query_result.intent)

            # MODIFIED: Build filters (always initialize, combine date + topic filters)
            filters = self._build_filters(query_result)

            # Build boosting rules
            boosting_rules = self._build_boosting_rules(query_result)

            # Determine if reranking needed
            should_rerank = self._should_rerank(
                top_k, query_result.intent, query_result.scope
            )

            logger.info(
                f"Strategy built: top_k={top_k}, "
                f"rerank={should_rerank}, filters={len(filters)} rules"
            )

            return RetrievalStrategy(
                top_k=top_k,
                filters=filters,
                boosting_rules=boosting_rules,
                rerank=should_rerank,
            )
        except Exception as e:
            logger.error(f"Error building retrieval strategy: {e}", exc_info=True)
            raise

    def _calculate_top_k(self, scope: QueryScope, intent: QueryIntent) -> int:
        """Calculate top_k based on scope and intent."""
        base_top_k = self.SCOPE_TOP_K_RANGE[scope]
        if intent == QueryIntent.COMPARATIVE:
            base_top_k += 5
        elif intent == QueryIntent.ANALYTICAL:
            base_top_k += 10
        return min(base_top_k, 30)  # MODIFIED: Cap at 30 to avoid over-retrieval

    # MODIFIED: New method to combine all filters
    def _build_filters(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        """Build complete filter dict from analysis (date only; topics are used for boosting, not hard filtering)."""
        filters = {}

        # Add date filter if time-sensitive
        date_filter = self._build_date_filter(
            analysis.time_sensitivity, analysis.date_range
        )
        if date_filter:
            filters.update(date_filter)

        # NOTE: Topics are NOT added as hard filters here because Qdrant MatchValue
        # does not support array fields properly. Topics are used via boosting_rules instead.

        return filters

    def _build_date_filter(
        self, time_sensitivity: TimeSensitivity, date_range: Optional[DateRange]
    ) -> Dict[str, Any]:
        """Build date filter based on time sensitivity."""
        # If explicit date_range provided, use it
        if date_range:
            filter_dict = {}
            range_val = {}
            if date_range.start:
                range_val["gte"] = date_range.start.timestamp()
            if date_range.end:
                range_val["lte"] = date_range.end.timestamp()
            if range_val:
                filter_dict["published_at"] = range_val
            return filter_dict

        # Otherwise, use time_sensitivity mapping
        days_offset = self.TIME_FILTER_DAYS.get(time_sensitivity)

        if days_offset is None:
            return {}  # No filter for HISTORICAL/TIMELESS

        # Calculate date threshold
        now = datetime.now()
        if days_offset == 0:
            # REALTIME: today at 00:00:00
            threshold = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # RECENT: now - days_offset
            threshold = now - timedelta(days=days_offset)

        # Qdrant Range requires numeric (float) values, not ISO strings
        return {"published_at": {"gte": threshold.timestamp()}}

    def _build_boosting_rules(self, analysis: QueryAnalysis) -> Dict[str, float]:
        """Build boosting rules based on query analysis."""
        boosting = {}

        # Recency boosting for time-sensitive queries
        if analysis.time_sensitivity == TimeSensitivity.REALTIME:
            boosting["recent"] = 0.3  # Strong boost for breaking news
        elif analysis.time_sensitivity == TimeSensitivity.RECENT:
            boosting["recent"] = 0.2  # Moderate boost

        # Entity matching boosting
        if analysis.entities:
            # Higher boost for factual/comparative queries
            if analysis.intent in [QueryIntent.FACTUAL, QueryIntent.COMPARATIVE]:
                boosting["entity_match"] = 0.4
            else:
                boosting["entity_match"] = 0.2

        # Topic matching boosting (always useful)
        if analysis.topics:
            boosting["topic_match"] = 0.15

        # Title matching boost for narrow scope
        if analysis.scope == QueryScope.NARROW and analysis.entities:
            boosting["title_match"] = 0.25

        return boosting

    def _should_rerank(
        self, top_k: int, intent: QueryIntent, scope: QueryScope
    ) -> bool:
        """Decide if reranking is needed based on query characteristics."""
        # Complex intents benefit from reranking
        intent_check = intent in [QueryIntent.COMPARATIVE, QueryIntent.ANALYTICAL]

        # Large result sets benefit from reranking
        top_k_check = top_k > 15

        # MODIFIED: Broad scope benefits from reranking to filter noise
        scope_check = scope == QueryScope.BROAD

        # MODIFIED: Rerank if any condition is true
        return intent_check or top_k_check or scope_check
