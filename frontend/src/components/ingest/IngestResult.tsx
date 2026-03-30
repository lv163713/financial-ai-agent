'use client';

import { PipelineResponse, BatchPipelineResponse } from '@/types/api';
import { CheckCircle2, XCircle, AlertCircle, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface IngestResultProps {
  data: PipelineResponse | BatchPipelineResponse | null;
}

export default function IngestResult({ data }: IngestResultProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  if (!data) return null;

  const isBatch = 'results' in data;
  const results = isBatch ? data.results : [data];

  const toggleExpand = (id: number) => {
    const next = new Set(expanded);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpanded(next);
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest px-1">抓取执行结果</h3>
        {isBatch && (
          <div className="flex gap-4 text-[10px] font-bold uppercase tracking-widest">
            <span className="text-green-600">成功 {data.success_count}</span>
            <span className="text-red-600">失败 {data.failed_count}</span>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {results.map((item, i) => (
          <div key={i} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden group">
            <div 
              className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => toggleExpand(item.news_id)}
            >
              <div className="flex items-center gap-4 min-w-0">
                <div className="bg-green-50 p-2 rounded-xl text-green-600">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-bold text-gray-900 truncate">{item.title}</div>
                  <div className="text-[10px] text-gray-400 flex items-center gap-2 mt-0.5">
                    <span className="font-medium text-gray-500 uppercase">{item.source}</span>
                    <a 
                      href={item.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="flex items-center gap-0.5 hover:text-blue-500"
                      onClick={(e) => e.stopPropagation()}
                    >
                      原文 <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-mono text-gray-300">ID: {item.news_id}</span>
                <button className="text-gray-400">
                  {expanded.has(item.news_id) ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {expanded.has(item.news_id) && (
              <div className="px-6 pb-6 pt-0 space-y-6 animate-in slide-in-from-top-2">
                <div className="h-px bg-gray-50" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <section className="space-y-2">
                    <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">分析摘要</h4>
                    <p className="text-sm text-gray-700 leading-relaxed">{item.summary}</p>
                  </section>
                  <section className="space-y-2">
                    <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">逻辑推演</h4>
                    <p className="text-sm text-gray-700 leading-relaxed">{item.logical_reasoning}</p>
                  </section>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-green-50/50 p-4 rounded-xl border border-green-100/50">
                    <h5 className="text-[10px] font-bold text-green-700 uppercase mb-2">受影响板块</h5>
                    <p className="text-xs text-green-800 leading-relaxed">{item.affected_sectors}</p>
                  </div>
                  <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100/50">
                    <h5 className="text-[10px] font-bold text-blue-700 uppercase mb-2">影响评估</h5>
                    <p className="text-xs text-blue-800 leading-relaxed">{item.impact_assessment}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
