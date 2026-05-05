import logging
import httpx
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, BackgroundTasks, status

from app.api.deps import require_admin, get_cache, get_embedder, get_vector_store
from app.core.indexing.chunker import Chunker
from app.config.settings import get_settings
from app.services.cache_service import RedisQueryCache
from workers.indexing_workers import IndexingWorker

router = APIRouter(
    prefix="/admin", tags=["ADMIN"], dependencies=[Depends(require_admin)]
)
logger = logging.getLogger(__name__)


@router.post("/cache/clean", status_code=status.HTTP_200_OK)
def clear_redis_cache(cache: RedisQueryCache = Depends(get_cache)):
    cleared_count = cache.clear()
    return {"message": "Cache cleared successfully", "cleared_keys": cleared_count}


@router.get("/metrics", status_code=status.HTTP_200_OK)
def get_system_metrics(cache: RedisQueryCache = Depends(get_cache)):
    return {
        "hits": cache.stats.hits,
        "misses": cache.stats.misses,
        "hit_rate": cache.stats.hit_rate,
    }


async def run_reindex_background_job(since: Optional[datetime] = None):
    """
    Background worker: pull articles from Spring Boot backend and index into Qdrant + Postgres.

    - since=None  → Full Reindex: clear Qdrant + Postgres trước, sau đó index lại tất cả
    - since=<dt>  → Delta Sync: chỉ index bài mới/cập nhật sau mốc thời gian đó
    """
    settings = get_settings()
    backend_url = settings.backend_base_url
    export_url = f"{backend_url}/api/articles/export"

    # Build IndexingWorker từ các cached deps (không dùng FastAPI DI vì background task)
    # NOTE: parent_chunk_repository=None vì _flush_to_postgres() tự tạo AsyncSessionLocal
    #       riêng — nó không dùng self.parent_chunk_repository.
    embedder = get_embedder()
    vector_store = get_vector_store()
    chunker = Chunker()
    worker = IndexingWorker(
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        parent_chunk_repository=None,
    )

    try:
        if since:
            # Delta Sync — chỉ kéo bài mới
            logger.info(
                f"[DELTA SYNC] Started. Pulling articles since: {since.isoformat()}"
            )
            # Đảm bảo UTC timezone — Python datetime có thể là naive (không có tzinfo)
            # nếu user pass "2026-01-26" thì FastAPI parse thành naive datetime
            # since.isoformat() → "2026-01-26T00:00:00" ← thiếu Z, Java sẽ crash!
            # Fix: attach UTC trước khi gọi isoformat()
            since_utc = (
                since.replace(tzinfo=timezone.utc) if since.tzinfo is None else since
            )
            params = {"since": since_utc.strftime("%Y-%m-%dT%H:%M:%SZ")}
        else:
            # Full Reindex:
            # 1. Xóa Qdrant collection
            logger.info(
                "[FULL REINDEX] Started. Clearing Qdrant collection + Postgres parent_chunks..."
            )
            try:
                vector_store.client.delete_collection(
                    collection_name=vector_store.collection_name
                )
                logger.info("[FULL REINDEX] Qdrant collection cleared.")
                vector_store._ensure_collection()  # recreate empty collection
            except Exception as e:
                logger.warning(
                    f"[FULL REINDEX] Could not clear Qdrant collection: {e}. Proceeding."
                )

            # 2. Truncate PostgreSQL parent_chunks để tránh stale data
            try:
                from app.config.database import AsyncSessionLocal
                from app.repositories.parent_chunk_repository import (
                    ParentChunkRepository,
                )

                async with AsyncSessionLocal() as session:
                    repo = ParentChunkRepository(session)
                    await repo.delete_all()
                logger.info("[FULL REINDEX] Postgres parent_chunks truncated.")
            except Exception as e:
                logger.warning(
                    f"[FULL REINDEX] Could not truncate Postgres parent_chunks: {e}. Proceeding."
                )

            params = {}

        # Paginated HTTP GET → loop cho đến khi backend trả về result rỗng
        # Mỗi page 200 bài → tránh OOM dù có 1 triệu bài
        PAGE_SIZE = 200
        page = 1
        success_count = 0
        fail_count = 0

        async with httpx.AsyncClient(timeout=60.0) as client:
            while True:
                paged_params = {**params, "page": page, "size": PAGE_SIZE}
                response = await client.get(export_url, params=paged_params)
                response.raise_for_status()
                data = response.json()

                articles = data.get("result", [])
                if not articles:
                    break  # hết data — dừng loop

                logger.info(
                    f"[REINDEX] Page {page}: fetched {len(articles)} articles. Indexing..."
                )

                for article_detail in articles:
                    try:
                        # Format: { "result": { "article": {...}, "blocks": [...] } }
                        # _flush_to_postgres() tự save parent_chunks vào Postgres
                        worker.index_article({"result": article_detail})
                        success_count += 1
                    except Exception as e:
                        article_id = article_detail.get("article", {}).get("id", "?")
                        logger.error(
                            f"[REINDEX] Failed to index article id={article_id}: {e}"
                        )
                        fail_count += 1

                page += 1

        mode = "DELTA SYNC" if since else "FULL REINDEX"
        total = success_count + fail_count
        logger.info(
            f"[{mode}] Completed. Success: {success_count}/{total}, Failed: {fail_count}/{total}"
        )

    except httpx.RequestError as e:
        logger.error(f"[REINDEX] Cannot connect to backend at {export_url}: {e}")
    except Exception as e:
        logger.error(f"[REINDEX] Job failed unexpectedly: {e}", exc_info=True)


@router.post("/reindex", status_code=status.HTTP_202_ACCEPTED)
async def trigger_reindex(
    background_tasks: BackgroundTasks, since: Optional[datetime] = None
):
    """
    Trigger a background job to sync articles from the Core DB to Vector DB.
    - If `since` is provided: Delta Sync (Pull only missed items).
    - If `since` is omitted: Full Reindex (Wipe and recreate everything).
    """
    background_tasks.add_task(run_reindex_background_job, since)

    mode = "Delta Sync" if since else "Full Reindex"
    return {
        "message": f"{mode} background task has been scheduled.",
        "status": "processing",
        "since": since.isoformat() if since else "Beginning of time",
    }
