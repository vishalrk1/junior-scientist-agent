import { RagSession } from "@/lib/types";
import { create } from "zustand";

interface RagSessionState {
  currentSession: RagSession | null;
  isCreatingSession: boolean;
  isUploadingFiles: boolean;
  error: string | null;

  createSession: (userId: string, title: string, openai_api_key: string, description?: string) => Promise<RagSession>;
  uploadFiles: (sessionId: string, files: File[]) => Promise<void>;
  getCurrentSession: () => RagSession | null;
  clearCurrentSession: () => void;
}

const useRagSessionStore = create<RagSessionState>((set, get) => ({
  currentSession: null,
  isCreatingSession: false,
  isUploadingFiles: false,
  error: null,

  createSession: async (userId: string, openai_api_key: string, title: string, description?: string) => {
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
      set({ currentSession: session, isCreatingSession: false });
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
  const {
    currentSession,
    isCreatingSession,
    isUploadingFiles,
    error,
    createSession,
    uploadFiles,
    getCurrentSession,
    clearCurrentSession,
  } = useRagSessionStore();

  return {
    currentSession,
    isCreatingSession,
    isUploadingFiles,
    error,
    createSession,
    uploadFiles,
    getCurrentSession,
    clearCurrentSession,
  };
};

export default useRagSession;
