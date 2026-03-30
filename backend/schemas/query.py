from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class QueryAnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    time_range_hours: int = Field(default=24, ge=1, le=1440)
    market: Optional[str] = Field(default=None, max_length=20)
    conversation_id: Optional[int] = Field(None, description="所属会话ID，用于关联历史记录")


class QueryIntent(BaseModel):
    raw_query: str
    keywords: List[str]
    sector: Optional[str] = None
    market: str
    time_range_hours: int
    intent_type: Literal["概览", "风险", "机会", "单主题追踪", "重大事件"]
    is_realtime_query: bool = False
    prefer_cls: bool = False


class QueryEvidence(BaseModel):
    source: str
    url: str
    title: str
    published_at: Optional[str] = None
    similarity_score: float


class QueryAnalysis(BaseModel):
    summary: str
    impact_assessment: str
    affected_sectors: str
    logical_reasoning: str
    risk_notice: str


class QueryMeta(BaseModel):
    retrieved_count: int
    fallback_triggered: bool
    fallback_attempted: bool = False
    fallback_success_count: int = 0
    fallback_failed_count: int = 0
    fallback_candidate_count: int = 0
    fallback_search_queries: List[str] = Field(default_factory=list)
    needs_sync: bool = False
    sync_reason: Optional[str] = None
    last_sync_time: Optional[str] = None
    quality_passed: bool = False
    quality_issues: List[str] = Field(default_factory=list)
    field_completeness_rate: float = 0.0
    evidence_freshness_passed: bool = False
    processing_ms: int


class QueryAnalyzeResponse(BaseModel):
    intent: QueryIntent
    evidence: List[QueryEvidence]
    analysis: QueryAnalysis
    meta: QueryMeta
