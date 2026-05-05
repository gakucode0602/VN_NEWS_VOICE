"""
Redis-based cache service for Query Analysis results
Reduces query analysis latency from 2-3s to <10ms for repeated queries
"""

import hashlib
import json
import logging
from typing import List, Optional
from datetime import timedelta

import redis
from pydantic import BaseModel

from app.models.domain.conversation import ConversationTurn
from app.models.domain.query import QueryAnalysis
from app.models.domain.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


class CacheStats(BaseModel):
    """Cache statistics"""

    hits: int = 0
    misses: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class RedisQueryCache:
    """Redis-based cache for QueryAnalysis results"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        ttl_seconds: int = 3600,  # 1 hour default
        password: Optional[str] = None,
        key_prefix: str = "query_analysis:",
        retrieval_ttl_seconds: int = 1800,
        retrieval_key_prefix: str = "retrieval:",
        conversation_key_prefix: str = "conversation:",
        conversation_ttl_seconds: int = 86400,
    ):
        """
        Initialize Redis cache

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            ttl_seconds: Time-to-live for cached entries
            key_prefix: Prefix for all cache keys
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        self.ttl = timedelta(seconds=ttl_seconds)
        self.key_prefix = key_prefix
        self.stats = CacheStats()
        self.retrieval_ttl = timedelta(seconds=retrieval_ttl_seconds)
        self.retrieval_key_prefix = retrieval_key_prefix
        self.conversation_key_prefix = conversation_key_prefix
        self.conversation_ttl = timedelta(seconds=conversation_ttl_seconds)

        # Test connection
        try:
            self.client.ping()
            logger.info(f"Redis cache connected: {host}:{port} (TTL: {ttl_seconds}s)")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for consistent cache keys
        - Lowercase
        - Strip whitespace
        - Collapse multiple spaces
        """
        return " ".join(query.lower().strip().split())

    def _generate_cache_key(self, query: str) -> str:
        """Generate MD5 hash cache key from normalized query"""
        normalized = self._normalize_query(query)
        hash_obj = hashlib.md5(normalized.encode("utf-8"))
        return f"{self.key_prefix}{hash_obj.hexdigest()}"

    def _normalize_retrieval_results(
        self, retrieval_results: List[RetrievalResult]
    ) -> str:
        """Serialize RetrievalResult list to JSON string for caching."""
        return json.dumps(
            [r.model_dump(mode="json") for r in retrieval_results],
            ensure_ascii=False,
        )

    def _generate_retrieval_cache_key(self, query: str) -> str:
        """Generate MD5 hash cache key for retrieval results."""
        normalized = self._normalize_query(query)
        hash_obj = hashlib.md5(normalized.encode("utf-8"))
        return f"{self.retrieval_key_prefix}{hash_obj.hexdigest()}"

    def _normalized_conversation_turn(
        self, conversation_turns: List[ConversationTurn]
    ) -> str:
        return json.dumps(
            [turn.model_dump(mode="json") for turn in conversation_turns],
            ensure_ascii=True,
        )

    def _generate_conversation_cache_key(
        self, conversation_id: str, user_id: str
    ) -> str:
        if conversation_id is None:
            return None
        normalized = f"{conversation_id.strip()}-{user_id.strip()}"
        hash_obj = hashlib.md5(normalized.encode("utf-8"))
        return f"{self.conversation_key_prefix}{hash_obj.hexdigest()}"

    def get(self, query: str) -> Optional[QueryAnalysis]:
        """
        Retrieve cached QueryAnalysis

        Args:
            query: User query

        Returns:
            Cached QueryAnalysis if found, None otherwise
        """
        cache_key = self._generate_cache_key(query)

        try:
            cached_json = self.client.get(cache_key)

            if cached_json is None:
                self.stats.misses += 1
                logger.debug(f"Cache MISS: {query[:50]}...")
                return None

            # Deserialize
            cached_data = json.loads(cached_json)
            analysis = QueryAnalysis(**cached_data)

            self.stats.hits += 1
            logger.debug(
                f"Cache HIT: {query[:50]}... (TTL: {self.client.ttl(cache_key)}s)"
            )

            return analysis

        except (redis.RedisError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Cache get error: {e}")
            self.stats.misses += 1
            return None

    def set(self, query: str, analysis: QueryAnalysis) -> bool:
        """
        Cache QueryAnalysis result

        Args:
            query: User query
            analysis: QueryAnalysis to cache

        Returns:
            True if cached successfully
        """
        cache_key = self._generate_cache_key(query)

        try:
            # Serialize QueryAnalysis to JSON
            analysis_json = analysis.model_dump_json()

            # Set with TTL
            self.client.setex(cache_key, self.ttl, analysis_json)

            logger.debug(
                f"Cache SET: {query[:50]}... (TTL: {self.ttl.total_seconds()}s)"
            )
            return True

        except (redis.RedisError, ValueError) as e:
            logger.error(f"Cache set error: {e}")
            return False

    def clear(self) -> int:
        """
        Clear all query analysis, retrieval, and conversation cache entries

        Returns:
            Number of keys deleted
        """
        try:
            deleted_count = 0
            prefixes = [
                self.key_prefix,
                self.retrieval_key_prefix,
                self.conversation_key_prefix,
            ]

            for prefix in prefixes:
                pattern = f"{prefix}*"
                # Retrieve all keys matching the prefix
                keys = list(self.client.scan_iter(match=pattern, count=100))

                if keys:
                    deleted_count += self.client.delete(*keys)

            logger.info(f"Cache cleared: {deleted_count} keys deleted")
            return deleted_count

        except redis.RedisError as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.stats

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = CacheStats()
        logger.info("Cache stats reset")

    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            return self.client.ping()
        except redis.RedisError:
            return False

    def set_cache_retrieval(self, query: str, results: List[RetrievalResult]) -> bool:
        """Cache retrieval results for a query."""
        cache_key = self._generate_retrieval_cache_key(query)
        try:
            results_json = self._normalize_retrieval_results(results)
            # Use retrieval_ttl (30 min), NOT query analysis ttl (1 hour)
            self.client.setex(cache_key, self.retrieval_ttl, results_json)
            logger.debug(
                f"Retrieval Cache SET: {query[:50]}... (TTL: {self.retrieval_ttl.total_seconds()}s)"
            )
            return True
        except (redis.RedisError, ValueError) as e:
            logger.error(f"Retrieval cache set error: {e}")
            return False

    def get_cached_retrieval(self, query: str) -> Optional[List[RetrievalResult]]:
        cache_key = self._generate_retrieval_cache_key(query)
        try:
            cached_json = self.client.get(cache_key)

            if cached_json is None:
                self.stats.misses += 1
                logger.debug(f"Retrieval Cache MISS: {query[:50]}...")
                return None

            # Deserialize back to List[RetrievalResult]
            cached_data = json.loads(cached_json)
            results = [RetrievalResult(**item) for item in cached_data]

            self.stats.hits += 1
            logger.debug(
                f"Retrieval Cache HIT: {query[:50]}... (TTL: {self.client.ttl(cache_key)}s)"
            )
            return results

        except (redis.RedisError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Retrieval cache get error: {e}")
            self.stats.misses += 1
            return None

    def get_cached_conversation(
        self, conversation_id: str | None, user_id: str
    ) -> Optional[List[ConversationTurn]]:
        if conversation_id is None:
            return None
        cached_key = self._generate_conversation_cache_key(conversation_id, user_id)

        try:
            cached_json = self.client.get(cached_key)

            if cached_json is None:
                self.stats.misses += 1
                logger.debug(f"Cache MISS: {conversation_id}-{user_id}")
                return None
            cached_data = json.loads(cached_json)

            results = [ConversationTurn(**item) for item in cached_data]

            return results

        except (redis.RedisError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Cache get error: {e}")
            self.stats.misses += 1
            return None

    def set_cached_conversation(
        self,
        conversation_id: str | None,
        user_id: str,
        conversation_turns: List[ConversationTurn],
    ) -> bool:
        cache_key = self._generate_conversation_cache_key(conversation_id, user_id)
        try:
            results_json = self._normalized_conversation_turn(conversation_turns)
            self.client.setex(cache_key, self.conversation_ttl, results_json)
            return True
        except (redis.RedisError, ValueError) as e:
            logger.error(f"Cache set error: {e}")
            return False
