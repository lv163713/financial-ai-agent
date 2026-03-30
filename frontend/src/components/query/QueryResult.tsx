'use client';

import { QueryAnalyzeResponse } from '@/types/api';
import { ExternalLink, CheckCircle2, AlertCircle, Clock, Search, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { formatDate, cn } from '@/lib/utils';
import { useState } from 'react';
import { syncApi } from '@/lib/api';

interface QueryResultProps {
  data: QueryAnalyzeResponse;
}

export default function QueryResult({ data }: QueryResultProps) {
  const [showMeta, setShowMeta] = useState(false);
  const { analysis, evidence, intent, meta } = data;
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      // 优先同步当前意图中的行业
      await syncApi.start({ sector: intent.sector || undefined });
      alert(`已启动后台 ${intent.sector || '全行业'} 数据同步，请稍后刷新重试。`);
    } catch (err) {
      console.error('Sync failed:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  const getSyncMessage = () => {
    if (meta.sync_reason === 'data_missing') {
      return {
        title: "本地知识库数据不足",
        desc: "未找到相关行业深度信息，建议手动同步以补全知识库。"
      };
    }
    if (meta.sync_reason === 'outdated' && meta.last_sync_time) {
      const days = Math.floor((new Date().getTime() - new Date(meta.last_sync_time).getTime()) / (1000 * 60 * 60 * 24));
      return {
        title: "本地数据可能已过时",
        desc: `最近一次相关更新在 ${days > 0 ? days + ' 天前' : '今天'}。金融市场瞬息万变，建议获取最新动态。`
      };
    }
    return {
      title: "建议更新知识库",
      desc: "为了提供更精准的分析，建议手动更新知识库后再试。"
    };
  };

  const syncMsg = getSyncMessage();

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 w-full">
      {/* 同步提醒栏 */}
      {meta.needs_sync && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 animate-in zoom-in-95 duration-300 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
              <AlertCircle className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-amber-900">{syncMsg.title}</h4>
              <p className="text-xs text-amber-700 mt-0.5">{syncMsg.desc}</p>
            </div>
          </div>
          <button
            onClick={handleSync}
            disabled={isSyncing}
            className={cn(
              "px-5 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-sm font-bold transition-all shadow-md flex items-center gap-2",
              isSyncing && "opacity-70 cursor-not-allowed"
            )}
          >
            {isSyncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            {isSyncing ? '正在同步...' : '更新知识库'}
          </button>
        </div>
      )}
      {/* 意图摘要 */}
      <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500 bg-white/50 px-2 py-1.5 rounded-lg w-fit">
        <span className="font-semibold text-gray-700">
          {intent.intent_type}
        </span>
        <span className="text-gray-300">|</span>
        <span className="flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" />
          {intent.time_range_hours}h
        </span>
        {intent.market && (
          <>
            <span className="text-gray-300">|</span>
            <span className="flex items-center gap-1">
              <Search className="h-3.5 w-3.5" />
              {intent.market}
            </span>
          </>
        )}
        {intent.keywords.length > 0 && (
          <>
            <span className="text-gray-300">|</span>
            <div className="flex flex-wrap gap-1">
              {intent.keywords.map((kw, i) => (
                <span key={i} className="text-blue-600 bg-blue-50/50 px-1.5 py-0.5 rounded text-xs">
                  #{kw}
                </span>
              ))}
            </div>
          </>
        )}
      </div>

      {/* 核心分析结论 */}
      <div className="space-y-5 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <section className="space-y-2">
          <h3 className="text-[13px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
            分析摘要
          </h3>
          <p className="text-gray-800 leading-relaxed text-[15px] whitespace-pre-wrap">{analysis.summary}</p>
        </section>

        <div className="h-px w-full bg-gray-50" />

        <section className="space-y-2">
          <h3 className="text-[13px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
            逻辑推演
          </h3>
          <p className="text-gray-800 leading-relaxed text-[15px] whitespace-pre-wrap">{analysis.logical_reasoning}</p>
        </section>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <section className="bg-amber-50/50 p-4 rounded-xl border border-amber-100/50">
            <h4 className="font-bold text-amber-900 mb-2 flex items-center gap-2 text-[13px]">
              <AlertCircle className="h-4 w-4" />
              风险提示
            </h4>
            <p className="text-amber-800 text-sm leading-relaxed">{analysis.risk_notice}</p>
          </section>
          <section className="bg-green-50/50 p-4 rounded-xl border border-green-100/50">
            <h4 className="font-bold text-green-900 mb-2 flex items-center gap-2 text-[13px]">
              <CheckCircle2 className="h-4 w-4" />
              受影响板块
            </h4>
            <p className="text-green-800 text-sm leading-relaxed">{analysis.affected_sectors}</p>
          </section>
        </div>
      </div>

      {/* 证据列表 */}
      {evidence.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest px-1">
            参考资料 ({evidence.length})
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {evidence.map((item, i) => (
              <a
                key={i}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-white p-3 rounded-xl border border-gray-100 hover:border-blue-200 hover:shadow-md transition-all group"
              >
                <div className="flex justify-between items-start gap-2 mb-1.5">
                  <span className="text-[10px] font-medium text-gray-500 bg-gray-50 px-1.5 py-0.5 rounded uppercase">{item.source}</span>
                  <span className="text-[10px] font-mono text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                    {(item.similarity_score * 100).toFixed(0)}% 相关
                  </span>
                </div>
                <h4 className="text-xs font-semibold text-gray-800 line-clamp-2 group-hover:text-blue-600 mb-2 leading-relaxed">
                  {item.title}
                </h4>
                <div className="flex justify-between items-center text-[10px] text-gray-400 mt-auto">
                  <span>{formatDate(item.published_at)}</span>
                  <ExternalLink className="h-3 w-3 group-hover:text-blue-500" />
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* 元信息区域 */}
      <div className="pt-2">
        <button
          onClick={() => setShowMeta(!showMeta)}
          className="flex items-center gap-1.5 text-[11px] font-medium text-gray-400 hover:text-gray-600 transition-colors bg-gray-50/50 px-2 py-1 rounded-lg"
        >
          {showMeta ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          处理耗时: {meta.processing_ms}ms
        </button>

        {showMeta && (
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-xl border border-gray-100 text-[11px] animate-in slide-in-from-top-2">
            <div className="space-y-1">
              <div className="text-gray-500">检索文档数</div>
              <div className="font-mono font-bold text-gray-700">{meta.retrieved_count}</div>
            </div>
            <div className="space-y-1">
              <div className="text-gray-500">回退抓取</div>
              <div className={cn("font-bold", meta.fallback_triggered ? "text-amber-600" : "text-green-600")}>
                {meta.fallback_triggered ? '已触发' : '未触发'}
                {meta.fallback_attempted && ' (曾尝试)'}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-gray-500">质量校验</div>
              <div className={cn("font-bold", meta.quality_passed ? "text-green-600" : "text-red-600")}>
                {meta.quality_passed ? '通过' : '未通过'}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-gray-500">字段完整度</div>
              <div className="font-mono font-bold text-gray-700">{(meta.field_completeness_rate * 100).toFixed(0)}%</div>
            </div>
            {meta.quality_issues.length > 0 && (
              <div className="col-span-full pt-3 mt-1 border-t border-gray-200">
                <div className="text-gray-500 mb-1.5">质量问题:</div>
                <div className="flex flex-wrap gap-2">
                  {meta.quality_issues.map((issue, i) => (
                    <span key={i} className="text-red-600 bg-red-50 px-2 py-1 rounded-md border border-red-100">
                      {issue}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
