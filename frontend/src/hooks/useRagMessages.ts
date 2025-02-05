import { ChatMessage } from "@/lib/types";
import { create } from "zustand";
import { WebSocketService } from "@/services/websocket";

interface RagMessagesState {
  messages: ChatMessage[];
  error: string | null;
  isLoading: boolean;
  websocket: WebSocketService | null;

  addUserMessage: (message: string) => void;
  addAiMessage: (message: string, session_id: string) => Promise<void>;
  clearMessages: () => void;
  initializeWebSocket: (sessionId: string) => void;
  cleanup: () => void;
}

const useRagMessages = create<RagMessagesState>((set, get) => ({
  messages: [],
  error: null,
  isLoading: false,
  websocket: null,

  addUserMessage: (message: string) => {
    set((state) => ({
      messages: [
        ...state.messages,
        {
          role: "user",
          content: message,
          timestamp: new Date(),
        },
      ],
    }));
  },

  addAiMessage: async (message: string, session_id: string) => {
    const { websocket } = get();
    if (websocket) {
      set({ isLoading: true, error: null });
      websocket.sendMessage(message);
    }
  },

  clearMessages: () => {
    set({ messages: [] });
  },

  initializeWebSocket: (sessionId: string) => {
    const ws = new WebSocketService(sessionId);
    
    // Clear existing messages before initializing new connection
    set({ messages: [] });

    ws.addMessageHandler((data) => {
      console.log('WebSocket message received:', data);  // Debug log
      
      if (data.type === "message" || data.type === "initialize") {
        set((state) => ({
          messages: [...state.messages, data.content],
          isLoading: false,
        }));
      } else if (data.type === "loading") {
        set({ isLoading: data.content.is_loading });
      } else if (data.type === "error") {
        set({ error: data.content, isLoading: false });
      }
    });

    ws.connect();
    set({ websocket: ws, error: null });
  },

  cleanup: () => {
    const { websocket } = get();
    if (websocket) {
      websocket.disconnect();
      set({ websocket: null, messages: [], isLoading: false, error: null });
    }
  },
}));

export default useRagMessages;
