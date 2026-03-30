'use client';

import { useState, useEffect } from 'react';
import { jobsApi } from '@/lib/api';
import { MetricsResponse, DailyRunResponse } from '@/types/api';
import MetricsCards from '@/components/jobs/MetricsCards';
import JobTracker from '@/components/jobs/JobTracker';
import { Play, Settings2, Loader2, AlertCircle, RefreshCw, LayoutDashboard } from 'lucide-react';

export default function JobsPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [currentJobId, setCurrentJobId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfig, setShowConfig] = useState(false);

  // 配置状态
  const [maxConcurrency, setMaxConcurrency] = useState(3);
  const [retryTimes, setRetryTimes] = useState(1);

  const fetchMetrics = async () => {
    try {
      const response = await jobsApi.getMetrics();
      setMetrics(response);
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const timer = setInterval(fetchMetrics, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleTriggerRun = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await jobsApi.triggerDailyRun({
        max_concurrency: maxConcurrency,
        retry_times: retryTimes,
      });
      setCurrentJobId(response.job_id);
    } catch (err: any) {
      console.error('Failed to trigger job:', err);
      setError(err.response?.data?.detail || err.message || '触发任务失败');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Header */}
      <header className="flex-shrink-0 h-14 border-b border-gray-100 flex items-center px-6 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <h1 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <LayoutDashboard className="h-5 w-5 text-blue-600" />
          每日任务看板
        </h1>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
        <div className="max-w-5xl mx-auto space-y-10 pb-20">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
            <div className="space-y-2">
              <p className="text-gray-500 text-sm max-w-2xl">
                监控系统全链路指标，手动执行每日自动化新闻抓取与智能分析任务。
              </p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <button
                onClick={() => setShowConfig(!showConfig)}
                className="p-2.5 rounded-xl border border-gray-200 bg-white text-gray-500 hover:text-gray-700 hover:border-gray-300 transition-all shadow-sm"
                title="任务配置"
              >
                <Settings2 className="h-5 w-5" />
              </button>
              <button
                onClick={handleTriggerRun}
                disabled={isLoading || (currentJobId !== null && metrics?.in_memory.daily_job_total !== undefined)}
                className="flex-1 sm:flex-none inline-flex items-center justify-center px-6 py-2.5 border border-transparent text-sm font-bold rounded-xl shadow-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
                    启动中...
                  </>
                ) : (
                  <>
                    <Play className="-ml-1 mr-2 h-4 w-4 fill-current" />
                    手动触发每日任务
                  </>
                )}
              </button>
            </div>
          </div>

          {showConfig && (
            <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm animate-in slide-in-from-top-4 duration-300">
              <div className="flex items-center gap-2 mb-4">
                <Settings2 className="h-4 w-4 text-blue-600" />
                <h3 className="text-sm font-bold text-gray-900">任务执行配置</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-medium text-gray-500">
                    <label>最大并发数</label>
                    <span>{maxConcurrency}</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    step="1"
                    value={maxConcurrency}
                    onChange={(e) => setMaxConcurrency(Number(e.target.value))}
                    className="w-full h-1.5 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-medium text-gray-500">
                    <label>重试次数</label>
                    <span>{retryTimes}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3"
                    step="1"
                    value={retryTimes}
                    onChange={(e) => setRetryTimes(Number(e.target.value))}
                    className="w-full h-1.5 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest">全链路指标</h2>
              <div className="flex items-center gap-1.5 text-[10px] font-medium text-gray-400">
                <RefreshCw className="h-2.5 w-2.5 animate-spin-slow" />
                实时自动刷新
              </div>
            </div>
            <MetricsCards metrics={metrics} />
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 text-red-800">
              <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
              <div className="text-sm">
                <p className="font-semibold text-red-900">触发任务失败</p>
                <p>{error}</p>
              </div>
            </div>
          )}

          {currentJobId ? (
            <JobTracker jobId={currentJobId} onComplete={fetchMetrics} />
          ) : (
            <div className="bg-gray-50/50 border-2 border-dashed border-gray-200 rounded-3xl py-24 text-center">
              <div className="max-w-xs mx-auto space-y-4">
                <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mx-auto transform rotate-12">
                  <Play className="h-8 w-8 text-blue-200 fill-current" />
                </div>
                <div className="space-y-1">
                  <p className="text-gray-500 font-bold">暂无正在运行的任务</p>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    点击上方“手动触发”按钮，开始一键式新闻抓取、AI 摘要及入库全链路。
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
