'use client';

import { useState, useEffect, useRef } from 'react';
import { jobsApi } from '@/lib/api';
import { DailyRunStatusResponse, DailyRunResultItem } from '@/types/api';
import { Loader2, CheckCircle2, XCircle, Clock, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { formatDate, cn } from '@/lib/utils';

interface JobTrackerProps {
  jobId: number | null;
  onComplete?: () => void;
}

export default function JobTracker({ jobId, onComplete }: JobTrackerProps) {
  const [status, setStatus] = useState<DailyRunStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const pollStatus = async (id: number) => {
    try {
      const response = await jobsApi.getStatus(id);
      setStatus(response);

      if (response.status === 'completed' || response.status === 'failed') {
        setIsPolling(false);
        if (onComplete) onComplete();
      } else {
        timerRef.current = setTimeout(() => pollStatus(id), 3000);
      }
    } catch (err: any) {
      console.error('Polling failed:', err);
      setError('获取任务状态失败');
      setIsPolling(false);
    }
  };

  useEffect(() => {
    if (jobId) {
      setIsPolling(true);
      setError(null);
      pollStatus(jobId);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [jobId]);

  const toggleExpand = (url: string) => {
    const next = new Set(expandedItems);
    if (next.has(url)) next.delete(url);
    else next.add(url);
    setExpandedItems(next);
  };

  if (!jobId) return null;

  const isFinished = status?.status === 'completed' || status?.status === 'failed';

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-bold text-gray-900">任务 #{jobId}</h3>
            <span className={cn(
              "px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase",
              status?.status === 'completed' ? "bg-green-100 text-green-700" :
              status?.status === 'failed' ? "bg-red-100 text-red-700" :
              "bg-blue-100 text-blue-700 animate-pulse"
            )}>
              {status?.status || '初始化中'}
            </span>
          </div>
          <div className="text-xs text-gray-400 font-mono">
            {status?.started_at && `开始: ${formatDate(status.started_at)}`}
          </div>
        </div>

        {isPolling && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在执行中，请稍候...
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {status && (
          <div className="grid grid-cols-3 gap-4 py-4 border-y border-gray-50">
            <div className="text-center">
              <div className="text-lg font-bold text-gray-900">{status.total}</div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">总计</div>
            </div>
            <div className="text-center border-x border-gray-50">
              <div className="text-lg font-bold text-green-600">{status.success_count}</div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">成功</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-red-600">{status.failed_count}</div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">失败</div>
            </div>
          </div>
        )}

        {status?.error_message && (
          <div className="p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-100">
            <strong>错误:</strong> {status.error_message}
          </div>
        )}
      </div>

      {/* 结果明细 */}
      <div className="space-y-3">
        <h4 className="text-sm font-bold text-gray-500 uppercase tracking-wider px-1">执行明细</h4>
        <div className="space-y-2">
          {status?.results.map((result, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden transition-all">
              <div 
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                onClick={() => result.success && toggleExpand(result.url)}
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  {result.success ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500 shrink-0" />
                  )}
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-gray-900 truncate">{result.title || result.url}</div>
                    <div className="text-[10px] text-gray-400 flex items-center gap-2">
                      <span>{result.source || '未知来源'}</span>
                      {result.retry_count > 0 && (
                        <span className="text-amber-600 bg-amber-50 px-1 rounded">重试 {result.retry_count} 次</span>
                      )}
                    </div>
                  </div>
                </div>
                {result.success && (
                  <button className="text-gray-400 p-1">
                    {expandedItems.has(result.url) ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                )}
                {!result.success && result.error && (
                  <div className="text-[10px] text-red-600 font-medium ml-4 shrink-0 max-w-[200px] truncate">
                    {result.error}
                  </div>
                )}
              </div>

              {result.success && expandedItems.has(result.url) && (
                <div className="px-4 pb-4 pt-0 space-y-4 animate-in slide-in-from-top-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-gray-50">
                    <div className="space-y-1">
                      <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">分析摘要</div>
                      <p className="text-xs text-gray-600 leading-relaxed">{result.summary}</p>
                    </div>
                    <div className="space-y-1">
                      <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">逻辑推演</div>
                      <p className="text-xs text-gray-600 leading-relaxed">{result.logical_reasoning}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3 bg-green-50 rounded-lg">
                      <div className="text-[10px] font-bold text-green-700 uppercase mb-1">受影响板块</div>
                      <p className="text-xs text-green-800">{result.affected_sectors}</p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <div className="text-[10px] font-bold text-blue-700 uppercase mb-1">影响评估</div>
                      <p className="text-xs text-blue-800">{result.impact_assessment}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
