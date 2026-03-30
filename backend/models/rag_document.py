from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import LONGTEXT
from core.database import Base


class RagDocument(Base):
    __tablename__ = "rag_documents"
    __table_args__ = (
        UniqueConstraint("news_id", "chunk_id", name="uq_rag_news_chunk"),
        Index("idx_rag_published_at", "published_at"),
        Index("idx_rag_market", "market"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    news_id = Column(Integer, nullable=False, index=True)
    chunk_id = Column(Integer, nullable=False)
    content = Column(LONGTEXT, nullable=False)
    embedding = Column(LONGTEXT, nullable=False)
    source = Column(String(100), nullable=True)
    published_at = Column(DateTime, nullable=True)
    market = Column(String(20), nullable=True)
    sectors = Column(String(255), nullable=True)
    ingest_time = Column(DateTime, default=func.now(), nullable=False)
