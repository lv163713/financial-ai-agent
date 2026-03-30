'use client';

import { useState } from 'react';
import { newsApi } from '@/lib/api';
import { PipelineResponse, BatchPipelineResponse } from '@/types/api';
import { Link, Layers, Loader2, Send, Plus, Trash2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface IngestFormProps {
  onSuccess: (data: PipelineResponse | BatchPipelineResponse) => void;
  onError: (msg: string) => void;
}

export default function IngestForm({ onSuccess, onError }: IngestFormProps) {
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single');
  const [isLoading, setIsLoading] = useState(false);

  // Single mode state
  const [url, setUrl] = useState('');
  const [source, setSource] = useState('');

  // Batch mode state
  const [batchInput, setBatchInput] = useState('');
  const [maxConcurrency, setMaxConcurrency] = useState(3);

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim() || isLoading) return;
    setIsLoading(true);
    try {
      const result = await newsApi.ingest({ url: url.trim(), source: source || undefined });
      onSuccess(result);
      setUrl('');
      setSource('');
    } catch (err: any) {
      onError(err.response?.data?.detail || err.message || '抓取失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBatchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const urls = batchInput.split('\n').filter(u => u.trim()).map(u => ({ url: u.trim() }));
    if (urls.length === 0 || isLoading) return;
    
    setIsLoading(true);
    try {
      const result = await newsApi.ingestBatch({ 
        items: urls,
        max_concurrency: maxConcurrency 
      });
      onSuccess(result);
      setBatchInput('');
    } catch (err: any) {
      onError(err.response?.data?.detail || err.message || '批量抓取失败');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="flex border-b border-gray-100">
        <button
          onClick={() => setActiveTab('single')}
          className={cn(
            "flex-1 py-4 text-sm font-bold flex items-center justify-center gap-2 transition-colors",
            activeTab === 'single' ? "text-blue-600 bg-blue-50/50" : "text-gray-400 hover:text-gray-600"
          )}
        >
          <Link className="h-4 w-4" />
          单条抓取
        </button>
        <button
          onClick={() => setActiveTab('batch')}
          className={cn(
            "flex-1 py-4 text-sm font-bold flex items-center justify-center gap-2 transition-colors",
            activeTab === 'batch' ? "text-blue-600 bg-blue-50/50" : "text-gray-400 hover:text-gray-600"
          )}
        >
          <Layers className="h-4 w-4" />
          批量抓取
        </button>
      </div>

      <div className="p-6">
        {activeTab === 'single' ? (
          <form onSubmit={handleSingleSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">新闻 URL</label>
              <input
                type="url"
                required
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
                placeholder="https://example.com/news/123"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">来源名称 (可选)</label>
              <input
                type="text"
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
                placeholder="如：华尔街见闻"
                value={source}
                onChange={(e) => setSource(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !url}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-sm shadow-lg shadow-blue-200 disabled:opacity-50 disabled:shadow-none transition-all flex items-center justify-center gap-2"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              立即抓取入库
            </button>
          </form>
        ) : (
          <form onSubmit={handleBatchSubmit} className="space-y-4">
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">URL 列表 (每行一个)</label>
                <span className="text-[10px] text-gray-400">
                  已输入 {batchInput.split('\n').filter(u => u.trim()).length} 条
                </span>
              </div>
              <textarea
                rows={6}
                required
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm font-mono"
                placeholder="https://url1.com&#10;https://url2.com"
                value={batchInput}
                onChange={(e) => setBatchInput(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-1 space-y-1">
                <div className="flex justify-between text-[10px] font-bold text-gray-400 uppercase">
                  <label>最大并发</label>
                  <span>{maxConcurrency}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={maxConcurrency}
                  onChange={(e) => setMaxConcurrency(Number(e.target.value))}
                  className="w-full h-1.5 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>
              <button
                type="submit"
                disabled={isLoading || !batchInput.trim()}
                className="flex-[2] py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-sm shadow-lg shadow-blue-200 disabled:opacity-50 disabled:shadow-none transition-all flex items-center justify-center gap-2"
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Layers className="h-4 w-4" />}
                启动批量任务
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
