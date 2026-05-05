import json
from typing import Any, Dict, List, Optional
from app.core.llm.base import BaseLLM
from app.models.domain.iteration import QueryRefinement, RetrievalQuality
from app.models.domain.retrieval import RetrievalResult
import logging

from app.models.enums import RefinementType

logger = logging.getLogger(__name__)


class LLMQueryRefiner:
    REFINEMENT_PROMPT = """
Bạn đang cải thiện câu truy vấn tìm kiếm tin tức.

Ý định ban đầu của người dùng: "{original_query}"
Câu truy vấn hiện tại: "{current_query}"

Các tiêu đề bài báo đã tìm được:
{article_titles}

Vấn đề chất lượng: {reasons}

Hãy cải thiện câu truy vấn để tìm được kết quả tốt hơn.
Trả về JSON format như sau:
{{
    "refined_query": "câu truy vấn đã cải thiện",
    "refinement_type": "expand/narrow/clarify/add_context",
    "reasoning": "lý do cải thiện như vậy",
    "entities_added" : [<Các entities được lấy ra và trả về dạng List[str], nếu không có trả về entities cũ>],
    "filters_changed" : bool <Nên thay đổi filters hiện tại hay không>
}}
    """

    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    def refine(
        self,
        original_query: str,
        current_query: str,
        retrieval_results: List[RetrievalResult],
        quality: RetrievalQuality,
    ) -> QueryRefinement:
        try:
            context_snippets = [
                result.chunk.metadata.get("title", "")
                for result in retrieval_results
                if result.chunk.metadata.get("title", "")
            ]
            reasons = quality.reasons

            prompt = self._build_refine_prompt(
                original_query=original_query,
                current_query=current_query,
                reasons=reasons,
                context_snippets=context_snippets,
            )

            llm_response = self.llm.generate(
                prompt=prompt, max_tokens=300, temperature=0.3
            )

            logger.debug(f"LLM's refine response : '{llm_response[:300]}' ")

            # Modified: Catch JSON extraction errors and fallback gracefully
            try:
                extracted_response = self._extract_llm_response(llm_response)
            except Exception as extract_error:
                logger.warning(
                    f"Failed to extract JSON from LLM response: {extract_error}"
                )
                logger.debug(f"Raw LLM response: {llm_response[:500]}")
                return self._get_default_query_refinement(query=original_query)

            parsed_json = self._parse_response(extracted_response)

            if parsed_json is None:
                logger.warning("JSON parsing failed, using default analysis")
                return self._get_default_query_refinement(query=original_query)

            query_refinement = self._build_query_refine(
                original_query=current_query, parsed_json=parsed_json
            )

            return query_refinement
        except Exception as e:
            # Modified: Fallback to default instead of crashing
            logger.error(f"Unexpected error during refinement: {e}")
            logger.debug(
                f"Original query: {original_query}, Current query: {current_query}"
            )
            return self._get_default_query_refinement(query=original_query)

    def _build_query_refine(
        self, original_query: str, parsed_json: Dict[str, Any]
    ) -> QueryRefinement:
        try:
            return QueryRefinement(
                original_query=original_query,
                refined_query=parsed_json["refined_query"].lower().strip(),
                refinement_type=RefinementType(
                    parsed_json["refinement_type"].lower().strip()
                ),
                reasoning=parsed_json.get("reasoning", ""),
                entities_added=parsed_json.get("entities_added", []),
                filters_changed=parsed_json["filters_changed"],
            )
        except Exception as e:
            logger.error(f"Error building QueryRefinement: {e}")
            raise

    def _build_refine_prompt(
        self,
        original_query: str,
        current_query: str,
        reasons: List[str],
        context_snippets: List[str],
    ) -> str:
        quality_reasons = ", ".join(reasons)
        article_titles = "\n".join(f"- {title}" for title in context_snippets)
        return self.REFINEMENT_PROMPT.format(
            original_query=original_query,
            current_query=current_query,
            reasons=quality_reasons,
            article_titles=article_titles,
        )

    def _extract_llm_response(self, text: str) -> str:
        text = text.replace("```json", "").replace("```", "")

        start = None
        depth = 0

        for i, ch in enumerate(text):
            if ch in "{[":
                if start is None:
                    start = i
                depth += 1
            elif ch in "]}":
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start : i + 1]

        text = text.strip()
        if text.startswith("{") and text.endswith("}"):
            return text

        raise ValueError(f"No valid JSON found in response: {text[:100]}...")

    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(response)

            required_fields = [
                "refined_query",
                "refinement_type",
                "reasoning",
                "entities_added",
                "filters_changed",
            ]

            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in JSON: {data.keys()}")
                return None

            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response: {response[:100]}...")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return None

    def _get_default_query_refinement(self, query: str) -> QueryRefinement:
        logger.warning(f"Using default refinement for query : '{query[:100]}'")
        return QueryRefinement(
            original_query=query,
            refined_query=query,
            refinement_type=RefinementType.NONE,
            reasoning="No reason since refine process was failed",
            filters_changed=False,
        )
