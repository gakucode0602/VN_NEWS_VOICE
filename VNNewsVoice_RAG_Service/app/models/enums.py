from enum import Enum


# The intention of user question/query -> using for adaptive RAG
class QueryIntent(str, Enum):
    """Intent classification for news queries."""

    FACTUAL = "factual"  # Fact-based questions: "Ai là tổng thống Mỹ?"
    TEMPORAL = "temporal"  # Time-specific queries: "Tin tức hôm nay"
    COMPARATIVE = "comparative"  # Comparison queries: "So sánh X và Y"
    EXPLORATORY = "exploratory"  # Topic exploration: "Tin về thể thao"
    ANALYTICAL = "analytical"  # Trend analysis: "Phân tích xu hướng..."


# Specific time range in the query/question
class TimeSensitivity(str, Enum):
    """
    Time sensitivity classification for queries.

    REALTIME = "realtime"  # Breaking news, today: "hôm nay", "breaking" \n
    RECENT = "recent"  # Recent past: "tuần này", "tháng này" \n
    HISTORICAL = "historical"  # Specific past time: "năm 2023", "tháng 5/2024" \n
    TIMELESS = "timeless"  # No time constraint \n
    """

    REALTIME = "realtime"  # Breaking news, today: "hôm nay", "breaking"
    RECENT = "recent"  # Recent past: "tuần này", "tháng này"
    HISTORICAL = "historical"  # Specific past time: "năm 2023", "tháng 5/2024"
    TIMELESS = "timeless"  # No time constraint


# Scope/breadth of the query
class QueryScope(str, Enum):
    """Scope classification for query breadth."""

    NARROW = "narrow"  # Specific entity/event: "Vinicius Quả bóng vàng"
    MEDIUM = "medium"  # Topic-level: "Tin Ukraine"
    BROAD = "broad"  # Category-level: "Tin thể thao"


# Type of retriever to use
class RetrieverType(str, Enum):
    """Retriever type selection for adaptive routing."""

    DENSE = "dense"  # Vector similarity search (default)
    SPARSE = "sparse"  # BM25 keyword search
    HYBRID = "hybrid"  # Combined dense + sparse


class RefinementType(str, Enum):
    NONE = "none"
    EXPAND = "expand"
    NARROW = "narrow"
    CLARIFY = "clarify"
    ADD_CONTEXT = "add_context"


class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
