import threading
import time
from datetime import datetime, date
from core.database import SessionLocal
from core.config import settings
from services.daily_jobs import run_daily_job_now
from services.metrics import metrics_store
from core.logger import get_logger

logger = get_logger("services.scheduler")

class DailyScheduler:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._last_run_date = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _loop(self):
        while not self._stop_event.is_set():
            now = datetime.now()
            if now.hour == settings.DAILY_RUN_HOUR and now.minute == settings.DAILY_RUN_MINUTE:
                today = date.today()
                if self._last_run_date != today:
                    self._last_run_date = today
                    self._run_daily_job()
            time.sleep(max(5, settings.SCHEDULER_POLL_SECONDS))

    def _run_daily_job(self):
        db = SessionLocal()
        try:
            result = run_daily_job_now(
                db=db,
                trigger_type="scheduled",
                items=None,
                max_concurrency=settings.DAILY_JOB_MAX_CONCURRENCY,
                retry_times=settings.DAILY_JOB_RETRY_TIMES
            )
            metrics_store.record_daily_job(failed=result.get("status") == "failed")
        except Exception as e:
            metrics_store.record_daily_job(failed=True)
            logger.error(f"daily_scheduler_run_failed error={str(e)}")
        finally:
            db.close()


daily_scheduler = DailyScheduler()
