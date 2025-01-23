import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Tokens } from '@/lib/types';
import { dummyUsers } from '@/lib/dummyData';

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
      user: dummyUsers[0],
      tokens: null,
      isAuthenticated: true,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setTokens: (tokens) => set({ tokens }),
      logout: () => set({ user: null, tokens: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
    }
  )
);

export default useAuthStore;
