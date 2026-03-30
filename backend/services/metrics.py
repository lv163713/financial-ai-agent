from threading import Lock
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.ingest_audit import IngestAuditLog
from models.daily_run_job import DailyRunJob


class MetricsStore:
    def __init__(self):
        self._lock = Lock()
        self._state = {
            "query_total": 0,
            "query_fallback_attempted": 0,
            "query_quality_passed": 0,
            "query_processing_ms_total": 0,
            "ingest_batch_total": 0,
            "ingest_item_total": 0,
            "ingest_item_success": 0,
            "ingest_item_failed": 0,
            "daily_job_total": 0,
            "daily_job_failed": 0,
            "updated_at": None
        }

    def record_query(self, processing_ms: int, fallback_attempted: bool, quality_passed: bool) -> None:
        with self._lock:
            self._state["query_total"] += 1
            self._state["query_processing_ms_total"] += max(0, int(processing_ms))
            if fallback_attempted:
                self._state["query_fallback_attempted"] += 1
            if quality_passed:
                self._state["query_quality_passed"] += 1
            self._state["updated_at"] = datetime.utcnow().isoformat()

    def record_ingest_batch(self, total: int, success_count: int, failed_count: int) -> None:
        with self._lock:
            self._state["ingest_batch_total"] += 1
            self._state["ingest_item_total"] += max(0, int(total))
            self._state["ingest_item_success"] += max(0, int(success_count))
            self._state["ingest_item_failed"] += max(0, int(failed_count))
            self._state["updated_at"] = datetime.utcnow().isoformat()

    def record_daily_job(self, failed: bool) -> None:
        with self._lock:
            self._state["daily_job_total"] += 1
            if failed:
                self._state["daily_job_failed"] += 1
            self._state["updated_at"] = datetime.utcnow().isoformat()

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            query_total = self._state["query_total"]
            avg_processing_ms = int(self._state["query_processing_ms_total"] / query_total) if query_total > 0 else 0
            quality_rate = round(self._state["query_quality_passed"] / query_total, 4) if query_total > 0 else 0.0
            fallback_rate = round(self._state["query_fallback_attempted"] / query_total, 4) if query_total > 0 else 0.0
            ingest_total = self._state["ingest_item_total"]
            ingest_success_rate = round(self._state["ingest_item_success"] / ingest_total, 4) if ingest_total > 0 else 0.0
            daily_total = self._state["daily_job_total"]
            daily_failed_rate = round(self._state["daily_job_failed"] / daily_total, 4) if daily_total > 0 else 0.0
            return {
                "query_total": query_total,
                "query_avg_processing_ms": avg_processing_ms,
                "query_fallback_rate": fallback_rate,
                "query_quality_pass_rate": quality_rate,
                "ingest_batch_total": self._state["ingest_batch_total"],
                "ingest_item_total": ingest_total,
                "ingest_success_rate": ingest_success_rate,
                "daily_job_total": daily_total,
                "daily_job_failed_rate": daily_failed_rate,
                "updated_at": self._state["updated_at"]
            }


def get_metrics_overview(db: Session) -> Dict[str, Any]:
    in_memory = metrics_store.snapshot()
    audit_total = db.query(func.count(IngestAuditLog.id)).scalar() or 0
    audit_success = db.query(func.count(IngestAuditLog.id)).filter(IngestAuditLog.success.is_(True)).scalar() or 0
    jobs_total = db.query(func.count(DailyRunJob.id)).scalar() or 0
    jobs_failed = db.query(func.count(DailyRunJob.id)).filter(DailyRunJob.status == "failed").scalar() or 0
    db_ingest_success_rate = round(audit_success / audit_total, 4) if audit_total > 0 else 0.0
    db_job_failed_rate = round(jobs_failed / jobs_total, 4) if jobs_total > 0 else 0.0
    return {
        "in_memory": in_memory,
        "db_summary": {
            "ingest_audit_total": int(audit_total),
            "ingest_audit_success_rate": db_ingest_success_rate,
            "daily_jobs_total": int(jobs_total),
            "daily_jobs_failed_rate": db_job_failed_rate
        }
    }


metrics_store = MetricsStore()
