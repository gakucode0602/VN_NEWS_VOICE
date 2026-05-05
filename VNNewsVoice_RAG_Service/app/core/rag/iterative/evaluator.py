from typing import List
from app.models.domain.iteration import RetrievalQuality
from app.models.domain.retrieval import RetrievalResult
import logging
import statistics

logger = logging.getLogger(__name__)


class RetrievalQualityEvaluator:
    def __init__(
        self,
        convergence_threshold: float = 0.7,
        min_chunks: int = 3,
        min_avg_score: float = 0.4,
    ) -> None:
        self.convergence_threshold = convergence_threshold
        self.min_chunks = min_chunks
        self.min_avg_score = min_avg_score

    def evaluate(self, results: List[RetrievalResult], query: str) -> RetrievalQuality:
        if len(results) == 0:
            return RetrievalQuality(
                is_good_enough=False,
                avg_score=0.0,
                top_score=0.0,
                total_chunks=0,
                confidence=0.0,
                score_variance=0.0,
                reasons=["No results retrieved"],  # Modified: Added descriptive reason,
                threshold_config={
                    "convergence_threshold": self.convergence_threshold,
                    "min_chunks": self.min_chunks,
                    "min_avg_score": self.min_avg_score,
                },
            )
        scores_list = [result.score for result in results]

        total_chunks = len(results)

        # Calculate scores metrics
        avg_score = sum(scores_list) / len(scores_list)
        top_score = max(scores_list)
        score_variance = (
            statistics.pvariance(scores_list) if len(scores_list) > 1 else 0.0
        )

        reasons = []

        check_avg_score = avg_score > self.min_avg_score
        check_top_score = top_score >= self.convergence_threshold
        check_chunks_amount = total_chunks >= self.min_chunks

        if check_avg_score:
            reasons.append(
                f"Current retrieval result with average score is {avg_score:.2f} > {self.min_avg_score:.2f}"
            )
        else:  # Modified: Added negative case for clarity
            reasons.append(
                f"Average score {avg_score:.2f} < minimum {self.min_avg_score:.2f}"
            )

        if check_top_score:
            reasons.append(
                f"Current retrieval result with top score is {top_score:.2f} > {self.convergence_threshold:.2f}"
            )
        else:
            reasons.append(
                f"Top score {top_score:.2f} < threshold {self.convergence_threshold:.2f}"
            )

        if check_chunks_amount:
            reasons.append(
                f"Current retrieval result with {total_chunks} chunks >= minimum {self.min_chunks}"
            )
        else:
            reasons.append(f"Total chunks {total_chunks} < minimum {self.min_chunks}")

        is_good_enough = check_avg_score and check_top_score and check_chunks_amount

        confidence = (
            min(avg_score / self.convergence_threshold, 1.0) * 0.35
            + min(top_score / self.convergence_threshold, 1.0) * 0.45
            + min(total_chunks / max(self.min_chunks, 1), 1.0) * 0.20
        )

        confidence = max(0.0, min(1.0, confidence))

        threshold_config = {
            "convergence_threshold": self.convergence_threshold,
            "min_chunks": self.min_chunks,
            "min_avg_score": self.min_avg_score,
        }

        return RetrievalQuality(
            is_good_enough=is_good_enough,
            avg_score=avg_score,
            top_score=top_score,
            total_chunks=total_chunks,
            confidence=confidence,
            score_variance=score_variance,
            reasons=reasons,
            threshold_config=threshold_config,
        )
