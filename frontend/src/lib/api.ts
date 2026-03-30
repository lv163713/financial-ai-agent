import axios from 'axios';
import {
  QueryAnalyzeRequest,
  QueryAnalyzeResponse,
  DailyRunRequest,
  DailyRunResponse,
  DailyRunStatusResponse,
  MetricsResponse,
  PipelineRequest,
  PipelineResponse,
  BatchPipelineRequest,
  BatchPipelineResponse,
  NewsItem,
  ConversationResponse,
  ConversationDetailResponse,
  ConversationCreate
} from '@/types/api';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const queryApi = {
  analyze: (data: QueryAnalyzeRequest) =>
    api.post<QueryAnalyzeResponse>('/query/analyze', data).then(res => res.data),
};

export const conversationsApi = {
  getList: (skip = 0, limit = 50) =>
    api.get<ConversationResponse[]>('/conversations', { params: { skip, limit } }).then(res => res.data),
  create: (data: ConversationCreate = {}) =>
    api.post<ConversationResponse>('/conversations', data).then(res => res.data),
  getDetail: (id: number) =>
    api.get<ConversationDetailResponse>(`/conversations/${id}`).then(res => res.data),
  delete: (id: number) =>
    api.delete(`/conversations/${id}`).then(res => res.data),
};

export const syncApi = {
  start: (data?: { sector?: string }): Promise<any> => api.post('/sync/start', data).then(res => res.data),
  status: (): Promise<any> => api.get('/sync/status').then(res => res.data),
};

export const jobsApi = {
  triggerDailyRun: (data: DailyRunRequest) =>
    api.post<DailyRunResponse>('/jobs/daily-run', data).then(res => res.data),
  getStatus: (jobId: number) =>
    api.get<DailyRunStatusResponse>(`/jobs/daily-run/${jobId}`).then(res => res.data),
  getMetrics: () =>
    api.get<MetricsResponse>('/jobs/metrics').then(res => res.data),
};

export const newsApi = {
  ingest: (data: PipelineRequest) =>
    api.post<PipelineResponse>('/news/ingest', data).then(res => res.data),
  ingestBatch: (data: BatchPipelineRequest) =>
    api.post<BatchPipelineResponse>('/news/ingest/batch', data).then(res => res.data),
  getList: (skip = 0, limit = 10) =>
    api.get<NewsItem[]>('/news', { params: { skip, limit } }).then(res => res.data),
};

export default api;
