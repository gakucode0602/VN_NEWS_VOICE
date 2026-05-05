import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import aio_pika
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.messaging.consumer import MlTaskConsumer
from app.messaging.publisher import ArticleEventsPublisher
from app.messaging.video_task_consumer import VideoTaskConsumer

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rabbitmq_ready = False
    app.state.rabbitmq_error = None
    app.state.connection = None
    app.state.channel = None
    app.state.consumer_tag = None
    app.state.video_consumer_tag = None

    if not settings.RABBITMQ_URL:
        app.state.rabbitmq_error = "RABBITMQ_URL is not configured"
        logger.warning("RABBITMQ_URL is empty - worker started in degraded mode")
        yield
        return

    try:
        logger.info("ML worker starting")
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=settings.AMQP_PREFETCH_COUNT)

        await ArticleEventsPublisher.declare_infrastructure(channel)
        ml_queue = await channel.declare_queue(settings.ML_TASKS_QUEUE, durable=True)

        publisher = ArticleEventsPublisher(channel)

        # Consumer 1: ml.tasks (article crawl pipeline)
        consumer = MlTaskConsumer(publisher)
        consumer_tag = await ml_queue.consume(consumer.handle_message, no_ack=False)

        # Consumer 2: ml.video.tasks (Veo video generation)
        video_queue = await channel.declare_queue(
            settings.ML_VIDEO_TASKS_QUEUE, durable=True
        )
        video_consumer = VideoTaskConsumer(publisher)
        video_consumer_tag = await video_queue.consume(
            video_consumer.handle_message, no_ack=False
        )

        app.state.rabbitmq_ready = True
        app.state.connection = connection
        app.state.channel = channel
        app.state.consumer_tag = consumer_tag
        app.state.video_consumer_tag = video_consumer_tag
        app.state.ml_queue = ml_queue
        app.state.video_queue = video_queue

        logger.info(
            "Consuming '%s' + '%s', publishing to '%s' fanout",
            settings.ML_TASKS_QUEUE,
            settings.ML_VIDEO_TASKS_QUEUE,
            settings.ARTICLE_EVENTS_EXCHANGE,
        )
    except Exception as exc:
        app.state.rabbitmq_error = str(exc)
        logger.exception("AMQP startup failed")

    yield

    try:
        if app.state.ml_queue is not None and app.state.consumer_tag is not None:
            await app.state.ml_queue.cancel(app.state.consumer_tag)
    except Exception:
        logger.debug("Failed to cancel ml consumer cleanly", exc_info=True)

    try:
        if (
            getattr(app.state, "video_queue", None) is not None
            and app.state.video_consumer_tag is not None
        ):
            await app.state.video_queue.cancel(app.state.video_consumer_tag)
    except Exception:
        logger.debug("Failed to cancel video consumer cleanly", exc_info=True)

    if app.state.channel is not None and not app.state.channel.is_closed:
        await app.state.channel.close()
    if app.state.connection is not None and not app.state.connection.is_closed:
        await app.state.connection.close()

    logger.info("ML worker shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
        "pipeline": {
            "consume": settings.ML_TASKS_QUEUE,
            "publish": settings.ARTICLE_EVENTS_EXCHANGE,
        },
    }


@app.get("/health")
async def health_check():
    from app.services.text_summarization import ArticleSummarizationService

    adapter_present = Path(settings.ADAPTER_PATH).exists()
    return {
        "status": "healthy",
        "rabbitmq": {
            "ready": bool(getattr(app.state, "rabbitmq_ready", False)),
            "error": getattr(app.state, "rabbitmq_error", None),
        },
        "pipeline": {
            "consumeQueue": settings.ML_TASKS_QUEUE,
            "publishExchange": settings.ARTICLE_EVENTS_EXCHANGE,
        },
        "ml": {
            "adapterPath": settings.ADAPTER_PATH,
            "adapterPresent": adapter_present,
            "adapterLoaded": ArticleSummarizationService._model is not None,
            "adapterActive": ArticleSummarizationService._adapter_loaded,
            "mlflowUri": settings.MLFLOW_TRACKING_URI,
        },
    }


def _sync_adapter_from_minio() -> bool:
    """Sync adapter files from MinIO to local ADAPTER_PATH using boto3.

    Returns True if sync was performed, False if MINIO_ENDPOINT_URL is not set
    (i.e. running locally where dvc pull already handled it).
    """
    endpoint_url = os.getenv("MINIO_ENDPOINT_URL")
    if not endpoint_url:
        return False

    import boto3

    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    bucket = os.getenv("MINIO_BUCKET", "vnnewsvoice-models")
    prefix = "vit5-qlora-adapter"

    local_dir = Path(settings.ADAPTER_PATH)
    local_dir.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    paginator = s3.get_paginator("list_objects_v2")
    downloaded = 0
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix + "/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel = key[len(prefix) + 1 :]  # strip "vit5-qlora-adapter/" prefix
            if not rel:
                continue
            local_path = local_dir / rel
            local_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("[reload] Downloading %s → %s", key, local_path)
            s3.download_file(bucket, key, str(local_path))
            downloaded += 1

    logger.info("[reload] MinIO sync complete: %d files → %s", downloaded, local_dir)
    return True


