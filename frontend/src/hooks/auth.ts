import { useState } from 'react';
import useAuthStore from './useAuthStore';
import { authApi } from '@/lib/api';
import { Tokens } from '@/lib/types';

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

      const tokenResponse = await authApi.login(credentials.email, credentials.password);
      
      const tokens: Tokens = {
        access_token: tokenResponse.access_token,
        expires_in: tokenResponse.expires_in
      };

      setTokens(tokens);
      
      // Add small delay to ensure token is set in axios interceptor
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const userResponse = await authApi.getCurrentUser();
      setUser(userResponse);
      
      return { user: userResponse, tokens };
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    try {
      setLoading(true);
      setError(null);

      const user = await authApi.register(data.name, data.email, data.password);
      return user;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Registration failed';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
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
