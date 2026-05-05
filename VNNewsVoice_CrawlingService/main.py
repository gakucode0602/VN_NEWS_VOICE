import logging
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.consumer.crawl_task_consumer import CrawlTaskConsumer
from app.publisher.ml_task_publisher import MlTaskPublisher

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:
      - Connect RabbitMQ
      - Declare queues
      - Start consuming crawl.task
    Shutdown:
      - Stop consumer
      - Close channel and connection
    """
    app.state.rabbitmq_ready = False
    app.state.rabbitmq_error = None
    app.state.rabbitmq_connection = None
    app.state.rabbitmq_channel = None
    app.state.crawl_queue = None
    app.state.crawl_dlq = None
    app.state.consumer_tag = None

    try:
        logger.info("CrawlingService starting")
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        dlx_exchange = await channel.declare_exchange(
            settings.crawl_task_dlx_exchange,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )
        crawl_dlq = await channel.declare_queue(settings.crawl_task_dlq, durable=True)
        await crawl_dlq.bind(
            dlx_exchange, routing_key=settings.crawl_task_dlq_routing_key
        )

        crawl_queue = await channel.declare_queue(
            settings.crawl_task_queue,
            durable=True,
            arguments={
                "x-dead-letter-exchange": settings.crawl_task_dlx_exchange,
                "x-dead-letter-routing-key": settings.crawl_task_dlq_routing_key,
            },
        )
        await MlTaskPublisher.declare_queue(channel)

        publisher = MlTaskPublisher(channel)
        consumer = CrawlTaskConsumer(publisher)
        consumer_tag = await crawl_queue.consume(consumer.handle_message, no_ack=False)

        app.state.rabbitmq_ready = True
        app.state.rabbitmq_connection = connection
        app.state.rabbitmq_channel = channel
        app.state.crawl_queue = crawl_queue
        app.state.crawl_dlq = crawl_dlq
        app.state.consumer_tag = consumer_tag

        logger.info(
            "Consuming '%s' -> publishing '%s' (DLQ: '%s')",
            settings.crawl_task_queue,
            settings.ml_tasks_queue,
            settings.crawl_task_dlq,
        )
    except Exception as exc:
        app.state.rabbitmq_error = str(exc)
        logger.exception("RabbitMQ startup failed")

    yield

    try:
        if app.state.crawl_queue is not None and app.state.consumer_tag is not None:
            await app.state.crawl_queue.cancel(app.state.consumer_tag)
    except Exception:
        logger.debug("Failed to cancel consumer cleanly", exc_info=True)

    if (
        app.state.rabbitmq_channel is not None
        and not app.state.rabbitmq_channel.is_closed
    ):
        await app.state.rabbitmq_channel.close()
    if (
        app.state.rabbitmq_connection is not None
        and not app.state.rabbitmq_connection.is_closed
    ):
        await app.state.rabbitmq_connection.close()

    logger.info("CrawlingService shutdown complete")


app = FastAPI(
    title="VNNewsVoice Crawling Service",
    description="Queue-only crawl worker: consume crawl.task and publish ml.tasks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {
        "message": "VNNewsVoice Crawling Service",
        "status": "running",
        "docs": "/docs",
        "pipeline": {
            "consume": settings.crawl_task_queue,
            "publish": settings.ml_tasks_queue,
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "rabbitmq": {
            "ready": bool(getattr(app.state, "rabbitmq_ready", False)),
            "error": getattr(app.state, "rabbitmq_error", None),
        },
        "queues": {
            "crawlTask": settings.crawl_task_queue,
            "crawlTaskDlq": settings.crawl_task_dlq,
            "mlTasks": settings.ml_tasks_queue,
        },
    }


@app.get("/ops/messaging")
async def messaging_status():
    return {
        "rabbitmqReady": bool(getattr(app.state, "rabbitmq_ready", False)),
        "rabbitmqError": getattr(app.state, "rabbitmq_error", None),
        "dlxExchange": settings.crawl_task_dlx_exchange,
        "consumeQueue": settings.crawl_task_queue,
        "deadLetterQueue": settings.crawl_task_dlq,
        "deadLetterRoutingKey": settings.crawl_task_dlq_routing_key,
        "publishQueue": settings.ml_tasks_queue,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
