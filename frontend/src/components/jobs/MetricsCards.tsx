'use client';

import { MetricsResponse } from '@/types/api';
import { BarChart3, Zap, Database, CheckCircle, XCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricsCardsProps {
  metrics: MetricsResponse | null;
}

export default function MetricsCards({ metrics }: MetricsCardsProps) {
  if (!metrics) return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-24 bg-gray-100 animate-pulse rounded-xl border border-gray-200" />
      ))}
    </div>
  );

  const { in_memory, db_summary } = metrics;

  const cards = [
    {
      title: '查询处理',
      value: in_memory.query_total,
      subValue: `${in_memory.query_avg_processing_ms.toFixed(0)}ms`,
      label: '平均耗时',
      icon: Search,
      color: 'blue',
    },
    {
      title: 'RAG 质量',
      value: `${(in_memory.query_quality_pass_rate * 100).toFixed(1)}%`,
      subValue: `${(in_memory.query_fallback_rate * 100).toFixed(1)}%`,
      label: '回退率',
      icon: Zap,
      color: 'amber',
    },
    {
      title: '入库统计',
      value: db_summary.ingest_audit_total,
      subValue: `${(db_summary.ingest_audit_success_rate * 100).toFixed(1)}%`,
      label: '成功率',
      icon: Database,
      color: 'green',
    },
    {
      title: '每日任务',
      value: db_summary.daily_jobs_total,
      subValue: `${(db_summary.daily_jobs_failed_rate * 100).toFixed(1)}%`,
      label: '失败率',
      icon: BarChart3,
      color: 'purple',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <div key={i} className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex flex-col justify-between">
            <div className="flex justify-between items-start mb-4">
              <span className="text-sm font-medium text-gray-500">{card.title}</span>
              <div className={cn(
                "p-2 rounded-lg",
                card.color === 'blue' && "bg-blue-50 text-blue-600",
                card.color === 'amber' && "bg-amber-50 text-amber-600",
                card.color === 'green' && "bg-green-50 text-green-600",
                card.color === 'purple' && "bg-purple-50 text-purple-600",
              )}>
                <Icon className="h-5 w-5" />
              </div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{card.value}</div>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-xs font-semibold text-gray-600">{card.subValue}</span>
                <span className="text-[10px] text-gray-400">{card.label}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

import { Search } from 'lucide-react';
