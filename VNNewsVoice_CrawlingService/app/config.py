from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # RabbitMQ
    rabbitmq_url: str = "amqp://admin:admin123@localhost:5672/"
    crawl_task_queue: str = "crawl.task"
    crawl_task_dlx_exchange: str = "crawl.task.dlx"
    crawl_task_dlq: str = "crawl.task.dlq"
    crawl_task_dlq_routing_key: str = "crawl.task.failed"
    ml_tasks_queue: str = "ml.tasks"

    # Publish resilience (ml.tasks)
    ml_publish_max_retries: int = 5
    ml_publish_backoff_initial_seconds: float = 0.5
    ml_publish_backoff_max_seconds: float = 8.0
    ml_publish_jitter_seconds: float = 0.25

    # Crawling limits
    max_articles_per_source: int = 5
    max_concurrent_crawlers: int = 3

    # Pre-ML duplicate guard (ArticleService claim)
    article_claim_enabled: bool = True
    article_claim_fail_open: bool = True
    article_service_base_url: str = Field(
        default="http://localhost:8080", env="ARTICLE_SERVICE_BASE_URL"
    )
    article_claim_endpoint: str = "/api/internal/articles/claim"
    article_claim_timeout_seconds: float = 2.5
    local_recent_url_cache_size: int = 5000

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
