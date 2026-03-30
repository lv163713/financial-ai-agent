from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.jobs import DailyRunRequest, DailyRunResponse, DailyRunStatusResponse
from services.daily_jobs import run_daily_job_now, get_daily_job_status
from services.metrics import get_metrics_overview


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/daily-run", response_model=DailyRunResponse, summary="手动触发每日任务")
def trigger_daily_run(payload: DailyRunRequest, db: Session = Depends(get_db)):
    try:
        items = None
        if payload.items:
            items = [{"url": str(item.url), "source": item.source} for item in payload.items]
        result = run_daily_job_now(
            db=db,
            trigger_type="manual",
            items=items,
            max_concurrency=payload.max_concurrency,
            retry_times=payload.retry_times
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/daily-run/{job_id}", response_model=DailyRunStatusResponse, summary="查询每日任务结果")
def get_daily_run_status(job_id: int, db: Session = Depends(get_db)):
    result = get_daily_job_status(db=db, job_id=job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return result


@router.get("/metrics", summary="查看核心链路指标")
def get_metrics(db: Session = Depends(get_db)):
    try:
        return get_metrics_overview(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
