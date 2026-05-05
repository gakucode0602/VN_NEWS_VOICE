import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Info

from app.api.v1.router import router
from app.config.settings import get_settings
from app.utils.limiter import limiter

# Initialize settings (this will setup logging automatically)
settings = get_settings()

# Get logger for main module
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: load embedding model in background thread, then start IndexingWorker
    and connect to RabbitMQ fanout consumer — app is ready immediately.
    Shutdown: close AMQP connection gracefully.
    """
    app.state.amqp_connection = None

    async def _load_and_start():
        try:
            from app.api.deps import get_embedder, get_vector_store
            from app.core.indexing.chunker import Chunker
            from workers.indexing_workers import IndexingWorker
            from app.services.article_event_consumer import start_fanout_consumer

            logger.info("[Startup] Loading embedding model in background...")
            # Run blocking model load in a thread so the event loop stays free
            embedder = await asyncio.to_thread(get_embedder)
            logger.info("[Startup] Embedding model loaded successfully")

            vector_store = get_vector_store()
            chunker = Chunker()
            worker = IndexingWorker(
                chunker=chunker,
                embedder=embedder,
                vector_store=vector_store,
                parent_chunk_repository=None,  # session created per flush internally
                async_loop=asyncio.get_event_loop(),
            )

            app.state.amqp_connection = await start_fanout_consumer(
                settings.rabbitmq_url, worker
            )
            logger.info("[AMQP] Fanout consumer started for article.events.rag-service")

        except Exception:
            logger.exception(
                "[AMQP] Could not start fanout consumer — RAG continues in HTTP-only mode"
            )

    asyncio.create_task(_load_and_start())
    logger.info("[Startup] App is ready — model loading in background")

    yield  # app is running

    if app.state.amqp_connection and not app.state.amqp_connection.is_closed:
        await app.state.amqp_connection.close()
        logger.info("[AMQP] Connection closed")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    redirect_slashes=False,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

_app_info = Info("fastapi_app", "FastAPI application information")
_app_info.info({"app_name": settings.app_name})

Instrumentator().instrument(app)


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


logger.info("FastAPI application initialized")
logger.info("API docs available at: /docs")


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "amqp": "consuming article.events.rag-service (fanout)",
    }
