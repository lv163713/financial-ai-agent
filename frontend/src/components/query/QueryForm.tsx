'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { QueryAnalyzeRequest } from '@/types/api';

interface QueryFormProps {
  onSubmit: (data: QueryAnalyzeRequest) => Promise<void>;
  isLoading: boolean;
}

export default function QueryForm({ onSubmit, isLoading }: QueryFormProps) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [query]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim() || isLoading) return;
    const currentQuery = query;
    setQuery('');
    // 聚焦输入框
    setTimeout(() => textareaRef.current?.focus(), 0);
    await onSubmit({
      query: currentQuery.trim()
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form 
        onSubmit={handleSubmit} 
        className="relative bg-white border border-gray-200 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.04)] focus-within:ring-1 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all flex items-end p-2"
      >
        <textarea
          ref={textareaRef}
          rows={1}
          className="flex-1 max-h-[200px] min-h-[40px] px-3 py-2.5 resize-none outline-none text-[15px] text-gray-900 bg-transparent leading-relaxed"
          placeholder="输入您的问题，如：分析今日 A 股半导体板块的风险点... (Shift+Enter 换行)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="p-2 mb-1 ml-2 rounded-xl text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:bg-gray-200 disabled:text-gray-400 transition-all flex-shrink-0"
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </form>
      <div className="text-center mt-2 text-[11px] text-gray-400">
        内容由 AI 生成，可能存在不准确的情况，请仔细甄别。
      </div>
    </div>
  );
}
