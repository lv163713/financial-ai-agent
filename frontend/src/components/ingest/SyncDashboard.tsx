'use client';

import { useState, useEffect } from 'react';
import { syncApi } from '@/lib/api';
import { Search, Loader2, RefreshCw, CheckCircle2, AlertCircle, Play } from 'lucide-react';
import { cn } from '@/lib/utils';

const TDX_SECTORS = [
  "金融", "采掘", "化工", "钢铁", "有色", "电子", "家用电器", "食品饮料", "商业贸易", 
  "轻工制造", "医药生物", "公用事业", "交通运输", "房地产", "有色金属", "机械设备", 
  "汽车", "计算机", "传媒", "通信", "建筑装饰", "建筑材料", "电力设备", 
  "国防军工", "美容护理", "纺织服饰", "社会服务", "基础化工", "农林牧渔", "石油石化", 
  "综合", "煤炭", "非银金融", "银行"
];

export default function SyncDashboard() {
  const [status, setStatus] = useState<any>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [selectedSector, setSelectedSector] = useState<string>('');

  const fetchStatus = async () => {
    try {
      const data = await syncApi.status();
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch sync status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 3000);
    return () => clearInterval(timer);
  }, []);

  const handleStartSync = async (sector?: string) => {
    setIsStarting(true);
    try {
      await syncApi.start({ sector });
      fetchStatus();
    } catch (err: any) {
      alert(err.response?.data?.detail || '同步启动失败');
    } finally {
      setIsStarting(false);
    }
  };

  const isRunning = status?.is_running;

  return (
    <div className="space-y-8">
      {/* 状态总览卡片 */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <RefreshCw className={cn("h-6 w-6 text-blue-600", isRunning && "animate-spin")} />
              知识库同步状态
            </h2>
            <p className="text-sm text-gray-500">
              {isRunning 
                ? `正在同步：${status.current_sector} (${status.processed_sectors}/${status.total_sectors})`
                : status?.last_sync_time 
                  ? `上次全量同步：${new Date(status.last_sync_time).toLocaleString()}`
                  : '尚未进行过行业同步'}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleStartSync()}
              disabled={isRunning || isStarting}
              className={cn(
                "px-6 py-3 rounded-2xl font-bold text-sm transition-all flex items-center gap-2 shadow-lg",
                isRunning 
                  ? "bg-blue-50 text-blue-400 cursor-not-allowed shadow-none"
                  : "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-100"
              )}
            >
              {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current" />}
              全行业增量同步
            </button>
          </div>
        </div>

        {/* 进度条 */}
        {isRunning && (
          <div className="mt-8 space-y-3">
            <div className="flex justify-between text-xs font-bold text-gray-500 uppercase tracking-wider">
              <span>同步进度</span>
              <span>{status.progress}%</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-600 transition-all duration-500 ease-out"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* 行业选择更新 */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8">
        <h3 className="text-lg font-bold text-gray-900 mb-6">按行业精准更新</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {TDX_SECTORS.map((sector) => (
            <button
              key={sector}
              onClick={() => handleStartSync(sector)}
              disabled={isRunning || isStarting}
              className={cn(
                "px-3 py-2.5 rounded-xl text-xs font-medium border transition-all text-center",
                status?.current_sector === sector
                  ? "bg-blue-50 border-blue-200 text-blue-700 font-bold animate-pulse"
                  : "bg-white border-gray-100 text-gray-600 hover:border-blue-200 hover:bg-blue-50/30"
              )}
            >
              {sector}
            </button>
          ))}
        </div>
      </div>

      {/* 说明卡片 */}
      <div className="bg-blue-50/50 border border-blue-100 rounded-2xl p-6 flex items-start gap-4">
        <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
        <div className="text-sm text-blue-800 space-y-1">
          <p className="font-bold">关于同步逻辑：</p>
          <ul className="list-disc list-inside space-y-1 text-blue-700/80">
            <li>系统会通过搜索引擎实时检索通达信行业相关的金融大事件。</li>
            <li>优先召回财联社电报、华尔街见闻等权威财经源。</li>
            <li>所有资讯入库前均经过 AI 相关性过滤，确保 RAG 知识库纯净度。</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
