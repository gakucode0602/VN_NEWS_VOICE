import logging
import time
from typing import Any, Dict, Optional
from app.core.rag.retrieval.base import BaseRetrieval
from app.core.rag.iterative.evaluator import RetrievalQualityEvaluator
from app.core.rag.iterative.refiner import LLMQueryRefiner
from app.models.domain.iteration import IterationState, IterativeRetrievalResult
from app.core.rag.adaptive.query_analyzer import LLMQueryAnalyzer
from app.core.rag.adaptive.strategy_builder import StrategyBuilder

logger = logging.getLogger(__name__)


class IterativeRetriever:
    def __init__(
        self,
        evaluator: RetrievalQualityEvaluator,
        refiner: LLMQueryRefiner,
        analyzer: LLMQueryAnalyzer,
        strategy_builder: StrategyBuilder,
    ) -> None:
        self.evaluator = evaluator
        self.refiner = refiner
        self.analyzer = analyzer
        self.strategy_builder = strategy_builder

    def retrieve_iteratively(
        self,
        query: str,
        retriever: BaseRetrieval,
        filters: Optional[Dict[str, Any]],
        max_iterations: int = 3,
        top_k: int = 15,
    ) -> IterativeRetrievalResult:
        """Iteratively retrieve and refine query until convergence or max iterations.

        Args:
            query: Original user query
            retriever: Retriever instance (dense/sparse/hybrid)
            filters: Optional metadata filters
            max_iterations: Maximum number of iterations (default: 3)
            top_k: Number of chunks to retrieve per iteration

        Returns:
            IterativeRetrievalResult with final results, history, and metrics
        """
        # Modified: Initialize tracking variables properly
        original_query = query
        current_query = query
        iteration_number = 0
        is_good_enough = False

        state_history = []
        refinement_chain = [query]  # Modified: Start with original query
        improvement_curve = []  # Modified: Fixed typo from 'improment'

        # Modified: Track best results across iterations (not just last)
        best_results = None
        best_quality = None

        start_time = time.time()

        # Modified: Correct loop condition - continue WHILE not converged AND within max iterations
        while iteration_number < max_iterations and not is_good_enough:
            iteration_number += 1
            logger.info(
                f"Iteration {iteration_number}/{max_iterations}: Current query = '{current_query[:100]}...'"
            )

            # 1. Retrieve with current query
            # Modified: Retrieve INSIDE loop for each iteration
            retrieval_results = retriever.retrieve(
                query=current_query, top_k=top_k, filters=filters
            )

            # 2. Evaluate retrieval quality
            # Modified: Evaluate with current_query (not original query)
            curr_retrieval_quality = self.evaluator.evaluate(
                results=retrieval_results, query=current_query
            )

            # Modified: Track avg_score for improvement curve (not variance)
            improvement_curve.append(curr_retrieval_quality.avg_score)
            logger.info(
                f"Iteration {iteration_number} quality: avg_score={curr_retrieval_quality.avg_score:.3f}, "
                f"is_good_enough={curr_retrieval_quality.is_good_enough}"
            )

            # 3. Track best results across all iterations
            # Modified: Compare quality and keep best iteration results
            if (
                best_quality is None
                or curr_retrieval_quality.avg_score > best_quality.avg_score
            ):
                best_results = retrieval_results
                best_quality = curr_retrieval_quality
                logger.info(f"Iteration {iteration_number} is new best result")

            # 4. Check convergence
            is_good_enough = curr_retrieval_quality.is_good_enough

            # 5. Build iteration state
            # Modified: cumulative_time_ms uses start_time (not curr_time)
            cumulative_time_ms = int((time.time() - start_time) * 1000)

            # Modified: should_continue simplified - just check is_good_enough
            should_continue = not is_good_enough and iteration_number < max_iterations

            iteration_state = IterationState(
                iteration_number=iteration_number,
                query=current_query,
                retrieval_results=retrieval_results,
                quality=curr_retrieval_quality,
                refinement=None,  # Will be filled if we refine
                should_continue=should_continue,
                cumulative_time_ms=cumulative_time_ms,
            )

            # 6. If converged, finalize state and break
            if is_good_enough:
                logger.info(
                    f"Converged at iteration {iteration_number} with avg_score={curr_retrieval_quality.avg_score:.3f}"
                )
                state_history.append(iteration_state)
                break

            # 7. Refine query for next iteration (if not last iteration and not converged)
            if iteration_number < max_iterations:
                logger.info(f"Refining query for iteration {iteration_number + 1}...")
                refinement_result = self.refiner.refine(
                    original_query=original_query,
                    current_query=current_query,
                    retrieval_results=retrieval_results,
                    quality=curr_retrieval_quality,
                )

                # Update iteration state with refinement
                iteration_state.refinement = refinement_result

                # Update current_query for next iteration
                current_query = refinement_result.refined_query
                refinement_chain.append(current_query)

                logger.info(
                    f"Refined query: '{current_query[:100]}...' (type: {refinement_result.refinement_type})"
                )

                # Modified: Re-analyze refined query and rebuild filters when needed
                if refinement_result.filters_changed:
                    logger.info("Filters changed - re-analyzing refined query...")

                    # Re-analyze the refined query to detect new intent/entities/time_sensitivity
                    query_analysis_result = self.analyzer.analyze(query=current_query)

                    # Build new strategy from analysis
                    new_strategy = self.strategy_builder.build_strategy(
                        query_result=query_analysis_result
                    )

                    # Update filters if strategy provides new ones
                    if new_strategy.filters:
                        old_filters = filters
                        filters = new_strategy.filters
                        logger.info(f"Filters updated: {old_filters} -> {filters}")
                    else:
                        logger.info(
                            "New strategy has no filters, keeping existing filters"
                        )

            # Append state to history
            state_history.append(iteration_state)

        # Calculate total time
        total_time_ms = int((time.time() - start_time) * 1000)

        # Build final result
        # Modified: Return best_results (not last iteration results)
        # Modified: convergence_iteration is None if not converged

        if best_results is None:
            best_results = retrieval_results

        final_result = IterativeRetrievalResult(
            final_results=best_results,
            total_iterations=iteration_number,
            converged=is_good_enough,
            convergence_iteration=iteration_number if is_good_enough else None,
            iteration_history=state_history,
            refinement_chain=refinement_chain,
            total_time_ms=total_time_ms,
            improvement_curve=improvement_curve,
        )

        logger.info(
            f"Iterative retrieval completed: {iteration_number} iterations, "
            f"converged={is_good_enough}, total_time={total_time_ms}ms"
        )

        return final_result
