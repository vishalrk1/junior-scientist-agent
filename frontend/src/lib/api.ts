import axios from 'axios';
import { Project, ProjectStatus } from './types';

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

export const projectApi = {
  createProject: async (project: Partial<Project>) => {
    const projectData = {
      ...project,
      api_key: project.api_key ? btoa(project.api_key) : undefined
    };
    const response = await api.post('projects', projectData);
    return response.data;
  },

  getProjects: async (status?: ProjectStatus) => {
    const response = await api.get('projects', {
      params: { status }
    });
    return response.data;
  },

  getProject: async (projectId: string) => {
    const response = await api.get(`projects/${projectId}`);
    return response.data;
  },

  updateProject: async (projectId: string, updates: Partial<Project>) => {
    const response = await api.patch(`projects/${projectId}`, updates);
    return response.data;
  },

  deleteProject: async (projectId: string) => {
    await api.delete(`projects/${projectId}`);
  },

  addDataset: async (projectId: string, dataset: any) => {
    const response = await api.post(`projects/${projectId}/dataset`, dataset);
    return response.data;
  }
};

export default api;
