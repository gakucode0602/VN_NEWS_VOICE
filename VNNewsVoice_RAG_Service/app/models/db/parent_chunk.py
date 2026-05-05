from sqlalchemy import Column, Integer, String, Text
from app.models.db.base import Base


class ParentChunk(Base):
    __tablename__ = "parent_chunks"
    id = Column(String, primary_key=True, index=True)
    article_id = Column(String, index=True)
    content = Column(Text)
    chunk_index = Column(Integer)
