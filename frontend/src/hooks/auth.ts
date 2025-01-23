import { useState } from 'react';
import useAuthStore from './useAuthStore';
import { dummyUsers } from '@/lib/dummyData';
import { User } from '@/lib/types';

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData extends LoginCredentials {
  name: string;
}

export const useAuth = () => {
  const { setUser, setTokens, logout: storeLogout } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (credentials: LoginCredentials) => {
    try {
      setLoading(true);
      setError(null);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Find user in dummy data
      const user = dummyUsers.find(u => u.email === credentials.email);
      
      if (!user) {
        throw new Error('Invalid credentials');
      }

      // For demo purposes, accept any password
      const dummyTokens = {
        access_token: 'dummy_access_token',
        refresh_token: 'dummy_refresh_token'
      };

      setTokens(dummyTokens);
      setUser(user);
      return { user, tokens: dummyTokens };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    try {
      setLoading(true);
      setError(null);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      if (dummyUsers.some(u => u.email === data.email)) {
        throw new Error('Email already registered');
      }

      const newUser: User = {
        id: `usr_${Math.random().toString(36).substr(2, 9)}`,
        name: data.name,
        email: data.email,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: new Date().toISOString(),
      };

      // In a real app, you would save this to the backend
      dummyUsers.push(newUser);
      return newUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    storeLogout();
  };

  return {
    login,
    register,
    logout,
    loading,
    error,
  };
};
