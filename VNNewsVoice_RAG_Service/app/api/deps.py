# Dependency Injection
from functools import lru_cache

from fastapi import Depends

from app.config.settings import get_settings
from app.core.generation.generator import Generator
from app.core.indexing.embedder import LocalSentenceTransformerEmbedder
from app.core.llm.base import BaseLLM  # ADDED: Import base class for type hints
from app.core.llm.gemini_adapter import GeminiAdapter
from app.core.llm.nvidia_adapter import NvidiaAdapter
from app.core.llm.ollama_adapter import OllamaAdapter
from app.core.llm.claude_adapter import ClaudeAdapter
from app.core.rag.adaptive.query_analyzer import LLMQueryAnalyzer
from app.core.rag.adaptive.strategy_builder import StrategyBuilder
from app.core.rag.iterative.evaluator import RetrievalQualityEvaluator
from app.core.rag.iterative.iterator import IterativeRetriever
from app.core.rag.iterative.refiner import LLMQueryRefiner
from app.core.rag.orchestrator import RAGOrchestrator
from app.core.rag.retrieval.native_hybrid_retriever import NativeHybridRetriever
from app.repositories.vector_store import QdrantVectorStore
from app.services.cache_service import RedisQueryCache
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.parent_chunk_repository import ParentChunkRepository
from app.config.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.auth_user import get_current_user


@lru_cache
def get_embedder():
    settings = get_settings()
    return LocalSentenceTransformerEmbedder(
        dense_model_name=settings.dense_local_embed_model_name,
        sparse_model_name=settings.sparse_local_embed_model_name,
    )


@lru_cache
def get_refiner_llm() -> BaseLLM:
    """Get LLM for query analysis/refinement. Follows the same provider as get_llm()."""
    return get_llm()


@lru_cache
def get_llm() -> BaseLLM:  # FIXED: Added return type hint
    """Get LLM instance based on configured provider."""
    settings = get_settings()
    if settings.llm_provider == "gemini":
        return GeminiAdapter(
            model_name=settings.gemini_model_name, api_key=settings.gemini_api_key
        )
    elif settings.llm_provider == "nvidia":
        return NvidiaAdapter(
            base_url=settings.nvidia_base_url,
            api_key=settings.nvidia_api_key,
            model_name=settings.nvidia_model_name,
        )
    elif settings.llm_provider == "ollama":
        return OllamaAdapter(
            model_name=settings.ollama_model_name, host=settings.ollama_base_url
        )
    elif settings.llm_provider == "claude":
        return ClaudeAdapter(
            model_name=settings.claude_model_name, api_key=settings.claude_api_key
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


def get_generator(
    llm: BaseLLM = Depends(get_llm),
):  # FIXED: Changed type hint to BaseLLM
    return Generator(llm=llm)


@lru_cache
def get_vector_store():
    settings = get_settings()
    return QdrantVectorStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection_name,
        api_key=settings.qdrant_api_key,
    )


def get_native_hybrid_retriever(
    embedder: LocalSentenceTransformerEmbedder = Depends(get_embedder),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
):
    return NativeHybridRetriever(embedder=embedder, vector_store=vector_store)


@lru_cache
def get_cache():
    """Create Redis cache singleton for query analysis."""
    settings = get_settings()
    try:
        return RedisQueryCache(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            ttl_seconds=settings.redis_ttl_seconds,
        )
    except Exception as e:
        # If Redis fails to connect, log error and return None (cache disabled)
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Redis cache initialization failed: {e}. Cache disabled.")
        return None


def get_query_analyzer(
    llm: BaseLLM = Depends(
        get_refiner_llm
    ),  # Ollama: lightweight local model for query analysis
    cache: RedisQueryCache = Depends(get_cache),
):
    return LLMQueryAnalyzer(llm=llm, cache=cache)


def get_strategy_builder():
    return StrategyBuilder()


def get_evaluator():
    return RetrievalQualityEvaluator()


def get_refiner(llm: BaseLLM = Depends(get_refiner_llm)):
    return LLMQueryRefiner(llm=llm)


def get_iterator(
    evaluator: RetrievalQualityEvaluator = Depends(get_evaluator),
    refiner: LLMQueryRefiner = Depends(get_refiner),
    analyzer: LLMQueryAnalyzer = Depends(get_query_analyzer),
    strategy_builder: StrategyBuilder = Depends(get_strategy_builder),
):
    return IterativeRetriever(
        evaluator=evaluator,
        refiner=refiner,
        analyzer=analyzer,
        strategy_builder=strategy_builder,
    )


def require_admin(current_user: str = Depends(get_current_user)) -> str:
    return current_user  # Hard code for now


async def get_conversation_repo(
    session: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    return ConversationRepository(session=session)


async def get_parent_chunk_repo(
    session: AsyncSession = Depends(get_db),
) -> ParentChunkRepository:
    return ParentChunkRepository(session=session)


def get_orchestrator(
    retriever=Depends(get_native_hybrid_retriever),
    generator=Depends(get_generator),
    query_analyzer=Depends(get_query_analyzer),
    strategy_builder=Depends(get_strategy_builder),
    iterator=Depends(get_iterator),
    conversation_repo=Depends(get_conversation_repo),
    parent_chunk_repo=Depends(get_parent_chunk_repo),
    cache=Depends(get_cache),
    settings=Depends(get_settings),
):
    """
    Create RAGOrchestrator instance with adaptive capabilities.

    Note: Adaptive components are always injected for simplicity,
    but only used when settings.adaptive_mode=True.
    cache_service=None when Redis is unavailable (caching disabled gracefully).
    """
    return RAGOrchestrator(
        retriever=retriever,
        generator=generator,
        query_analyzer=query_analyzer,
        strategy_builder=strategy_builder,
        iterator=iterator,
        conversation_repo=conversation_repo,
        parent_chunk_repo=parent_chunk_repo,
        cache_service=cache,  # None if Redis unavailable
        adaptive_mode=settings.adaptive_mode,
        iterative_mode=settings.iterative_mode,
        agentic_mode=settings.agentic_mode,
        max_iterations=settings.max_iterations,
    )
