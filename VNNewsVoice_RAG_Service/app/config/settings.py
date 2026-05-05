import logging
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    app_name: str = "VN News Voice - RAG"
    debug: bool = Field(..., alias="DEBUG_MODE")

    # LLM PROVIDER
    llm_provider: str = Field(..., alias="LLM_PROVIDER")
    ollama_base_url: str = Field(..., alias="OLLAMA_BASE_URL")
    ollama_model_name: str = Field(..., alias="OLLAMA_MODEL_NAME")

    # Embedding
    embedding_provider: str = Field(..., alias="EMBEDDING_PROVIDER")
    embedding_dimension: int = Field(..., alias="EMBEDDING_DIMENSION")
    dense_local_embed_model_name: str = Field(..., alias="DENSE_LOCAL_EMBED_MODEL_NAME")
    sparse_local_embed_model_name: str = Field(
        ..., alias="SPARSE_LOCAL_EMBED_MODEL_NAME"
    )

    # Vector database
    qdrant_host: str = Field(..., alias="QDRANT_HOST")
    qdrant_port: int = Field(..., alias="QDRANT_PORT")
    qdrant_collection_name: str = Field(..., alias="QDRANT_COLLECTION_NAME")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")

    # API Config
    api_host: str = Field(..., alias="API_HOST")
    api_port: int = Field(..., alias="API_PORT")

    # Logging
    log_level: str = Field(..., alias="LOG_LEVEL")

    # RAG Configuration
    adaptive_mode: bool = Field(default=False, alias="ADAPTIVE_MODE")
    iterative_mode: bool = Field(default=False, alias="ITERATIVE_MODE")
    agentic_mode: bool = Field(default=False, alias="AGENTIC_MODE")
    max_iterations: int = Field(..., alias="MAX_ITERATIONS")

    # Redis Cache Configuration
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_ttl_seconds: int = Field(default=3600, alias="REDIS_TTL_SECONDS")  # 1 hour

    # Gemini Configuration
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model_name: str = Field(
        default="gemini-3-flash-preview", alias="GEMINI_MODEL_NAME"
    )

    # NVIDIA Configuration
    nvidia_base_url: str = Field(default="", alias="NVIDIA_BASE_URL")
    nvidia_api_key: str = Field(default="", alias="NVIDIA_API_KEY")
    nvidia_model_name: str = Field(
        default="meta/llama-3.1-8b-instruct", alias="NVIDIA_MODEL_NAME"
    )

    # Rabbit MQ Configuration
    rabbitmq_url: str = Field(..., alias="RABBITMQ_URL")

    # Database conversation url
    database_url: str = Field(..., alias="DATABASE_URL")

    # Spring Boot Backend URL (for reindex — RAG calls /api/articles/export)
    backend_base_url: str = Field(
        default="http://localhost:8080", alias="BACKEND_BASE_URL"
    )

    # Authentication Info
    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    jwt_expiration: int = Field(default=86400000, alias="JWT_EXPIRATION")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_issuer: str = Field(default="vnnewsvoice-auth-service", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="vnnewsvoice-services", alias="JWT_AUDIENCE")
    jwt_allow_legacy_hs256: bool = Field(default=True, alias="JWT_ALLOW_LEGACY_HS256")
    jwt_verify_issuer_audience: bool = Field(
        default=True, alias="JWT_VERIFY_ISSUER_AUDIENCE"
    )

    # Auth JWKS (for RS256 verification)
    auth_jwks_url: str = Field(
        default="http://localhost:8084/api/.well-known/jwks.json",
        alias="AUTH_JWKS_URL",
    )
    auth_jwks_timeout_seconds: float = Field(
        default=2.0, alias="AUTH_JWKS_TIMEOUT_SECONDS"
    )
    auth_jwks_cache_lifespan_seconds: int = Field(
        default=900, alias="AUTH_JWKS_CACHE_LIFESPAN_SECONDS"
    )
    auth_jwks_cache_refresh_seconds: int = Field(
        default=300, alias="AUTH_JWKS_CACHE_REFRESH_SECONDS"
    )

    # Claude Configuration
    claude_api_key: str = Field(default="", alias="CLAUDE_API_KEY")
    claude_model_name: str = Field(
        default="claude-sonnet-4-20250514", alias="CLAUDE_MODEL_NAME"
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(ROOT_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings():
    settings = Settings()

    # Setup logging when settings are initialized
    from app.config.logging import setup_logging

    setup_logging(settings.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Settings loaded successfully")
    logger.info("LLM Provider: %s", settings.llm_provider)
    logger.info(
        "RAG Mode: %s",
        "Adaptive"
        if settings.adaptive_mode
        else "Iterative"
        if settings.iterative_mode
        else "Agentic",
    )

    return settings
