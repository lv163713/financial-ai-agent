from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.mysql import LONGTEXT
from core.database import Base


class DailyRunJob(Base):
    __tablename__ = "daily_run_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")
    trigger_type = Column(String(20), nullable=False, default="manual", comment="触发方式")
    status = Column(String(20), nullable=False, default="pending", comment="任务状态")
    total = Column(Integer, nullable=False, default=0, comment="总数")
    success_count = Column(Integer, nullable=False, default=0, comment="成功数")
    failed_count = Column(Integer, nullable=False, default=0, comment="失败数")
    max_concurrency = Column(Integer, nullable=False, default=3, comment="并发数")
    retry_times = Column(Integer, nullable=False, default=1, comment="重试次数")
    items_json = Column(LONGTEXT, nullable=True, comment="任务输入JSON")
    results_json = Column(LONGTEXT, nullable=True, comment="任务结果JSON")
    error_message = Column(String(1000), nullable=True, comment="失败原因")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="结束时间")
    created_at = Column(DateTime, default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="记录更新时间")
