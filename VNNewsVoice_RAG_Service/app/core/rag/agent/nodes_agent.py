import logging
import re
from typing import Literal, Set
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    RemoveMessage,
)

from app.core.rag.agent.state import AgentState
from app.core.rag.agent.prompts import (
    get_orchestrator_prompt,
    get_fallback_response_prompt,
    get_context_compression_prompt,
)
from app.core.rag.retrieval.native_hybrid_retriever import NativeHybridRetriever
from app.repositories.parent_chunk_repository import ParentChunkRepository

logger = logging.getLogger(__name__)

MAX_TOOL_CALLS = 5
MAX_ITERATIONS = 4
BASE_TOKEN_THRESHOLD = 3000
TOKEN_GROWTH_FACTOR = 0.9


def estimate_context_tokens(messages: list) -> int:
    """Roughly estimate token count in messages."""
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
    except ImportError:
        # Fallback: roughly 4 chars = 1 token
        return sum(len(str(getattr(m, "content", m))) // 4 for m in messages)

    total = 0
    for msg in messages:
        if hasattr(msg, "content") and msg.content:
            total += len(encoding.encode(str(msg.content)))
    return total


class AgentNodes:
    """Contains tools and LangGraph nodes for the subgraph (Agent)."""

    def __init__(
        self,
        llm,
        retriever: NativeHybridRetriever,
        parent_repo: ParentChunkRepository,
        filters: dict | None = None,
    ):
        self.retriever = retriever
        self.parent_repo = parent_repo
        self.llm = llm
        self.filters = filters or {}

        # Tools definitions bounded to self dependencies
        async def search_child_chunks(query: str, limit: int = 5) -> str:
            """Search for the top K most relevant chunks using Vector DB."""
            try:
                import asyncio

                results = await asyncio.to_thread(
                    self.retriever.retrieve, query, limit, self.filters or None
                )
                if not results:
                    return "NO_RELEVANT_CHUNKS"

                return "\n\n".join(
                    [
                        f"Parent ID: {doc.chunk.parent_id}\n"
                        f"Article ID: {doc.chunk.article_id}\n"
                        f"Title: {doc.chunk.metadata.get('title', 'N/A')}\n"
                        f"URL: {doc.chunk.metadata.get('url', '')}\n"
                        f"Content: {doc.chunk.content.strip()}"
                        for doc in results
                    ]
                )
            except Exception as e:
                logger.error(f"Error in search tool: {e}")
                return f"RETRIEVAL_ERROR: {str(e)}"

        async def retrieve_parent_chunks(parent_id: str) -> str:
            """Retrieve full parent chunks by their IDs to get surrounding context."""
            if not self.parent_repo:
                return "PARENT_DOCUMENT_NOT_CONFIGURED"
            try:
                parents = await self.parent_repo.get_by_ids([parent_id])
                if not parents:
                    return "NO_PARENT_DOCUMENT"

                parent = parents[0]
                return (
                    f"Parent ID: {parent_id}\n"
                    f"Article ID: {parent.article_id}\n"
                    f"Title: {parent.metadata.get('title', 'N/A')}\n"
                    f"URL: {parent.metadata.get('url', '')}\n"
                    f"Content: {parent.content.strip()}"
                )
            except Exception as e:
                logger.error(f"Error in retrieve parent tool: {e}")
                return f"RETRIEVAL_ERROR: {str(e)}"

        # Bind tools to LLM
        self.tools = [search_child_chunks, retrieve_parent_chunks]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    @staticmethod
    def _tool_call_name(tool_call) -> str:
        if isinstance(tool_call, dict):
            return str(tool_call.get("name", ""))
        return str(getattr(tool_call, "name", ""))

    @staticmethod
    def _tool_call_args(tool_call) -> dict:
        if isinstance(tool_call, dict):
            args = tool_call.get("args", {})
        else:
            args = getattr(tool_call, "args", {})

        return args if isinstance(args, dict) else {}

    async def orchestrator(self, state: AgentState):
        """Main agent logic deciding to search or answer."""
        logger.info(
            f"[Node] Executing: orchestrator (Sub-Flow Question {state.get('question_index', 0)})"
        )
        context_summary = state.get("context_summary", "").strip()
        sys_msg = SystemMessage(content=get_orchestrator_prompt())

        summary_injection = []
        if context_summary:
            summary_injection = [
                HumanMessage(
                    content=f"[COMPRESSED CONTEXT FROM PRIOR RESEARCH]\n\n{context_summary}"
                )
            ]

        if not state.get("messages"):
            human_msg = HumanMessage(content=state["question"])
            guidance = HumanMessage(
                content=(
                    "Assess the question above: if it is a news/event question, call 'search_child_chunks' first. "
                    "If it is a general knowledge question (definition, concept, universal explanation), "
                    "answer directly WITHOUT calling any tool."
                )
            )
            response = await self.llm_with_tools.ainvoke(
                [sys_msg] + summary_injection + [human_msg, guidance]
            )
            return {
                "messages": [human_msg, response],
                "tool_call_count": len(response.tool_calls)
                if hasattr(response, "tool_calls") and response.tool_calls
                else 0,
                "iteration_count": 1,
            }

        # subsequent calls
        response = await self.llm_with_tools.ainvoke(
            [sys_msg] + summary_injection + state["messages"]
        )
        tool_calls = response.tool_calls if hasattr(response, "tool_calls") else []
        return {
            "messages": [response],
            "tool_call_count": len(tool_calls) if tool_calls else 0,
            "iteration_count": 1,
        }

    def route_after_orchestrator(
        self, state: AgentState
    ) -> Literal["tools", "fallback_response", "collect_answer"]:
        """Routing logic after Orchestrator node."""
        iteration = state.get("iteration_count", 0)
        tool_count = state.get("tool_call_count", 0)

        logger.info(
            f"[Edge] Routing from orchestrator (Iteration {iteration}/{MAX_ITERATIONS}, ToolCount {tool_count}/{MAX_TOOL_CALLS})..."
        )

        if iteration >= MAX_ITERATIONS or tool_count > MAX_TOOL_CALLS:
            logger.info("   -> Routing to: fallback_response (Limits Reached)")
            return "fallback_response"

        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []

        if not tool_calls:
            logger.info("   -> Routing to: collect_answer (Ready)")
            return "collect_answer"

        logger.info(f"   -> Routing to: tools (Invoking {len(tool_calls)} tools)")
        return "tools"

    async def fallback_response(self, state: AgentState):
        """Fallback synthesis when we hit constraints."""
        logger.info(
            "[Node] Executing: fallback_response (Limits reached, synthesizing...)"
        )
        seen = set()
        unique_contents = []
        for m in state["messages"]:
            if isinstance(m, ToolMessage) and m.content not in seen:
                unique_contents.append(m.content)
                seen.add(m.content)

        context_summary = state.get("context_summary", "").strip()
        context_parts = []
        if context_summary:
            context_parts.append(f"## Compressed Context\n\n{context_summary}")
        if unique_contents:
            context_parts.append(
                "## Retrieved Data\n\n"
                + "\n\n".join(f"--- DATA SOURCE ---\n{c}" for c in unique_contents)
            )

        context_text = (
            "\n\n".join(context_parts) if context_parts else "No data retrieved."
        )

        prompt_content = f"USER QUERY: {state.get('question')}\n\n{context_text}\n\nINSTRUCTION: Synthesize an answer directly based only on the available context."
        response = await self.llm.ainvoke(
            [
                SystemMessage(content=get_fallback_response_prompt()),
                HumanMessage(content=prompt_content),
            ]
        )
        return {"messages": [response]}

    def should_compress_context(
        self, state: AgentState
    ) -> Literal["compress_context", "orchestrator"]:
        """Edge logic determining if we need compression."""
        logger.info("[Edge] Routing from tools_node...")
        messages = state["messages"]

        # calculate tokens
        current_token_msgs = estimate_context_tokens(messages)
        current_token_sum = estimate_context_tokens(
            [HumanMessage(content=state.get("context_summary", ""))]
        )
        current_tokens = current_token_msgs + current_token_sum

        max_allowed = BASE_TOKEN_THRESHOLD + int(
            current_token_sum * TOKEN_GROWTH_FACTOR
        )

        if current_tokens > max_allowed:
            logger.info(
                f"   -> Routing to: compress_context ({current_tokens}/{max_allowed} tokens)"
            )
            return "compress_context"

        logger.info(
            f"   -> Routing to: orchestrator ({current_tokens}/{max_allowed} tokens)"
        )
        return "orchestrator"

    async def tools_node(self, state: AgentState):
        """Execute tools and update retrieval keys in state."""
        logger.info("[Node] Executing: tools_node")
        from langgraph.prebuilt import ToolNode

        # 1. Run the standard ToolNode to get tool results
        tool_runner = ToolNode(self.tools)
        raw_result = await tool_runner.ainvoke(state)

        # 2. Extract context from the AI message that invoked the tools
        messages = state["messages"]
        new_ids: Set[str] = set()

        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    tool_name = self._tool_call_name(tc)
                    tool_args = self._tool_call_args(tc)

                    if tool_name == "retrieve_parent_chunks":
                        raw = (
                            tool_args.get("parent_id")
                            or tool_args.get("id")
                            or tool_args.get("ids")
                            or []
                        )
                        if isinstance(raw, str):
                            new_ids.add(f"parent::{raw}")
                        else:
                            new_ids.update(f"parent::{r}" for r in raw)
                    elif tool_name == "search_child_chunks":
                        query = tool_args.get("query", "")
                        if query:
                            new_ids.add(f"search::{query}")
                break

        updated_ids = state.get("retrieval_keys", set()) | new_ids

        # ToolNode output can vary by runtime/provider. Normalize to a message list.
        tool_messages = []
        if isinstance(raw_result, dict):
            maybe_messages = raw_result.get("messages", [])
            if isinstance(maybe_messages, list):
                tool_messages = maybe_messages
            elif maybe_messages is not None:
                tool_messages = [maybe_messages]
        elif isinstance(raw_result, list):
            tool_messages = raw_result
        else:
            maybe_messages = getattr(raw_result, "messages", None)
            if isinstance(maybe_messages, list):
                tool_messages = maybe_messages
            elif maybe_messages is not None:
                tool_messages = [maybe_messages]
            else:
                logger.warning(
                    "Unexpected ToolNode result type=%s; continuing without tool messages",
                    type(raw_result).__name__,
                )

        # Extract sources from fresh tool messages before they can be deleted by compress_context
        new_sources: list[dict] = []
        seen_article_ids: set[str] = set()
        for tm in tool_messages:
            if not isinstance(tm, ToolMessage):
                continue
            blocks = tm.content.split("\n\n")
            for block in blocks:
                article_id_match = re.search(r"Article ID:\s*(.+)", block)
                if not article_id_match:
                    continue
                art_id = article_id_match.group(1).strip()
                if not art_id or art_id == "None" or art_id in seen_article_ids:
                    continue
                seen_article_ids.add(art_id)
                title_match = re.search(r"Title:\s*(.+)", block)
                url_match = re.search(r"URL:\s*(.+)", block)
                content_match = re.search(r"Content:\s*(.*)", block, re.DOTALL)
                content = content_match.group(1).strip() if content_match else ""
                new_sources.append(
                    {
                        "article_id": art_id,
                        "title": title_match.group(1).strip() if title_match else "N/A",
                        "url": url_match.group(1).strip() if url_match else "",
                        "chunk_preview": content[:200] + "..."
                        if len(content) > 200
                        else content,
                        "relevance_score": 1.0,
                    }
                )

        # Merge tool messages and custom state variable updates
        return {
            "messages": tool_messages,
            "retrieval_keys": updated_ids,
            "extracted_sources": new_sources,
        }

    async def compress_context(self, state: AgentState):
        """Summarize conversation to fit inside token limits."""
        logger.info("[Node] Executing: compress_context (Reducing memory size...)")
        messages = state["messages"]
        existing_summary = state.get("context_summary", "").strip()

        if not messages:
            return {}

        conversation_text = (
            f"USER QUESTION:\n{state.get('question')}\n\nConversation to compress:\n\n"
        )
        if existing_summary:
            conversation_text += f"[PRIOR COMPRESSED CONTEXT]\n{existing_summary}\n\n"

        for msg in messages[1:]:
            if isinstance(msg, AIMessage):
                tool_calls_info = ""
                if getattr(msg, "tool_calls", None):
                    calls = ", ".join(
                        f"{self._tool_call_name(tc)}({self._tool_call_args(tc)})"
                        for tc in msg.tool_calls
                    )
                    tool_calls_info = f" | Tool calls: {calls}"
                conversation_text += f"[ASSISTANT{tool_calls_info}]\n{msg.content or '(tool call only)'}\n\n"
            elif isinstance(msg, ToolMessage):
                tool_name = getattr(msg, "name", "tool")
                conversation_text += f"[TOOL RESULT — {tool_name}]\n{msg.content}\n\n"

        response = await self.llm.ainvoke(
            [
                SystemMessage(content=get_context_compression_prompt()),
                HumanMessage(content=conversation_text),
            ]
        )
        new_summary = response.content

        # add already executed keys
        retrieved_ids = state.get("retrieval_keys", set())
        if retrieved_ids:
            parent_ids = sorted(r for r in retrieved_ids if r.startswith("parent::"))
            search_qu = sorted(
                r.replace("search::", "")
                for r in retrieved_ids
                if r.startswith("search::")
            )

            block = "\n\n---\n**Already executed:**\n"
            if parent_ids:
                block += (
                    "Parent chunks:\n"
                    + "\n".join(f"- {p.replace('parent::', '')}" for p in parent_ids)
                    + "\n"
                )
            if search_qu:
                block += (
                    "Search queries:\n" + "\n".join(f"- {q}" for q in search_qu) + "\n"
                )
            new_summary += block

        return {
            "context_summary": new_summary,
            "messages": [
                RemoveMessage(id=m.id) for m in messages[1:] if m.id is not None
            ],
        }

    def collect_answer(self, state: AgentState):
        """Append the final answer from subgraph."""
        logger.info("[Node] Executing: collect_answer (Finalizing Sub-Flow)")
        last_message = state["messages"][-1]
        is_valid = (
            isinstance(last_message, AIMessage)
            and last_message.content
            and not getattr(last_message, "tool_calls", None)
        )
        answer = last_message.content if is_valid else "Unable to generate an answer."

        return {
            "final_answer": answer,
            "agent_answers": [
                {
                    "index": state["question_index"],
                    "question": state["question"],
                    "answer": answer,
                    "sources": state.get("extracted_sources", []),
                }
            ],
        }
