from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Literal


class DailyRunItem(BaseModel):
    url: HttpUrl
    source: Optional[str] = None


class DailyRunRequest(BaseModel):
    items: Optional[List[DailyRunItem]] = None
    max_concurrency: int = Field(default=3, ge=1, le=10)
    retry_times: int = Field(default=1, ge=0, le=3)


class DailyRunResponse(BaseModel):
    job_id: int
    trigger_type: Literal["manual", "scheduled"]
    status: str
    total: int
    success_count: int
    failed_count: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class DailyRunStatusResponse(DailyRunResponse):
    error_message: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)
