'use client';

import { useState, useRef, useEffect } from 'react';
import { queryApi, conversationsApi } from '@/lib/api';
import { QueryAnalyzeRequest, QueryAnalyzeResponse } from '@/types/api';
import QueryForm from '@/components/query/QueryForm';
import QueryResult from '@/components/query/QueryResult';
import { AlertCircle, User, Bot, Sparkles, Loader2 } from 'lucide-react';
import { useChatStore } from '@/lib/store';

type Message = {
  id: string;
  type: 'user' | 'bot';
  content?: string;
  request?: QueryAnalyzeRequest;
  result?: QueryAnalyzeResponse;
  error?: string;
  isLoading?: boolean;
};

export default function QueryPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isInitializing, setIsInitializing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { currentConversationId, setCurrentConversationId, fetchConversations } = useChatStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 当 currentConversationId 变化时，加载历史消息
  useEffect(() => {
    if (!currentConversationId) {
      setMessages([]);
      return;
    }

    const loadHistory = async () => {
      setIsInitializing(true);
      try {
        const detail = await conversationsApi.getDetail(currentConversationId);
        const historyMessages: Message[] = [];
        
        detail.messages.forEach(msg => {
          if (msg.role === 'user') {
            historyMessages.push({
              id: msg.id.toString(),
              type: 'user',
              content: msg.content
            });
          } else if (msg.role === 'assistant') {
            historyMessages.push({
              id: msg.id.toString(),
              type: 'bot',
              content: msg.content,
              result: msg.meta_data || undefined
            });
          }
        });
        
        setMessages(historyMessages);
      } catch (error) {
        console.error('Failed to load conversation history:', error);
      } finally {
        setIsInitializing(false);
      }
    };

    loadHistory();
  }, [currentConversationId]);

  const handleQuerySubmit = async (data: QueryAnalyzeRequest) => {
    let activeConvId = currentConversationId;
    
    // 如果是新对话，先创建一个会话
    if (!activeConvId) {
      try {
        const newConv = await conversationsApi.create({ title: data.query });
        activeConvId = newConv.id;
        setCurrentConversationId(activeConvId);
        // 刷新侧边栏列表
        fetchConversations();
      } catch (err) {
        console.error('Failed to create conversation:', err);
      }
    }

    const userMsgId = Date.now().toString();
    const botMsgId = (Date.now() + 1).toString();
    
    setMessages(prev => [
      ...prev,
      { id: userMsgId, type: 'user', content: data.query, request: data },
      { id: botMsgId, type: 'bot', isLoading: true }
    ]);

    try {
      const response = await queryApi.analyze({
        ...data,
        conversation_id: activeConvId || undefined
      });
      
      setMessages(prev => prev.map(msg => 
        msg.id === botMsgId ? { ...msg, isLoading: false, result: response } : msg
      ));
      
      // 如果是第一次对话，后端会更新标题，我们需要刷新侧边栏
      if (messages.length === 0) {
        fetchConversations();
      }
    } catch (err: any) {
      console.error('Query analysis failed:', err);
      const errorMsg = err.response?.data?.detail || err.message || '查询分析失败，请稍后重试。';
      setMessages(prev => prev.map(msg => 
        msg.id === botMsgId ? { ...msg, isLoading: false, error: errorMsg } : msg
      ));
    }
  };

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Header */}
      <header className="flex-shrink-0 h-14 border-b border-gray-100 flex items-center px-6 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <h1 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-600" />
          智能查询分析
        </h1>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth">
        {isInitializing ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-6 max-w-2xl mx-auto mt-[-10vh] animate-in fade-in zoom-in duration-500">
            <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mb-4">
              <Bot className="h-8 w-8 text-blue-600" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-800">我是你的金融资讯智能助手</h2>
            <p className="text-gray-500 text-sm leading-relaxed max-w-md">
              我可以结合 RAG 检索与即时抓取，深度解析金融资讯意图，提供结构化分析结论。
              试着问我一些问题吧！
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-8">
              {['A股半导体板块有哪些风险？', '总结昨日的美股科技股动态', '追踪最近的降息影响'].map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleQuerySubmit({ query: q, time_range_hours: 24 })}
                  className="px-4 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-full text-sm text-gray-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-8 pb-10">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-4 ${msg.type === 'user' ? 'flex-row-reverse' : ''} animate-in slide-in-from-bottom-2`}>
                <div className="flex-shrink-0 mt-1">
                  {msg.type === 'user' ? (
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center shadow-sm">
                      <User className="h-5 w-5 text-white" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 bg-blue-50 rounded-full flex items-center justify-center border border-blue-100">
                      <Bot className="h-5 w-5 text-blue-600" />
                    </div>
                  )}
                </div>
                
                <div className={`max-w-[85%] ${msg.type === 'user' ? 'bg-blue-50 text-gray-900 rounded-2xl rounded-tr-sm px-5 py-3.5 border border-blue-100/50' : 'w-full'}`}>
                  {msg.type === 'user' && (
                    <div className="whitespace-pre-wrap text-[15px] leading-relaxed">{msg.content}</div>
                  )}
                  
                  {msg.type === 'bot' && (
                    <div className="w-full">
                      {msg.isLoading && (
                        <div className="flex items-center gap-2 text-blue-600 text-sm py-2">
                          <span className="flex gap-1">
                            <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                            <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                            <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></span>
                          </span>
                          <span className="font-medium ml-1">正在检索与深度分析资讯...</span>
                        </div>
                      )}
                      
                      {msg.error && (
                        <div className="flex items-start gap-2 text-red-600 bg-red-50 p-4 rounded-xl border border-red-100 mt-2">
                          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                          <div className="text-sm font-medium">{msg.error}</div>
                        </div>
                      )}
                      
                      {msg.result ? (
                        <div className="mt-2">
                          <QueryResult data={msg.result} />
                        </div>
                      ) : msg.content && !msg.isLoading && !msg.error && (
                        <div className="whitespace-pre-wrap text-[15px] leading-relaxed text-gray-800">{msg.content}</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 bg-gradient-to-t from-white via-white to-transparent pt-6 pb-4 px-4 sm:px-6 z-10">
        <QueryForm 
          onSubmit={handleQuerySubmit} 
          isLoading={messages.length > 0 && messages[messages.length - 1].isLoading === true} 
        />
      </div>
    </div>
  );
}
