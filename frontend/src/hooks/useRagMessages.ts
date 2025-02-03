import { ChatMessage } from "@/lib/types";
import { create } from "zustand";

interface RagMessagesState {
  messages: ChatMessage[];
  error: string | null;
  isLoading: boolean;

  addUserMessage: (message: string) => void;
  addAiMessage: (message: string, session_id: string) => Promise<void>;
  clearMessages: () => void;
}

const useRagMessages = create<RagMessagesState>((set, get) => ({
  messages: [],
  error: null,
  isLoading: false,

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
    set({ isLoading: true, error: null });
    const token = localStorage.getItem("auth-token");
    try {
      const response = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}rag/${session_id}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message,
          }),
        }
      );

      if (!response.ok) throw Error("Failed to get answer");
      const res = await response.json();

      set((state) => ({
        messages: [
          ...state.messages,
          {
            role: "ai",
            content: res?.message ? res?.message : "No response",
            source: res?.sources ? res?.sources : [],
            timestamp: new Date(),
          },
        ],
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  clearMessages: () => {
    set({ messages: [] });
  },
}));

export default useRagMessages;
