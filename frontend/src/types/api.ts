export interface QueryAnalyzeRequest {
  query: string;
  time_range_hours?: number;
  market?: string;
  conversation_id?: number;
}

export interface Intent {
  raw_query: string;
  keywords: string[];
  sector: string | null;
  market: string;
  time_range_hours: number;
  intent_type: "概览" | "风险" | "机会" | "单主题追踪";
}

export interface Evidence {
  source: string;
  url: string;
  title: string;
  published_at?: string;
  similarity_score: number;
}

export interface Analysis {
  summary: string;
  impact_assessment: string;
  affected_sectors: string;
  logical_reasoning: string;
  risk_notice: string;
}

export interface Meta {
  retrieved_count: number;
  fallback_triggered: boolean;
  fallback_attempted: boolean;
  fallback_success_count: number;
  fallback_failed_count: number;
  fallback_candidate_count: number;
  fallback_search_queries: string[];
  quality_passed: boolean;
  quality_issues: string[];
  field_completeness_rate: number;
  evidence_freshness_passed: boolean;
  processing_ms: number;
}

export interface QueryAnalyzeResponse {
  intent: Intent;
  evidence: Evidence[];
  analysis: Analysis;
  meta: Meta;
}

export interface MessageResponse {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  meta_data: QueryAnalyzeResponse | null;
  created_at: string;
}

export interface ConversationResponse {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetailResponse extends ConversationResponse {
  messages: MessageResponse[];
}

export interface ConversationCreate {
  title?: string;
}

export interface DailyRunRequest {
  items?: { url: string; source?: string }[];
  max_concurrency?: number;
  retry_times?: number;
}

export interface DailyRunResponse {
  job_id: number;
  trigger_type: "manual";
  status: string;
  total: number;
  success_count: number;
  failed_count: number;
  started_at: string | null;
  finished_at: string | null;
}

export interface DailyRunResultItem {
  url: string;
  success: boolean;
  retry_count: number;
  audit_log_id?: number;
  error?: string | null;
  news_id?: number | null;
  title?: string | null;
  source?: string | null;
  summary?: string | null;
  impact_assessment?: string | null;
  affected_sectors?: string | null;
  logical_reasoning?: string | null;
}

export interface DailyRunStatusResponse extends DailyRunResponse {
  error_message?: string;
  items: { url: string; source?: string }[];
  results: DailyRunResultItem[];
}

export interface MetricsResponse {
  in_memory: {
    query_total: number;
    query_avg_processing_ms: number;
    query_fallback_rate: number;
    query_quality_pass_rate: number;
    ingest_batch_total: number;
    ingest_item_total: number;
    ingest_success_rate: number;
    daily_job_total: number;
    daily_job_failed_rate: number;
    updated_at: string;
  };
  db_summary: {
    ingest_audit_total: number;
    ingest_audit_success_rate: number;
    daily_jobs_total: number;
    daily_jobs_failed_rate: number;
  };
}

export interface PipelineRequest {
  url: string;
  source?: string;
}

export interface PipelineResponse {
  news_id: number;
  title: string;
  url: string;
  source: string;
  summary: string;
  impact_assessment: string;
  affected_sectors: string;
  logical_reasoning: string;
}

export interface BatchPipelineRequest {
  items: { url: string; source?: string }[];
  max_concurrency?: number;
  retry_times?: number;
}

export interface BatchPipelineResponse {
  total: number;
  success_count: number;
  failed_count: number;
  results: PipelineResponse[];
}

export interface NewsItem {
  id: number;
  title: string;
  url: string;
  source?: string;
  created_at: string;
}
