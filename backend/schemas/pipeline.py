from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


class PipelineRequest(BaseModel):
    url: HttpUrl
    source: Optional[str] = None


class PipelineResponse(BaseModel):
    news_id: int
    title: str
    url: str
    source: Optional[str]
    summary: str
    impact_assessment: str
    affected_sectors: str
    logical_reasoning: str


class BatchPipelineItem(BaseModel):
    url: HttpUrl
    source: Optional[str] = None


class BatchPipelineRequest(BaseModel):
    items: List[BatchPipelineItem] = Field(..., min_length=1, max_length=50)
    max_concurrency: int = Field(default=3, ge=1, le=10)
    retry_times: int = Field(default=1, ge=0, le=3)


class BatchPipelineItemResponse(BaseModel):
    url: str
    success: bool
    retry_count: int
    audit_log_id: Optional[int] = None
    error: Optional[str] = None
    news_id: Optional[int] = None
    title: Optional[str] = None
    source: Optional[str] = None
    summary: Optional[str] = None
    impact_assessment: Optional[str] = None
    affected_sectors: Optional[str] = None
    logical_reasoning: Optional[str] = None


class BatchPipelineResponse(BaseModel):
    total: int
    success_count: int
    failed_count: int
    results: List[BatchPipelineItemResponse]
