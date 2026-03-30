from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base
from models.news import News


class IngestAuditLog(Base):
    __tablename__ = "ingest_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")
    url = Column(String(512), nullable=False, comment="任务URL")
    source = Column(String(50), nullable=True, comment="来源")
    success = Column(Boolean, nullable=False, default=False, comment="是否成功")
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")
    error_message = Column(String(1000), nullable=True, comment="失败原因")
    news_id = Column(Integer, ForeignKey("news.id", ondelete="SET NULL"), nullable=True, comment="关联新闻ID")
    started_at = Column(DateTime, nullable=False, default=func.now(), comment="开始时间")
    finished_at = Column(DateTime, nullable=False, default=func.now(), comment="结束时间")
    created_at = Column(DateTime, default=func.now(), comment="记录创建时间")

    news = relationship("News", backref="ingest_audit_logs")
