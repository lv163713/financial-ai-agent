import { create } from 'zustand';
import { conversationsApi } from '@/lib/api';
import { ConversationResponse } from '@/types/api';

interface ChatStore {
  currentConversationId: number | null;
  conversations: ConversationResponse[];
  setCurrentConversationId: (id: number | null) => void;
  fetchConversations: () => Promise<void>;
  addConversation: (conv: ConversationResponse) => void;
  removeConversation: (id: number) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  currentConversationId: null,
  conversations: [],
  
  setCurrentConversationId: (id) => set({ currentConversationId: id }),
  
  fetchConversations: async () => {
    try {
      const data = await conversationsApi.getList();
      set({ conversations: data });
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    }
  },
  
  addConversation: (conv) => set((state) => {
    const exists = state.conversations.find(c => c.id === conv.id);
    if (exists) {
      return {
        conversations: state.conversations.map(c => c.id === conv.id ? conv : c)
      };
    }
    return {
      conversations: [conv, ...state.conversations]
    };
  }),

  removeConversation: (id) => set((state) => ({
    conversations: state.conversations.filter(c => c.id !== id),
    currentConversationId: state.currentConversationId === id ? null : state.currentConversationId
  })),
}));
