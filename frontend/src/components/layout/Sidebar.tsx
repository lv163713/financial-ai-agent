'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Bot, Search, LayoutDashboard, Database, Plus, MessageSquare, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useChatStore } from '@/lib/store';
import { useEffect } from 'react';
import { conversationsApi } from '@/lib/api';

const navItems = [
  { name: '查询分析', href: '/query', icon: Search },
  { name: '任务看板', href: '/jobs', icon: LayoutDashboard },
  { name: '更新知识库', href: '/ingest', icon: Database },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { conversations, fetchConversations, currentConversationId, setCurrentConversationId, removeConversation } = useChatStore();

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleNewChat = () => {
    setCurrentConversationId(null);
    router.push('/query');
  };

  const handleSelectChat = (id: number) => {
    setCurrentConversationId(id);
    router.push('/query');
  };

  const handleDeleteChat = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (confirm('确定要删除这个对话吗？')) {
      try {
        await conversationsApi.delete(id);
        removeConversation(id);
      } catch (error) {
        console.error('Failed to delete conversation:', error);
      }
    }
  };

  return (
    <div className="w-64 bg-[#f9f9f9] border-r border-gray-200 h-screen flex flex-col flex-shrink-0">
      <div className="p-4 flex items-center gap-3 mt-2">
        <Bot className="h-7 w-7 text-blue-600" />
        <span className="font-bold text-lg text-gray-900">爬虫智能机器人</span>
      </div>
      
      <div className="px-4 pb-4 mt-4">
        <button 
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 py-2.5 rounded-xl text-sm font-medium transition-all shadow-sm"
        >
          <Plus className="h-4 w-4" />
          新对话
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 space-y-4 mt-2 custom-scrollbar">
        <div>
          <div className="text-[11px] font-semibold text-gray-400 px-2 py-2 uppercase tracking-wider">功能工作台</div>
          <div className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href && currentConversationId === null;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => {
                    if (item.href === '/query') {
                      setCurrentConversationId(null);
                    }
                  }}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>

        {conversations.length > 0 && (
          <div>
            <div className="text-[11px] font-semibold text-gray-400 px-2 py-2 uppercase tracking-wider">历史对话</div>
            <div className="space-y-1">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelectChat(conv.id)}
                  className={cn(
                    'group flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium cursor-pointer transition-colors',
                    currentConversationId === conv.id && pathname === '/query'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  )}
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <MessageSquare className="h-4 w-4 flex-shrink-0" />
                    <span className="truncate">{conv.title}</span>
                  </div>
                  <button 
                    onClick={(e) => handleDeleteChat(e, conv.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* 底部用户信息占位 */}
      <div className="p-4 border-t border-gray-200 mt-auto">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-xs">
            U
          </div>
          <div className="text-sm font-medium text-gray-700">User</div>
        </div>
      </div>
    </div>
  );
}
