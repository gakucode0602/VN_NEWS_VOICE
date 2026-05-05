from typing import Annotated, List, Set
from langgraph.graph import MessagesState

import operator


def accumulate_or_reset(existing: List[dict], new: List[dict]) -> List[dict]:
    if new and any(item.get("__reset__") for item in new):
        return []
    return existing + new


def set_union(a: Set[str], b: Set[str]) -> Set[str]:
    return a | b


def accumulate_sources(existing: List[dict], new: List[dict]) -> List[dict]:
    """Accumulate sources by article_id — deduplicate on the fly."""
    seen = {s["article_id"] for s in existing if s.get("article_id")}
    result = list(existing)
    for src in new:
        aid = src.get("article_id")
        if aid and aid not in seen:
            seen.add(aid)
            result.append(src)
    return result


# Main Graph State
class FlowState(MessagesState):
    questionIsClear: bool
    conversation_summary: str
    originalQuery: str
    rewrittenQuestions: List[str]
    agent_answers: Annotated[List[dict], accumulate_or_reset]
    final_sources: List[dict]


# Subgraph State
class AgentState(MessagesState):
    tool_call_count: Annotated[int, operator.add]
    iteration_count: Annotated[int, operator.add]
    question: str
    question_index: int
    context_summary: str
    retrieval_keys: Annotated[Set[str], set_union]
    # Sources accumulated from every tool call — survives compress_context
    extracted_sources: Annotated[List[dict], accumulate_sources]
    final_answer: str
    agent_answers: List[dict]
