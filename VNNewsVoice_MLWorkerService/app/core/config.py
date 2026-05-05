from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "VNNewsVoice ML Worker Service"
    DESCRIPTION: str = "Queue-only worker for summarization and TTS"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # AMQP pipeline
    RABBITMQ_URL: Optional[str] = "amqp://admin:admin123@localhost:5672/"
    ML_TASKS_QUEUE: str = "ml.tasks"
    ML_VIDEO_TASKS_QUEUE: str = "ml.video.tasks"
    AMQP_PREFETCH_COUNT: int = 1
    ARTICLE_EVENTS_EXCHANGE: str = "article.events"

    # Google AI API keys — one per task quota group
    GOOGLE_AI_API_KEY: Optional[str] = None  # TTS (Gemini TTS provider)
    GOOGLE_AI_API_KEY_TS: Optional[str] = None  # Text summarization
    GOOGLE_AI_API_KEY_VEO: Optional[str] = None  # Veo video generation
    HUGGINGFACE_API_KEY: Optional[str] = None
    TTS_PROVIDER: str = "gemini"
    TTS_MAX_INPUT_CHARS: int = 4000

    # Model + MLOps
    ADAPTER_PATH: str = "models/vit5-qlora-adapter"
    MLFLOW_ENABLED: bool = False
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "vit5-summarization"
    SAPO_DATA_PATH: str = "data/processed/pairs.jsonl"
    SAPO_AUTO_PUSH_THRESHOLD: int = (
        1000  # push to MinIO every N new pairs (0 = disabled)
    )

    # AWS S3 for audio
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None

    # Optional Cloudinary fallback fields (kept for compatibility)
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    # Veo video generation
    # veo-2.0-generate-001 requires GCP billing (Vertex AI only)
    # veo-3.1-generate-preview is the latest, works with standard Gemini API key
    VEO_MODEL: str = "veo-3.1-generate-preview"
    VEO_DURATION_SECONDS: int = 8  # Valid for veo-3.x: 4, 6, 8

    # CORS/ops API
    ALLOWED_HOSTS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
