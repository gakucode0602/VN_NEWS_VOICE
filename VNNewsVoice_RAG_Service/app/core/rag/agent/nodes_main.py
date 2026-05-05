import logging
from typing import Literal
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    RemoveMessage,
)
from langgraph.types import Send
from pydantic import BaseModel, Field

from app.core.rag.agent.state import FlowState
from app.core.rag.agent.prompts import (
    get_conversation_summary_prompt,
    get_rewrite_query_prompt,
    get_aggregation_prompt,
)

logger = logging.getLogger(__name__)


class RewriteAnalysis(BaseModel):
    is_clear: bool = Field(
        description="Indicates if the user's question is clear and answerable."
    )
    questions: list[str] = Field(
        description="List of rewritten, self-contained questions."
    )
    clarification_needed: str = Field(
        description="Explanation if the question is unclear."
    )


class MainNodes:
    """Contains LangGraph nodes for the Main Flow Graph."""

    def __init__(self, llm):
        self.llm = llm

    async def summarize_history(self, state: FlowState):
        """Analyzes chat history and summarizes key points for context."""
        logger.info("[Node] Executing: summarize_history (Main Flow)")
        if len(state["messages"]) < 4:
            return {"conversation_summary": ""}

        # Exclude current query
        relevant_msgs = [
            msg
            for msg in state["messages"][:-1]
            if isinstance(msg, (HumanMessage, AIMessage))
            and not getattr(msg, "tool_calls", None)
        ]

        if not relevant_msgs:
            return {"conversation_summary": ""}

        conversation = "Conversation history:\n"
        for msg in relevant_msgs[-6:]:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            conversation += f"{role}: {msg.content}\n"

        response = await self.llm.ainvoke(
            [
                SystemMessage(content=get_conversation_summary_prompt()),
                HumanMessage(content=conversation),
            ]
        )

        return {
            "conversation_summary": response.content,
            "agent_answers": [{"__reset__": True}],
        }

    async def rewrite_query(self, state: FlowState):
        """Analyzes user query and rewrites it for clarity and map-reduce."""
        logger.info("[Node] Executing: rewrite_query (Main Flow)")
        last_message = state["messages"][-1]
        conversation_summary = state.get("conversation_summary", "")

        context_section = ""
        if conversation_summary.strip():
            context_section += f"Conversation Context:\n{conversation_summary}\n"
        context_section += f"User Query:\n{last_message.content}\n"

        # Use Langchain's with_structured_output for guaranteed adherence
        llm_with_structure = self.llm.with_structured_output(RewriteAnalysis)
        try:
            response = await llm_with_structure.ainvoke(
                [
                    SystemMessage(content=get_rewrite_query_prompt()),
                    HumanMessage(content=context_section),
                ]
            )

            if response.questions and response.is_clear:
                # Store original query and rewritten ones, clear out intermediate messages
                delete_all = [
                    RemoveMessage(id=m.id)
                    for m in state["messages"]
                    if not isinstance(m, SystemMessage)
                ]
                return {
                    "questionIsClear": True,
                    "messages": delete_all,
                    "originalQuery": last_message.content,
                    "rewrittenQuestions": response.questions,
                }

            clarification = (
                response.clarification_needed
                if response.clarification_needed
                else "I need more information to understand your question."
            )
            return {
                "questionIsClear": False,
                "messages": [AIMessage(content=clarification)],
            }
        except Exception as e:
            logger.error(f"Error in rewrite_query: {e}")
            # Fallback if structured output fails
            return {
                "questionIsClear": True,
                "messages": [
                    RemoveMessage(id=m.id)
                    for m in state["messages"]
                    if not isinstance(m, SystemMessage)
                ],
                "originalQuery": last_message.content,
                "rewrittenQuestions": [last_message.content],
            }

    def request_clarification(self, state: FlowState):
        """Placeholder for human-in-the-loop interruption."""
        return {}

    def route_after_rewrite(
        self, state: FlowState
    ) -> Literal["request_clarification", "agent_subgraph"]:
        """Route to subgraph(s) if clear, else wait for human."""
        logger.info("[Edge] Routing from rewrite_query...")
        if not state.get("questionIsClear", False):
            logger.info("   -> Routing to: request_clarification")
            return "request_clarification"

        # Map-Reduce: Spawn one Agent subgraph for each rewritten question
        logger.info(
            f"   -> Routing to: agent_subgraph (Spawning {len(state.get('rewrittenQuestions', []))} subgraphs)"
        )
        # Ensure we return valid Send objects targeting 'agent_subgraph'
        return [
            Send(
                "agent_subgraph",
                {"question": query, "question_index": idx, "messages": []},
            )
            for idx, query in enumerate(state.get("rewrittenQuestions", []))
        ]

    async def aggregate_answers(self, state: FlowState):
        """Aggregate multiple answers from subgraphs into final response."""
        logger.info("[Node] Executing: aggregate_answers (Main Flow)")
        if not state.get("agent_answers"):
            return {
                "messages": [AIMessage(content="No answers were generated.")],
                "final_sources": [],
            }

        normalized_answers = [a for a in state["agent_answers"] if isinstance(a, dict)]
        if not normalized_answers:
            logger.warning("agent_answers did not contain dict payloads")
            return {
                "messages": [AIMessage(content="No answers were generated.")],
                "final_sources": [],
            }

        sorted_answers = sorted(normalized_answers, key=lambda x: x.get("index", 0))

        formatted_answers = ""
        all_sources = []
        seen_articles = set()

        for i, ans in enumerate(sorted_answers, start=1):
            formatted_answers += f"\nAnswer {i}:\n{ans.get('answer', '')}\n"
            for src in ans.get("sources", []):
                if isinstance(src, dict):
                    article_id = src.get("article_id")
                    normalized_src = src
                else:
                    article_id = getattr(src, "article_id", None)
                    normalized_src = {
                        "article_id": article_id,
                        "title": getattr(src, "title", "N/A"),
                        "url": getattr(src, "url", ""),
                        "chunk_preview": getattr(src, "chunk_preview", ""),
                        "relevance_score": getattr(src, "relevance_score", 1.0),
                    }

                article_id = str(article_id).strip() if article_id is not None else ""
                if not article_id or article_id in seen_articles:
                    continue

                seen_articles.add(article_id)
                normalized_src["article_id"] = article_id
                all_sources.append(normalized_src)

        user_message = HumanMessage(
            content=f"Original user question: {state.get('originalQuery', '')}\nRetrieved answers:{formatted_answers}"
        )

        response = await self.llm.ainvoke(
            [SystemMessage(content=get_aggregation_prompt()), user_message]
        )

        return {
            "messages": [AIMessage(content=response.content)],
            "final_sources": all_sources,
        }
