import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Tokens } from '@/lib/types';
import api from '@/lib/api';

interface AuthState {
  user: User | null;
  tokens: Tokens | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setTokens: (tokens: Tokens | null) => void;
  logout: () => void;
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setTokens: (tokens) => {
        set({ tokens });
        if (tokens?.access_token) {
          localStorage.setItem('auth-token', tokens.access_token);
          api.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`;
        } else {
          localStorage.removeItem('auth-token');
          delete api.defaults.headers.common['Authorization'];
        }
      },
      logout: () => {
        localStorage.removeItem('auth-token');
        delete api.defaults.headers.common['Authorization'];
        set({ user: null, tokens: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);

export default useAuthStore;
