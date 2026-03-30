import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from core.config import settings
from models.daily_run_job import DailyRunJob
from services.pipeline import run_batch_ingest_pipeline
from services.metrics import metrics_store
from core.logger import get_logger

logger = get_logger("services.daily_jobs")


def run_daily_job_now(
    db: Session,
    trigger_type: str,
    items: Optional[List[Dict[str, Optional[str]]]],
    max_concurrency: Optional[int] = None,
    retry_times: Optional[int] = None
) -> Dict[str, Any]:
    normalized_items = _normalize_items(items)
    if not normalized_items:
        raise ValueError("每日任务输入为空，请配置 DAILY_JOB_URLS 或在请求中传入 items。")
    job = DailyRunJob(
        trigger_type=trigger_type,
        status="pending",
        total=len(normalized_items),
        success_count=0,
        failed_count=0,
        max_concurrency=max_concurrency or settings.DAILY_JOB_MAX_CONCURRENCY,
        retry_times=retry_times if retry_times is not None else settings.DAILY_JOB_RETRY_TIMES,
        items_json=json.dumps(normalized_items, ensure_ascii=False)
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    try:
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        batch_result = run_batch_ingest_pipeline(
            db=db,
            items=normalized_items,
            max_concurrency=job.max_concurrency,
            retry_times=job.retry_times
        )
        job.status = "completed"
        job.total = int(batch_result.get("total", len(normalized_items)))
        job.success_count = int(batch_result.get("success_count", 0))
        job.failed_count = int(batch_result.get("failed_count", 0))
        job.results_json = json.dumps(batch_result.get("results", []), ensure_ascii=False)
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        metrics_store.record_daily_job(failed=False)
        return _serialize_job(job)
    except Exception as e:
        db.rollback()
        failed_job = db.query(DailyRunJob).filter(DailyRunJob.id == job.id).first()
        if failed_job:
            failed_job.status = "failed"
            failed_job.error_message = str(e)
            failed_job.finished_at = datetime.utcnow()
            db.commit()
            db.refresh(failed_job)
            metrics_store.record_daily_job(failed=True)
            logger.error(f"daily_job_failed job_id={failed_job.id} error={str(e)}")
            return _serialize_job(failed_job)
        raise


def get_daily_job_status(db: Session, job_id: int) -> Optional[Dict[str, Any]]:
    job = db.query(DailyRunJob).filter(DailyRunJob.id == job_id).first()
    if job is None:
        return None
    return _serialize_job(job)


def _normalize_items(items: Optional[List[Dict[str, Optional[str]]]]) -> List[Dict[str, Optional[str]]]:
    if items:
        return [{"url": str(item["url"]), "source": item.get("source")} for item in items if item.get("url")]
    urls = [url.strip() for url in settings.DAILY_JOB_URLS.split(",") if url.strip()]
    return [{"url": url, "source": None} for url in urls]


def _safe_load_json(value: Optional[str]) -> List[Dict[str, Any]]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        return []
    except Exception:
        return []


def _serialize_job(job: DailyRunJob) -> Dict[str, Any]:
    return {
        "job_id": job.id,
        "trigger_type": job.trigger_type,
        "status": job.status,
        "total": job.total,
        "success_count": job.success_count,
        "failed_count": job.failed_count,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "error_message": job.error_message,
        "items": _safe_load_json(job.items_json),
        "results": _safe_load_json(job.results_json)
    }
