"""RAG orchestrator for coordinating retrieval and generation."""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, List, Optional
import uuid


from app.core.generation.generator import Generator
from app.core.rag.adaptive.query_analyzer import LLMQueryAnalyzer
from app.core.rag.adaptive.strategy_builder import StrategyBuilder
from app.core.rag.retrieval.native_hybrid_retriever import NativeHybridRetriever
from app.models.domain.conversation import ConversationTurn
from app.models.enums import ConversationRole
from app.models.schemas import ChatRequest, ChatResponse, SourceInfo
from app.core.rag.iterative.iterator import IterativeRetriever
from app.services.cache_service import RedisQueryCache
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.parent_chunk_repository import ParentChunkRepository
from app.models.domain.article import DocumentChunk

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """Orchestrator for RAG pipeline."""

    def __init__(
        self,
        retriever: NativeHybridRetriever,
        generator: Generator,
        query_analyzer: LLMQueryAnalyzer,
        strategy_builder: StrategyBuilder,
        iterator: IterativeRetriever,
        conversation_repo: ConversationRepository,
        parent_chunk_repo: Optional[ParentChunkRepository] = None,
        cache_service: Optional[RedisQueryCache] = None,
        adaptive_mode: bool = False,
        iterative_mode: bool = True,
        agentic_mode: bool = False,
        max_iterations: int = 3,
    ):
        self.retriever = retriever
        self.generator = generator
        self.query_analyzer = query_analyzer
        self.strategy_builder = strategy_builder
        self.iterator = iterator
        self.conversation_repo = conversation_repo
        self.parent_chunk_repo = parent_chunk_repo
        self.cache_service = cache_service  # Optional: None = caching disabled
        self.adaptive_mode = adaptive_mode
        self.iterative_mode = iterative_mode
        self.agentic_mode = agentic_mode
        self.max_iterations = max_iterations
        logger.info("RAGOrchestrator initialized")

    async def process_query(
        self,
        request: ChatRequest,
        current_user: str,
        max_tokens: int = 4096,
        temperature: float = 0.4,
    ) -> ChatResponse:
        """Process user query through RAG pipeline."""
        try:
            total_start = time.time()
            user_id = current_user  # Hardcoded for now, Phase 8 will inject from JWT

            # 1. Prepare context (Cache / DB)
            (
                conversation_id,
                conversation_results,
                query,
                search_query,
            ) = await self._prepare_conversation_context(request, user_id)

            # 2. Agentic Mode
            if self.agentic_mode:
                return await self._execute_agentic_rag(
                    request,
                    conversation_id,
                    user_id,
                    conversation_results,
                    temperature,
                    total_start,
                )

            # 3. Retrieval Mode (Iterative / Adaptive / Standard)
            logger.info(f"Processing query: '{request.query[:100]}...'")
            retrieval_result, retrieval_time_ms = await self._execute_retrieval(
                search_query, request
            )

            # 4. Format Sources
            source_infos = self._build_source_infos(retrieval_result)

            # 5. Generation
            generation_start = time.time()
            generated_response = await asyncio.to_thread(
                self.generator.generate,
                query,
                retrieval_result,
                max_tokens,
                temperature,
            )
            generation_time_ms = (time.time() - generation_start) * 1000
            logger.info(f"Generation completed in {generation_time_ms:.2f}ms")

            # 6. Finalize timings and state
            total_time_ms = (time.time() - total_start) * 1000
            self._save_conversation_state(
                conversation_id,
                user_id,
                request.query,
                generated_response,
                conversation_results,
            )

            logger.info(f"Query processed successfully in {total_time_ms:.2f}ms")
            return ChatResponse(
                query=request.query,
                answer=generated_response,
                conversation_id=conversation_id,
                sources=source_infos,
                retrieval_time_ms=retrieval_time_ms,
                generation_time_ms=generation_time_ms,
                total_time_ms=total_time_ms,
            )

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    async def process_query_stream(
        self,
        request: ChatRequest,
        current_user: str,
        max_tokens: int = 512,
        temperature: float = 0.4,
    ) -> AsyncGenerator[str, None]:
        """Stream response for the RAG pipeline."""
        try:
            total_start = time.time()
            user_id = current_user

            # 1. Prepare context
            (
                conversation_id,
                conversation_results,
                query,
                search_query,
            ) = await self._prepare_conversation_context(request, user_id)

            yield f"[CONVERSATION_ID]{conversation_id}"

            logger.info(f"Processing query stream: '{request.query[:100]}...'")

            # 2. Retrieval Mode

            if self.agentic_mode:
                article_filter = (request.filters or {}).get("article_id")

                # Widget chat passes article_id filter. In this scoped mode, force a
                # retrieval-first path so vague prompts like "bài này nói gì" still
                # answer from the current article instead of clarification interrupt.
                if article_filter:
                    logger.info(
                        "[Scoped Stream] Detected article_id=%s. Using direct retrieval path.",
                        article_filter,
                    )

                    retrieval_result, retrieval_time_ms = await self._execute_retrieval(
                        search_query, request
                    )

                    # If retrieval returned nothing, the article is likely not indexed yet.
                    if not retrieval_result:
                        not_indexed_msg = (
                            "Bài viết này chưa được đưa vào cơ sở tri thức của tôi. "
                            "Vui lòng thử lại sau hoặc liên hệ quản trị viên để reindex."
                        )
                        yield not_indexed_msg
                        self._save_conversation_state(
                            conversation_id,
                            user_id,
                            request.query,
                            not_indexed_msg,
                            conversation_results,
                        )
                        yield "[DONE]"
                        return

                    source_infos = self._build_source_infos(retrieval_result)

                    generation_start = time.time()
                    full_response = ""
                    async for chunk in self.generator.generate_stream(
                        query, retrieval_result, max_tokens, temperature
                    ):
                        if chunk:
                            full_response += chunk
                            yield chunk
                            await asyncio.sleep(0)

                    if not full_response.strip():
                        full_response = (
                            "Mình chưa tìm thấy đủ nội dung cho bài viết hiện tại. "
                            "Bạn thử đặt câu hỏi cụ thể hơn như 'Bài này nói về sự kiện nào?'"
                        )
                        yield full_response

                    sources_payload = [
                        {
                            "article_id": s.article_id,
                            "title": s.title,
                            "url": s.url,
                            "relevance_score": s.relevance_score,
                        }
                        for s in source_infos
                    ]
                    yield f"[SOURCES]{json.dumps(sources_payload, ensure_ascii=False)}"

                    self._save_conversation_state(
                        conversation_id,
                        user_id,
                        request.query,
                        full_response,
                        conversation_results,
                    )

                    generation_time_ms = (time.time() - generation_start) * 1000
                    total_time_ms = (time.time() - total_start) * 1000
                    logger.info(
                        "[Scoped Stream] Retrieval %.2fms | Generation %.2fms | Total %.2fms",
                        retrieval_time_ms,
                        generation_time_ms,
                        total_time_ms,
                    )

                    yield "[DONE]"
                    return

                full_response = ""
                async for chunk in self._execute_agentic_rag_stream(
                    request, conversation_id, conversation_results, temperature
                ):
                    # [SOURCES] and text tokens — forward to caller
                    if not chunk.startswith("[SOURCES]"):
                        full_response += chunk
                    yield chunk

                if not full_response.strip():
                    full_response = (
                        "Mình chưa hiểu rõ yêu cầu của bạn. "
                        "Bạn có thể hỏi cụ thể hơn về bài viết này, ví dụ: "
                        "'Bài này nói về sự kiện nào?' hoặc 'Nhân vật chính là ai?'"
                    )
                    yield full_response

                # Persist both user query and AI answer to DB (same as standard mode)
                self._save_conversation_state(
                    conversation_id,
                    user_id,
                    request.query,
                    full_response,
                    conversation_results,
                )
                yield "[DONE]"
                return

            retrieval_result, retrieval_time_ms = await self._execute_retrieval(
                search_query, request
            )

            # 3. Format Sources
            source_infos = self._build_source_infos(retrieval_result)

            # 4. Stream Generation
            generation_start = time.time()
            full_response = ""
            async for chunk in self.generator.generate_stream(
                query, retrieval_result, max_tokens, temperature
            ):
                if chunk:
                    full_response += chunk
                    yield chunk
                    await asyncio.sleep(0)

            # 5. Stream source info as special event before [DONE]
            sources_payload = [
                {
                    "article_id": s.article_id,
                    "title": s.title,
                    "url": s.url,
                    "relevance_score": s.relevance_score,
                }
                for s in source_infos
            ]
            yield f"[SOURCES]{json.dumps(sources_payload, ensure_ascii=False)}"

            # 6. Finalize timings and state
            self._save_conversation_state(
                conversation_id,
                user_id,
                request.query,
                full_response,
                conversation_results,
            )

            generation_time_ms = (time.time() - generation_start) * 1000
            total_time_ms = (time.time() - total_start) * 1000
            logger.info(f"Retrieval process in {retrieval_time_ms}:.2fms")
            logger.info(f"Generation process in {generation_time_ms:.2f}ms")
            logger.info(f"Streaming query processed in {total_time_ms:.2f}ms")

            yield "[DONE]"

        except Exception as e:
            logger.error(f"Error processing query stream: {e}")
            yield f"[ERROR] {str(e)}"

    # =========================================================================
    # REFACTORED HELPER METHODS (CLEAN CODE)
    # =========================================================================

    async def _prepare_conversation_context(
        self, request: ChatRequest, user_id: str
    ) -> tuple[str, List[ConversationTurn], str, str]:
        """Prepare context by fetching history and modifying the prompt if needed."""
        conversation_id = request.conversation_id or str(uuid.uuid4())
        conversation_results = self._check_conversation_cached(conversation_id, user_id)

        if conversation_results is None:
            history_results = await self._check_conversation_database(conversation_id)
            if history_results:
                if self.cache_service:
                    self.cache_service.set_cached_conversation(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        conversation_turns=history_results,
                    )
                query = self._build_prompt(request.query, history_results)
                search_query = self._build_search_query(request.query, history_results)
                conversation_results = history_results
            else:
                conversation_results = []
                query = request.query
                search_query = request.query
        else:
            query = self._build_prompt(request.query, conversation_results)
            search_query = self._build_search_query(request.query, conversation_results)

        return conversation_id, conversation_results, query, search_query

    async def _execute_agentic_rag(
        self,
        request: ChatRequest,
        conversation_id: str,
        user_id: str,
        conversation_results: List[ConversationTurn],
        temperature: float,
        total_start: float,
    ) -> ChatResponse:
        """Isolated execution logic for Agentic Mode using LangGraph."""
        logger.info("Executing Agentic RAG Mode via LangGraph")
        from app.core.rag.agent.graph import create_agent_graph
        from langchain_core.messages import HumanMessage, AIMessage

        llm = self.generator.llm.get_langchain_model(temperature=temperature)

        app_graph = create_agent_graph(
            llm=llm, retriever=self.retriever, parent_repo=self.parent_chunk_repo
        )

        config = {"configurable": {"thread_id": conversation_id}, "recursion_limit": 50}

        # BUG FIX: Convert History correctly to Human/AIMessages
        agent_messages = []
        if conversation_results:
            for turn in conversation_results:
                if turn.role == ConversationRole.USER:
                    agent_messages.append(HumanMessage(content=str(turn.content)))
                else:
                    agent_messages.append(AIMessage(content=str(turn.content)))

        agent_messages.append(HumanMessage(content=request.query))

        start_time = time.time()
        result_state = await app_graph.ainvoke(
            {"originalQuery": request.query, "messages": agent_messages}, config
        )

        final_answer = result_state["messages"][-1].content
        generation_time_ms = (time.time() - start_time) * 1000

        # Build Source Info from LangGraph State
        source_infos = []
        for s in result_state.get("final_sources", []):
            if isinstance(s, dict):
                article_id = s.get("article_id")
                title = s.get("title", "N/A")
                url = s.get("url", "")
                relevance_score = s.get("relevance_score", 1.0)
                chunk_preview = s.get("chunk_preview", "")
            else:
                article_id = getattr(s, "article_id", None)
                title = getattr(s, "title", "N/A")
                url = getattr(s, "url", "")
                relevance_score = getattr(s, "relevance_score", 1.0)
                chunk_preview = getattr(s, "chunk_preview", "")

            if article_id is None:
                continue

            source_infos.append(
                SourceInfo(
                    article_id=str(article_id),
                    title=title,
                    url=url,
                    published_at=None,
                    relevance_score=relevance_score,
                    chunk_preview=chunk_preview,
                )
            )

        # Save conversation using standard state method
        self._save_conversation_state(
            conversation_id, user_id, request.query, final_answer, conversation_results
        )

        total_time_ms = (time.time() - total_start) * 1000
        return ChatResponse(
            query=request.query,
            answer=final_answer,
            conversation_id=conversation_id,
            sources=source_infos,
            retrieval_time_ms=0.0,
            generation_time_ms=generation_time_ms,
            total_time_ms=total_time_ms,
        )

    async def _execute_retrieval(
        self, search_query: str, request: ChatRequest
    ) -> tuple[List[Any], float]:
        """Handles retrieval routing between Adaptive, Iterative, and Standard modes."""
        cached_retrieval = self._check_cached_retrieval(request.query)
        if cached_retrieval:
            logger.info("Using cached retrieval")
            return cached_retrieval, 0.0

        if self.iterative_mode and self.adaptive_mode:
            logger.warning(
                "Both iterative_mode and adaptive_mode enabled. Using iterative_mode."
            )

        retrieval_start = time.time()
        if self.iterative_mode and self._has_iterative_components():
            iterator_result = await asyncio.to_thread(
                self.iterator.retrieve_iteratively,
                query=search_query,
                retriever=self.retriever,
                filters=request.filters,
                max_iterations=self.max_iterations,
                top_k=request.top_k,
            )
            logger.info(
                f"Iterative retrieval completed: {iterator_result.total_iterations} iterations."
            )
            retrieval_result = iterator_result.final_results
            retrieval_time_ms = iterator_result.total_time_ms

        elif self.adaptive_mode:
            analysis_result = await asyncio.to_thread(
                self.query_analyzer.analyze, query=search_query
            )
            strategy = await asyncio.to_thread(
                self.strategy_builder.build_strategy, analysis_result
            )
            # Merge strategy filters with explicit request filters.
            # request.filters (e.g. article_id from widget) take precedence.
            merged_filters = {
                **(strategy.filters or {}),
                **(request.filters or {}),
            } or None
            retrieval_result = await asyncio.to_thread(
                self.retriever.retrieve,
                query=search_query,
                top_k=strategy.top_k,
                filters=merged_filters,
            )
            retrieval_time_ms = (time.time() - retrieval_start) * 1000

        else:
            retrieval_result = await asyncio.to_thread(
                self.retriever.retrieve, search_query, request.top_k, request.filters
            )
            retrieval_time_ms = (time.time() - retrieval_start) * 1000

        # Parent Mapping & Cache Update
        retrieval_result = await self._map_to_parents(retrieval_result)
        logger.info(f"Retrieval completed in {retrieval_time_ms:.2f}ms")

        if self.cache_service:
            try:
                self.cache_service.set_cache_retrieval(request.query, retrieval_result)
            except Exception as e:
                logger.warning(f"Failed to cache retrieval: {e}")

        return retrieval_result, retrieval_time_ms

    def _build_source_infos(self, retrieval_result: List[Any]) -> List[SourceInfo]:
        """Convert retrieval results to SourceInfo DTOs."""
        return [
            SourceInfo(
                article_id=r.chunk.article_id,
                title=r.chunk.metadata.get("title", "N/A"),
                url=r.chunk.metadata.get("url", ""),
                published_at=r.chunk.metadata.get("published_at"),
                relevance_score=r.score,
                chunk_preview=r.chunk.content[:200] + "..."
                if len(r.chunk.content) > 200
                else r.chunk.content,
            )
            for r in retrieval_result
        ]

    def _save_conversation_state(
        self,
        conversation_id: str,
        user_id: str,
        query: str,
        response: str,
        conversation_results: List[ConversationTurn],
    ):
        """Update Chat History across Memory Array, Redis Cache, and Async Postgres Thread."""
        user_turn = ConversationTurn(role=ConversationRole.USER, content=query)
        ai_turn = ConversationTurn(role=ConversationRole.ASSISTANT, content=response)

        conversation_results.append(user_turn)
        conversation_results.append(ai_turn)

        # HOT PATH: Write to Redis immediately
        if self.cache_service:
            self.cache_service.set_cached_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                conversation_turns=conversation_results,
            )

        # COLD PATH: Flush to PostgreSQL async in background (fire-and-forget)
        asyncio.create_task(
            self._flush_to_postgres(
                conversation_id=conversation_id,
                user_id=user_id,
                user_content=query,
                ai_content=response,
            )
        )

    def _has_iterative_components(self) -> bool:
        return self.iterator is not None

    def _check_cached_retrieval(self, query: str):
        """Return cached retrieval results, or None if cache disabled/miss."""
        if self.cache_service is None:
            return None
        try:
            return self.cache_service.get_cached_retrieval(query)
        except Exception as e:
            logger.warning(f"Cache check failed, proceeding without cache: {e}")
            return None

    def _check_conversation_cached(
        self, conversation_id: str | None, user_id: str = "test_user"
    ):
        if self.cache_service is None or conversation_id is None:
            return None
        try:
            return self.cache_service.get_cached_conversation(
                conversation_id=conversation_id, user_id=user_id
            )
        except Exception as e:
            logger.error(f"Cache check failed, proceeding with out cache: {e}")
            return None

    async def _check_conversation_database(
        self, conversation_id: str | None, user_id: str = "test_user"
    ) -> List[ConversationTurn]:
        if conversation_id is None:
            return []
        try:
            results = await self.conversation_repo.get_history(
                conversation_id=conversation_id
            )
            return results
        except Exception as e:
            logger.error(f"History fetch failed: {e}")
            return []

    async def _flush_to_postgres(
        self,
        conversation_id: str,
        user_id: str,
        user_content: str,
        ai_content: str,
    ) -> None:
        """Background cold-path: persist conversation turn to PostgreSQL.

        Creates its OWN database session — the request-scoped session is
        already closed by FastAPI when this background task runs.
        Errors are logged but never propagate back to the caller.
        """
        from app.config.database import AsyncSessionLocal
        from app.repositories.conversation_repository import ConversationRepository

        try:
            async with AsyncSessionLocal() as session:
                repo = ConversationRepository(session)
                await repo.append_turn(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role=ConversationRole.USER,
                    content=user_content,
                )
                await repo.append_turn(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role=ConversationRole.ASSISTANT,
                    content=ai_content,
                )
            logger.debug(f"[PG flush] conversation {conversation_id} persisted.")
        except Exception as e:
            logger.error(
                f"[PG flush] Failed to persist conversation {conversation_id}: {e}"
            )

    def _build_prompt(
        self, query: str, conversation_turns: List[ConversationTurn]
    ) -> str:
        conversation_turns_str = [
            f"role: {turn.role}\ncontent:{turn.content}\ncreated_at:{turn.created_at}\n"
            for turn in conversation_turns
        ]
        combine_str = "\n\n".join(conversation_turns_str)
        return f"""{query}\n\nCuộc hội thoại trước đó như sau:\n {combine_str}"""

    def _build_search_query(
        self, query: str, conversation_turns: List[ConversationTurn]
    ) -> str:
        """Build a context-enriched search query for retrieval.

        Only uses previous USER turns as context — assistant responses
        (especially "không có thông tin" fallbacks) are noise for retrieval.
        """
        if not conversation_turns:
            return query

        # Only look at USER turns from the recent history
        user_turns = [t for t in conversation_turns if t.role == ConversationRole.USER]
        # Take the last 2 user queries (excluding the current one)
        recent_user = user_turns[-2:] if len(user_turns) >= 2 else user_turns

        context_snippets = []
        for turn in recent_user:
            snippet = str(turn.content)[:120].strip()
            if snippet:
                context_snippets.append(snippet)

        if not context_snippets:
            return query

        context_str = " | ".join(context_snippets)
        enriched = f"{query} (ngữ cảnh: {context_str})"
        logger.debug(f"Search query enriched: '{enriched[:150]}...'")
        return enriched

    async def _map_to_parents(self, retrieval_results: List[Any]) -> List[Any]:
        """Convert child chunks from Qdrant directly to parent chunks from DB."""
        if not self.parent_chunk_repo:
            return retrieval_results

        # Extract parent_ids from retrieval results metadata
        parent_ids = list(
            set(
                [
                    r.chunk.metadata.get("parent_id")
                    for r in retrieval_results
                    if r.chunk.metadata.get("parent_id")
                ]
            )
        )

        if not parent_ids:
            return retrieval_results

        # Fetch parents from DB
        parent_chunks_from_db = await self.parent_chunk_repo.get_by_ids(parent_ids)
        parent_map = {p.id: p for p in parent_chunks_from_db}

        final_results = []
        seen_parents = set()

        for r in retrieval_results:
            pid = r.chunk.metadata.get("parent_id")
            if pid and pid in parent_map and pid not in seen_parents:
                p = parent_map[pid]

                # Turn DB ParentChunk into DocumentChunk for UI/Generation
                parent_doc_chunk = DocumentChunk(
                    chunk_id=p.id,
                    article_id=p.article_id,
                    content=p.content,
                    chunk_index=p.chunk_index,
                    metadata={
                        "source": "parent_chunk_from_db",
                        "title": r.chunk.metadata.get("title", ""),
                        "url": r.chunk.metadata.get("url", ""),
                        "published_at": r.chunk.metadata.get("published_at") or None,
                    },
                )

                final_results.append(r.model_copy(update={"chunk": parent_doc_chunk}))
                seen_parents.add(pid)
            elif not pid:
                # Flat chunk (no parent relationship), include as-is
                final_results.append(r)
            else:
                # parent_id is set but NOT found in Postgres (DB out of sync).
                # Fall back to the child chunk from Qdrant rather than silently discarding.
                logger.warning(
                    "Parent chunk %s not found in Postgres for article %s. Using child chunk as fallback.",
                    pid,
                    r.chunk.article_id,
                )
                final_results.append(r)

        return final_results

    async def _execute_agentic_rag_stream(
        self,
        request: ChatRequest,
        conversation_id: str,
        conversation_results: List[ConversationTurn],
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens from the LangGraph Agentic pipeline.

        Streams only final-answer tokens from `aggregate_answers` node.
        All intermediate reasoning nodes (rewrite_query, summarize_history,
        agent_subgraph) are intentionally suppressed from the output.

        Yields:
            str: Text tokens from the LLM, then a [SOURCES] JSON event at the end.
        """
        from app.core.rag.agent.graph import create_agent_graph
        from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
        from langchain_core.runnables import RunnableConfig

        logger.info(f"[Agentic Stream] Starting for conversation_id={conversation_id}")

        llm = self.generator.llm.get_langchain_model(temperature=temperature)
        app_graph = create_agent_graph(
            llm=llm,
            retriever=self.retriever,
            parent_repo=self.parent_chunk_repo,
            filters=request.filters or None,
        )
        config: RunnableConfig = {
            "configurable": {"thread_id": str(conversation_id)},
            "recursion_limit": 50,
        }

        # Build message history from conversation turns
        agent_messages: List = []
        for turn in conversation_results:
            if turn.role == ConversationRole.USER:
                agent_messages.append(HumanMessage(content=str(turn.content)))
            elif turn.role == ConversationRole.ASSISTANT:
                agent_messages.append(AIMessage(content=str(turn.content)))
        agent_messages.append(HumanMessage(content=str(request.query)))

        # Stream: only yield tokens from the final 'aggregate_answers' node
        token_count = 0
        async for chunk, metadata in app_graph.astream(  # type: ignore[call-overload]
            {"originalQuery": request.query, "messages": agent_messages},
            config=config,
            stream_mode="messages",
        ):
            metadata = metadata if isinstance(metadata, dict) else {}
            node = metadata.get("langgraph_node", "")
            # Only surface tokens from the final synthesis node
            if node == "aggregate_answers" and isinstance(chunk, AIMessageChunk):
                content = chunk.content
                if content:
                    token_count += 1
                    yield content

        logger.info(f"[Agentic Stream] Streamed {token_count} tokens.")

        # Fetch final graph state ONCE after the stream completes
        state = await app_graph.aget_state(config=config)
        state_values = state.values if isinstance(state.values, dict) else {}

        # If the graph stopped at clarification checkpoint, there may be no final tokens.
        # Surface the latest AI clarification message instead of returning empty content.
        if token_count == 0:
            fallback_text = ""
            state_messages = state_values.get("messages", [])
            if isinstance(state_messages, list):
                for msg in reversed(state_messages):
                    msg_content = ""
                    msg_is_ai = False

                    if isinstance(msg, dict):
                        msg_content = str(msg.get("content", ""))
                        msg_type = str(msg.get("type", "")).lower()
                        msg_is_ai = msg_type == "ai"
                    else:
                        msg_content = str(getattr(msg, "content", ""))
                        msg_type = str(getattr(msg, "type", "")).lower()
                        class_name = msg.__class__.__name__.lower()
                        msg_is_ai = msg_type == "ai" or class_name.startswith(
                            "aimessage"
                        )

                    if msg_is_ai and msg_content.strip():
                        fallback_text = msg_content.strip()
                        break

            if not fallback_text:
                fallback_text = (
                    "Mình chưa hiểu rõ yêu cầu của bạn. "
                    "Bạn có thể hỏi cụ thể hơn về bài viết này, ví dụ: "
                    "'Bài này nói về sự kiện nào?' hoặc 'Nhân vật chính là ai?'"
                )

            logger.info(
                "[Agentic Stream] No final tokens; emitting clarification fallback text."
            )
            yield fallback_text

        final_sources: List = state_values.get("final_sources", [])

        normalized_sources = []
        for source in final_sources:
            if isinstance(source, dict):
                article_id = source.get("article_id")
                title = source.get("title", "N/A")
                url = source.get("url", "")
                relevance_score = source.get("relevance_score", 1.0)
                chunk_preview = source.get("chunk_preview", "")
            else:
                article_id = getattr(source, "article_id", None)
                title = getattr(source, "title", "N/A")
                url = getattr(source, "url", "")
                relevance_score = getattr(source, "relevance_score", 1.0)
                chunk_preview = getattr(source, "chunk_preview", "")

            if article_id is None:
                continue

            normalized_sources.append(
                {
                    "article_id": str(article_id),
                    "title": title,
                    "url": url,
                    "relevance_score": relevance_score,
                    "chunk_preview": chunk_preview,
                }
            )

        if normalized_sources:
            logger.info(
                f"[Agentic Stream] Attaching {len(normalized_sources)} sources."
            )
            yield f"[SOURCES]{json.dumps(normalized_sources, ensure_ascii=False)}"