@app.post("/admin/reload-model")
async def reload_model(x_admin_secret: str = Header(default="")):
    expected = os.getenv("ADMIN_SECRET", "")
    if expected and x_admin_secret != expected:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    from app.services.text_summarization import ArticleSummarizationService

    # When running on RunPod (or any containerised env), pull the latest adapter
    # from MinIO before reloading.  On local/Hetzner the self-hosted runner already
    # ran `dvc pull`, so MINIO_ENDPOINT_URL is not set and we skip the sync.
    try:
        synced = await asyncio.to_thread(_sync_adapter_from_minio)
        if synced:
            logger.info("[reload] Adapter synced from MinIO.")
    except Exception as exc:
        logger.error("MinIO sync failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"MinIO sync failed: {exc}")

    try:
        await asyncio.to_thread(ArticleSummarizationService.cleanup_model)
        await asyncio.to_thread(ArticleSummarizationService._load_model)
        model_type = type(ArticleSummarizationService._model).__name__
        return {"status": "ok", "modelType": model_type, "syncedFromMinIO": synced}
    except Exception as exc:
        logger.error("Model reload failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


def _push_training_data_to_minio() -> dict:
    """Upload SAPO_DATA_PATH (pairs.jsonl) to MinIO for centralized storage.

    Returns a dict with upload stats.  Raises RuntimeError if env vars are missing
    or the file does not exist.
    """
    endpoint_url = os.getenv("MINIO_ENDPOINT_URL")
    if not endpoint_url:
        raise RuntimeError("MINIO_ENDPOINT_URL is not set — cannot push training data")

    data_path = Path(settings.SAPO_DATA_PATH)
    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found: {data_path}")

    import boto3

    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    bucket = os.getenv("MINIO_BUCKET", "vnnewsvoice-models")
    s3_key = "training-data/pairs.jsonl"

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    file_size = data_path.stat().st_size
    line_count = sum(1 for _ in data_path.open(encoding="utf-8"))

    s3.upload_file(str(data_path), bucket, s3_key)
    logger.info(
        "[push-data] Uploaded %s (%d lines, %d bytes) → s3://%s/%s",
        data_path,
        line_count,
        file_size,
        bucket,
        s3_key,
    )

    return {
        "lines": line_count,
        "bytes": file_size,
        "destination": f"s3://{bucket}/{s3_key}",
    }


@app.post("/admin/push-training-data")
async def push_training_data(x_admin_secret: str = Header(default="")):
    expected = os.getenv("ADMIN_SECRET", "")
    if expected and x_admin_secret != expected:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    try:
        result = await asyncio.to_thread(_push_training_data_to_minio)
        return {"status": "ok", **result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Push training data failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/ops/messaging")
async def messaging_status():
    return {
        "rabbitmqReady": bool(getattr(app.state, "rabbitmq_ready", False)),
        "rabbitmqError": getattr(app.state, "rabbitmq_error", None),
        "consumeQueues": [settings.ML_TASKS_QUEUE, settings.ML_VIDEO_TASKS_QUEUE],
        "publishExchange": settings.ARTICLE_EVENTS_EXCHANGE,
    }


class VideoGenerateRequest(BaseModel):
    article_id: str
    title: str
    top_image_url: Optional[str] = None
    summary: Optional[str] = None
    model: Optional[str] = None
    duration_seconds: Optional[int] = None
    """Video duration in seconds. veo-2: 5 | 6 | 8. veo-3.1: 4 | 6 | 8. Default: 8."""
    video_style: Optional[str] = None
    """Style preset: news | animation | 3d | cinematic | documentary | watercolor | drone | timelapse. Default: news."""


@app.post("/ops/generate-video")
async def ops_generate_video(request: VideoGenerateRequest):
    """
    Trigger Veo video generation for a given article (demo/test endpoint).
    Blocking up to 6 minutes while Veo processes. Returns Cloudinary video URL.
    """
    from app.services.video_generation_service import VideoGenerationService

    logger.info(
        "ops/generate-video called: article_id=%s title=%s",
        request.article_id,
        request.title[:60],
    )

    result = await asyncio.to_thread(
        VideoGenerationService.generate_and_upload,
        request.article_id,
        request.title,
        request.top_image_url,
        request.summary,
        request.model,
        request.duration_seconds,
        request.video_style,
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Video generation failed. Check service logs for details.",
        )

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
