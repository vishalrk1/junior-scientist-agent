import { create } from "zustand";
import useRagSession from "./useRagSession";

export interface FileState {
  files: File[];
  maxFiles: number;
  isUploading: boolean;
  addFiles: (newFiles: File[]) => void;
  removeFile: (index: number) => void;
  clearFiles: () => void;
  setIsUploading: (status: boolean) => void;
  uploadFiles: () => Promise<void>;
  currentSessionId: string | null;
  uploadToRag: (sessionId: string) => Promise<void>;
  setCurrentSessionId: (sessionId: string | null) => void;
}

const MAX_FILES = 5;

const useFiles = create<FileState>((set, get) => ({
  files: [],
  maxFiles: MAX_FILES,
  isUploading: false,
  currentSessionId: null,

  addFiles: (newFiles) => {
    set((state) => ({
      files: [...state.files, ...newFiles].slice(0, state.maxFiles),
    }));
  },

  removeFile: (index) => {
    set((state) => ({
      files: state.files.filter((_, i) => i !== index),
    }));
  },

  clearFiles: () => {
    set({ files: [] });
  },

  setIsUploading: (status) => {
    set({ isUploading: status });
  },

  setCurrentSessionId: (sessionId) => {
    set({ currentSessionId: sessionId });
  },

  uploadToRag: async (sessionId: string) => {
    const { files, setIsUploading, clearFiles } = get();
    if (files.length === 0) return;

    setIsUploading(true);
    try {
      await useRagSession.getState().uploadFiles(sessionId, files);
      clearFiles();
    } catch (error) {
      console.error('RAG upload failed:', error);
      throw error;
    } finally {
      setIsUploading(false);
    }
  },

  uploadFiles: async () => {
    const { files, currentSessionId, uploadToRag, setIsUploading, clearFiles } = get();
    if (files.length === 0) return;

    setIsUploading(true);
    try {
      if (currentSessionId) {
        await uploadToRag(currentSessionId);
      } else {
        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });
        if (response.ok) {
          clearFiles();
        }
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  },
}));

export default useFiles;
