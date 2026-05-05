import logging
from typing import Optional, TYPE_CHECKING

from app.core.llm.base import BaseLLM
from app.models.domain.query import QueryAnalysis
from app.models.enums import QueryIntent, QueryScope, TimeSensitivity

if TYPE_CHECKING:
    from app.services.cache_service import RedisQueryCache

logger = logging.getLogger(__name__)


class LLMQueryAnalyzer:
    """LLM-based query analyzer using structured prompting."""

    ANALYSIS_PROMPT_TEMPLATE = """Bạn là chuyên gia phân tích câu hỏi tin tức tiếng Việt.

Phân tích câu hỏi sau và trả về JSON:

Câu hỏi: "{query}"

QUAN TRỌNG - CHỈ SỬ DỤNG CÁC GIÁ TRỊ SAU (không được tự ý thêm):

intent (MỤC ĐÍCH CÂU HỎI):
- "factual": Hỏi thông tin cụ thể (ai, gì, ở đâu) - VD: "Ai là tổng thống Mỹ?"
- "temporal": Hỏi tin tức theo thời gian (hôm nay, tuần này) - VD: "Tin Ukraine hôm nay", "Thời sự trong tuần"
- "comparative": So sánh giữa 2+ đối tượng - VD: "So sánh GDP 2024 và 2025"
- "exploratory": Khám phá chủ đề rộng - VD: "Tin thể thao", "Tin công nghệ"
- "analytical": Phân tích xu hướng/mô hình - VD: "Phân tích lạm phát", "Xu hướng thị trường"

time_sensitivity (ĐỘ NHẠY THỜI GIAN):
- "realtime": Tin tức hôm nay/hiện tại (hôm nay, bây giờ, breaking) - VD: "Tin hôm nay"
- "recent": Tin gần đây (tuần/tháng này, vừa rồi) - VD: "Tin trong tuần", "Sự kiện tháng 1"
- "historical": Sự kiện quá khứ cụ thể (năm nào, ngày nào) - VD: "Chiến tranh thế giới 2"
- "timeless": Không phụ thuộc thời gian (định nghĩa, tổng quan) - VD: "Thể thao là gì?", "Tin thể thao" (chung chung)

scope (PHẠM VI):
- "narrow": Cụ thể (tên riêng, sự kiện đơn lẻ) - VD: "Vinicius giành Quả bóng vàng"
- "medium": Chủ đề (một lĩnh vực) - VD: "Tin Ukraine"
- "broad": Danh mục rộng (thể thao, chính trị) - VD: "Tin thể thao"

Ví dụ phân tích:

Q: "Tin Ukraine hôm nay"
A: {{"intent": "temporal", "time_sensitivity": "realtime", "scope": "medium", "entities": ["Ukraine"], "topics": ["quốc tế", "chiến tranh"], "confidence": 0.9}}

Q: "Ai là tổng thống Mỹ?"
A: {{"intent": "factual", "time_sensitivity": "timeless", "scope": "narrow", "entities": ["Mỹ"], "topics": ["chính trị"], "confidence": 0.95}}

Q: "So sánh GDP 2024 và 2025"
A: {{"intent": "comparative", "time_sensitivity": "recent", "scope": "narrow", "entities": ["GDP"], "topics": ["kinh tế"], "confidence": 0.9}}

Q: "Tin thể thao"
A: {{"intent": "exploratory", "time_sensitivity": "timeless", "scope": "broad", "topics": ["thể thao"], "confidence": 0.85}}

"""

    def __init__(self, llm: BaseLLM, cache: Optional["RedisQueryCache"] = None):
        """
        Initialize with LLM instance and optional cache.

        Args:
            llm: LLM instance for query analysis
            cache: Optional RedisQueryCache for caching results
        """
        self.llm = llm
        self.cache = cache
        if cache:
            logger.info("Query analyzer initialized with Redis cache")

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze query using LLM with caching support.

        Steps:
        1. Check cache first
        2. If cache miss, call LLM
        3. Parse and build QueryAnalysis
        4. Cache the result
        5. Return analysis
        """
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(query)
            if cached_result:
                logger.info(f"Cache HIT for query: '{query[:50]}...'")
                return cached_result

        try:
            logger.info(f"Analyzing query: '{query[:100]}...'")

            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(query)

            # Call LLM
            llm_response = self.llm.generate_structured(
                prompt=analysis_prompt,
                schema=QueryAnalysis,
                max_tokens=200,
                temperature=0.3,
            )

            logger.debug(f"LLM response: {llm_response}...")

            query_analysis = (
                llm_response  # Since llm_response is already a QueryAnalysis dict/model
            )

            logger.info(
                f"Analysis complete: intent={query_analysis.intent}, confidence={query_analysis.confidence}"
            )

            # Cache the result
            if self.cache:
                self.cache.set(query, query_analysis)

            return query_analysis

        except Exception as e:
            logger.error(f"Analysis failed with error: {e}", exc_info=True)
            return self._get_default_analysis(query)

    def _build_analysis_prompt(self, query: str) -> str:
        """Build structured prompt for LLM."""
        return self.ANALYSIS_PROMPT_TEMPLATE.format(query=query)

    def _get_default_analysis(self, query: str) -> QueryAnalysis:
        """Fallback analysis if LLM fails."""
        logger.warning(f"Using default analysis for query: '{query[:50]}...'")
        return QueryAnalysis(
            original_query=query,
            intent=QueryIntent.EXPLORATORY,
            time_sensitivity=TimeSensitivity.TIMELESS,
            scope=QueryScope.MEDIUM,
            entities=[],
            topics=[],
            keywords=[],
            date_range=None,
            confidence=0.3,
            reasoning="LLM structured analysis failed, using default safe values",
        )
