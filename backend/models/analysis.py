from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base

class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, comment="关联的新闻ID")
    
    summary = Column(String(500), nullable=False, comment="事件一句话摘要")
    impact_assessment = Column(String(20), nullable=False, comment="影响评估: 利好/利空/中性")
    affected_sectors = Column(String(255), nullable=True, comment="受影响板块(逗号分隔)")
    logical_reasoning = Column(Text, nullable=True, comment="逻辑推演过程")
    
    created_at = Column(DateTime, default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="记录更新时间")
    
    # 定义关联关系
    news = relationship("News", backref="analysis")