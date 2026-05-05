from typing import List
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.parent_chunk import ParentChunk


class ParentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_all(self, chunks: List[ParentChunk]) -> None:
        self.session.add_all(instances=chunks)
        await self.session.commit()

    async def get_by_ids(self, chunk_ids: List[str]) -> List[ParentChunk]:
        stmt = select(ParentChunk).filter(ParentChunk.id.in_(chunk_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_article_id(self, article_id: str):
        stmt = delete(ParentChunk).where(ParentChunk.article_id == article_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_all(self):
        """Xóa toàn bộ parent_chunks — dùng khi Full Reindex để tránh stale data."""
        stmt = delete(ParentChunk)
        await self.session.execute(stmt)
        await self.session.commit()
