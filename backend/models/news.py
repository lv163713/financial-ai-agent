from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.mysql import LONGTEXT
from core.database import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")
    title = Column(String(255), nullable=False, comment="新闻标题")
    url = Column(String(512), unique=True, nullable=False, comment="新闻原文链接")
    source = Column(String(50), nullable=True, comment="新闻来源，如：雅虎财经")
    content_md = Column(LONGTEXT, nullable=True, comment="抓取后转换的Markdown正文")
    publish_time = Column(DateTime, nullable=True, comment="新闻发布时间")
    
    created_at = Column(DateTime, default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="记录更新时间")
