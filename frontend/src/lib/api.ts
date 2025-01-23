import axios from 'axios';

const BASE_URL = import.meta.env.VITE_BASE_API_URL || 'http://localhost:8000/';

const api = axios.create({
  baseURL: BASE_URL,
});

api.interceptors.request.use((config) => {
  if (config.url === 'auth/login') {
    config.headers['Content-Type'] = 'application/x-www-form-urlencoded';
  } else {
    config.headers['Content-Type'] = 'application/json';
  }

  const token = localStorage.getItem('auth-token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const response = await api.post('auth/login', formData);
    localStorage.setItem('auth-token', response.data.access_token);
    return response.data;
  },

  register: async (name: string, email: string, password: string) => {
    const response = await api.post('auth/register', {
      name,
      email,
      password,
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('auth/me');
    return response.data;
  },
};

export default api;
