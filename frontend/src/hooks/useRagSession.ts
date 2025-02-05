import { RagSession } from "@/lib/types";
import { create } from "zustand";
import { useNavigate } from "react-router-dom";
import useRagMessages from "./useRagMessages";

interface RagSessionState {
  currentSession: RagSession | null;
  isCreatingSession: boolean;
  isUploadingFiles: boolean;
  error: string | null;
  sessions: RagSession[];
  isLoading: boolean;

  createSession: (
    userId: string,
    title: string,
    openai_api_key: string,
    description?: string
  ) => Promise<RagSession>;
  uploadFiles: (sessionId: string, files: File[]) => Promise<void>;
  getCurrentSession: () => RagSession | null;
  clearCurrentSession: () => void;
  fetchSessions: () => Promise<void>;
  fetchSession: (sessionId: string) => Promise<void>;
}

const useRagSessionStore = create<RagSessionState>((set, get) => ({
  currentSession: null,
  isCreatingSession: false,
  isUploadingFiles: false,
  error: null,
  sessions: [],
  isLoading: false,

  fetchSessions: async () => {
    set({ isLoading: true, error: null });
    const token = localStorage.getItem("auth-token");
    try {
      const response = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}rag/history`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error("Failed to fetch sessions");

      const sessions = await response.json();
      set({ sessions, isLoading: false });
    } catch (error) {
      set({ error: "Failed to fetch sessions", isLoading: false });
      throw error;
    }
  },

  fetchSession: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    const token = localStorage.getItem("auth-token");
    const ragMessages = useRagMessages.getState()

    try {
      const response = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}rag/session/${sessionId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error("Failed to fetch session");

      const session = await response.json();
      set({
        currentSession: session,
        isLoading: false,
        error: null,
      });
      ragMessages.messages = session.messages
    } catch (error) {
      set({
        error: "Failed to fetch session",
        isLoading: false,
        currentSession: null,
      });
      throw error;
    }
  },

  createSession: async (
    userId: string,
    openai_api_key: string,
    title: string,
    description?: string
  ) => {
    set({ isCreatingSession: true, error: null });
    const token = localStorage.getItem("auth-token");
    try {
      const response = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}rag/session`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            user_id: userId,
            api_key: openai_api_key,
            title,
            description,
          }),
        }
      );

      if (!response.ok) throw new Error("Failed to create session");

      const session = await response.json();
      set((state) => ({
        currentSession: session,
        isCreatingSession: false,
        sessions: [...state.sessions, session],
      }));
      return session;
    } catch (error) {
      set({ error: "Failed to create session", isCreatingSession: false });
      throw error;
    }
  },

  uploadFiles: async (sessionId: string, files: File[]) => {
    set({ isUploadingFiles: true, error: null });
    const token = localStorage.getItem("auth-token");
    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));

      const response = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}rag/${sessionId}/upload`,
        {
          method: "POST",
          body: formData,
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error("Failed to upload files");

      const result = await response.json();
      set((state) => ({
        currentSession: state.currentSession
          ? {
              ...state.currentSession,
              documents: [
                ...(state.currentSession.documents || []),
                ...files.map((f) => f.name),
              ],
            }
          : null,
        isUploadingFiles: false,
      }));
    } catch (error) {
      set({ error: "Failed to upload files", isUploadingFiles: false });
      throw error;
    }
  },

  getCurrentSession: () => get().currentSession,
  clearCurrentSession: () => set({ currentSession: null }),
}));

const useRagSession = () => {
  const navigate = useNavigate();
  const state = useRagSessionStore();

  const createAndNavigate = async (
    userId: string,
    openai_api_key: string,
    title: string,
    description?: string
  ) => {
    const session = await state.createSession(
      userId,
      openai_api_key,
      title,
      description
    );
    navigate(`/rag#${session.id}`);
    return session;
  };

  return {
    ...state,
    createSession: createAndNavigate,
  };
};

export default useRagSession;
