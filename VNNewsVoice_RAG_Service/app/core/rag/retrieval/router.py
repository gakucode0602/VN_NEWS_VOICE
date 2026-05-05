import logging
from typing import List

from app.core.rag.retrieval.dense_retriever import DenseRetriever
from app.core.rag.retrieval.hybrid_retriever import HybridRetriever
from app.core.rag.retrieval.sparse_retriever import SparseRetriever
from app.models.domain.query import QueryAnalysis, RetrievalStrategy
from app.models.domain.retrieval import RetrievalResult
from app.models.enums import RetrieverType

logger = logging.getLogger(__name__)


@DeprecationWarning
class AdaptiveRouter:
    """Router to dispatch queries to appropriate retriever based on strategy."""

    def __init__(
        self, dense: DenseRetriever, sparse: SparseRetriever, hybrid: HybridRetriever
    ) -> None:
        """
        Initialize router with retriever instances.

        Args:
            dense: Dense vector similarity retriever
            sparse: Sparse BM25 retriever (stub)
            hybrid: Hybrid retriever (partial stub)
        """
        self.retrievers = {
            RetrieverType.DENSE: dense,
            RetrieverType.SPARSE: sparse,
            RetrieverType.HYBRID: hybrid,
        }
        logger.info("AdaptiveRouter initialized with 3 retrievers (2 stubs)")

    def route(
        self,
        query: str,
        strategy: RetrievalStrategy,
        query_analysis: QueryAnalysis,
    ) -> List[RetrievalResult]:
        """
        Route query to appropriate retriever based on strategy.

        Args:
            query: User query string
            strategy: Retrieval strategy with retriever_type, top_k, filters
            query_analysis: Query analysis with entities, topics, keywords (for boosting)

        Returns:
            List of RetrievalResult objects ranked by score
        """
        retriever_type = strategy.retriever_type
        logger.info(
            f"Routing query to {retriever_type.value} retriever. "
            f"Query: '{query[:50]}...', top_k={strategy.top_k}"
        )

        # Select retriever
        retriever = self.retrievers[retriever_type]

        # Retrieve results
        results = retriever.retrieve(
            query=query, top_k=strategy.top_k, filters=strategy.filters
        )

        logger.info(f"Retrieved {len(results)} results from {retriever_type.value}")

        # Apply boosting rules from strategy.boosting_rules
        if strategy.boosting_rules and query_analysis:
            boosting_results = self._apply_boosting(
                results=results,
                boosting_rules=strategy.boosting_rules,
                query_analysis=query_analysis,
            )
            logger.info(
                f"Boosting applied based on {len(strategy.boosting_rules)} rules"
            )
        else:
            boosting_results = results

        return boosting_results

    def _apply_boosting(
        self,
        results: List[RetrievalResult],
        boosting_rules: dict,
        query_analysis: QueryAnalysis,
    ) -> List[RetrievalResult]:
        """
        Apply boosting rules to re-rank results.

        Args:
            results: List of retrieval results
            boosting_rules: Dict of boosting multipliers
            query_analysis: Query analysis with entities, topics, keywords

        Returns:
            Re-ranked list of results with updated scores
        """
        from datetime import datetime

        for result in results:
            metadata = result.chunk.metadata
            total_boost = 0.0

            # 1. Recent boost: Check if published within 3 days
            if "recent" in boosting_rules and boosting_rules["recent"] > 0:
                published_at = metadata.get("published_at")
                if published_at:
                    try:
                        # Handle both datetime object and ISO string
                        if isinstance(published_at, str):
                            pub_date = datetime.fromisoformat(
                                published_at.replace("Z", "+00:00")
                            )
                        else:
                            pub_date = published_at

                        days_ago = (datetime.now(pub_date.tzinfo) - pub_date).days
                        if days_ago <= 3:
                            total_boost += boosting_rules["recent"]
                            logger.debug(
                                f"Recent boost applied: {boosting_rules['recent']} (published {days_ago} days ago)"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to parse published_at: {e}")

            # 2. Entity match boost: Check if query entities appear in metadata
            if "entity_match" in boosting_rules and boosting_rules["entity_match"] > 0:
                if query_analysis.entities:
                    metadata_entities = metadata.get("entities", [])
                    # Case-insensitive matching
                    query_entities_lower = [e.lower() for e in query_analysis.entities]
                    metadata_entities_lower = [e.lower() for e in metadata_entities]

                    if any(
                        qe in metadata_entities_lower for qe in query_entities_lower
                    ):
                        total_boost += boosting_rules["entity_match"]
                        logger.debug(
                            f"Entity match boost applied: {boosting_rules['entity_match']}"
                        )

            # 3. Topic match boost: Check if query topics match metadata topic
            if "topic_match" in boosting_rules and boosting_rules["topic_match"] > 0:
                if query_analysis.topics:
                    metadata_topic = metadata.get("topic", "").lower()
                    query_topics_lower = [t.lower() for t in query_analysis.topics]

                    if any(
                        qt in metadata_topic or metadata_topic in qt
                        for qt in query_topics_lower
                    ):
                        total_boost += boosting_rules["topic_match"]
                        logger.debug(
                            f"Topic match boost applied: {boosting_rules['topic_match']}"
                        )

            # 4. Title match boost: Check if query keywords appear in title
            if "title_match" in boosting_rules and boosting_rules["title_match"] > 0:
                if query_analysis.keywords or query_analysis.entities:
                    title = metadata.get("title", "").lower()
                    search_terms = [k.lower() for k in query_analysis.keywords] + [
                        e.lower() for e in query_analysis.entities
                    ]

                    if any(term in title for term in search_terms):
                        total_boost += boosting_rules["title_match"]
                        logger.debug(
                            f"Title match boost applied: {boosting_rules['title_match']}"
                        )

            # Apply boost to score
            if total_boost > 0:
                original_score = result.score
                result.score = original_score * (1 + total_boost)
                logger.debug(
                    f"Score boosted: {original_score:.4f} -> {result.score:.4f} "
                    f"(+{total_boost * 100:.1f}%)"
                )

        # Re-rank results by new scores
        results.sort(key=lambda r: r.score, reverse=True)

        # Update rank field
        for idx, result in enumerate(results, start=1):
            result.rank = idx

        return results
