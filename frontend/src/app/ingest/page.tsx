'use client';

import { useState, useEffect } from 'react';
import { newsApi } from '@/lib/api';
import { NewsItem } from '@/types/api';
import SyncDashboard from '@/components/ingest/SyncDashboard';
import { Database, AlertCircle, History, ExternalLink, Calendar, RefreshCw, Clock } from 'lucide-react';
import { formatDate } from '@/lib/utils';

export default function IngestPage() {
  const [history, setHistory] = useState<NewsItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const data = await newsApi.getList(0, 8);
      setHistory(data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    // 没 10 秒刷新一次历史记录，看看同步效果
    const timer = setInterval(fetchHistory, 10000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#fcfcfc] relative">
      {/* Header */}
      <header className="flex-shrink-0 h-14 border-b border-gray-100 flex items-center px-6 bg-white sticky top-0 z-10">
        <h1 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <RefreshCw className="h-5 w-5 text-blue-600" />
          更新本地知识库
        </h1>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8 scroll-smooth">
        <div className="max-w-6xl mx-auto space-y-10 pb-20">
          <div className="text-center space-y-2">
            <p className="text-gray-500 text-sm max-w-2xl mx-auto leading-relaxed">
              主动同步 A 股行业相关的大事件。系统将自动抓取财联社电报等实时快讯，通过 AI 结构化分析后存入向量库。
            </p>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
            <div className="xl:col-span-3 space-y-8">
              <SyncDashboard />
            </div>

            {/* 最近入库历史 */}
            <div className="space-y-6">
              <div className="flex items-center gap-2 px-1">
                <History className="h-4 w-4 text-gray-400" />
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">最新入库资料</h3>
              </div>
              
              <div className="space-y-3">
                {isLoadingHistory && history.length === 0 ? (
                  [...Array(5)].map((_, i) => (
                    <div key={i} className="h-24 bg-white border border-gray-100 animate-pulse rounded-2xl" />
                  ))
                ) : history.length > 0 ? (
                  history.map((item) => (
                    <div key={item.id} className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm space-y-2 group hover:border-blue-200 transition-all hover:shadow-md">
                      <div className="flex items-center gap-2">
                        <span className="px-1.5 py-0.5 bg-blue-50 text-blue-600 text-[9px] font-bold rounded uppercase tracking-tighter">
                          {item.source || '资讯'}
                        </span>
                      </div>
                      <h4 className="text-[13px] font-bold text-gray-800 line-clamp-2 leading-relaxed">
                        {item.title}
                      </h4>
                      <div className="flex items-center justify-between text-[10px] text-gray-400 pt-1">
                        <span className="flex items-center gap-1 font-medium">
                          <Clock className="h-3 w-3" />
                          {formatDate(item.created_at)}
                        </span>
                        <a 
                          href={item.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-blue-500 hover:text-blue-700 flex items-center gap-0.5 transition-colors font-bold"
                        >
                          原文 <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-10 text-gray-300 text-xs italic bg-gray-50/50 rounded-2xl border border-dashed border-gray-200">
                    暂无入库历史
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
