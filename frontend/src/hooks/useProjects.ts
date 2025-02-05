import { create } from 'zustand';
import { Project, ProjectStatus } from '@/lib/types';
import { projectApi } from '@/lib/api';

interface ProjectStore {
  projects: Project[];
  activeProjectId: string | null;
  isLoading: boolean;
  error: string | null;

  fetchProjects: (status?: ProjectStatus) => Promise<void>;
  createProject: (project: Partial<Project>) => Promise<Project>;
  updateProject: (projectId: string, updates: Partial<Project>) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  setActiveProject: (projectId: string | null) => void;
  addDataset: (projectId: string, dataset: any) => Promise<void>;

  getActiveProject: () => Project | null;
  getProjectById: (projectId: string) => Project | null;
}

const useProjects = create<ProjectStore>((set, get) => ({
  projects: [],
  activeProjectId: null,
  isLoading: false,
  error: null,

  fetchProjects: async (status?: ProjectStatus) => {
    set({ isLoading: true, error: null });
    try {
      const projects = await projectApi.getProjects(status);
      set({ projects, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch projects', isLoading: false });
    }
  },

  createProject: async (project: Partial<Project>) => {
    set({ isLoading: true, error: null });
    try {
      const newProject = await projectApi.createProject(project);
      set(state => ({
        projects: [...state.projects, newProject],
        isLoading: false
      }));
      return newProject;
    } catch (error) {
      set({ error: 'Failed to create project', isLoading: false });
      throw error;
    }
  },

  updateProject: async (projectId: string, updates: Partial<Project>) => {
    set({ isLoading: true, error: null });
    try {
      const updatedProject = await projectApi.updateProject(projectId, updates);
      set(state => ({
        projects: state.projects.map(p => 
          p.id === projectId ? updatedProject : p
        ),
        isLoading: false
      }));
    } catch (error) {
      set({ error: 'Failed to update project', isLoading: false });
      throw error;
    }
  },

  deleteProject: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await projectApi.deleteProject(projectId);
      set(state => ({
        projects: state.projects.filter(p => p.id !== projectId),
        activeProjectId: state.activeProjectId === projectId ? null : state.activeProjectId,
        isLoading: false
      }));
    } catch (error) {
      set({ error: 'Failed to delete project', isLoading: false });
      throw error;
    }
  },

  setActiveProject: (projectId) => set({ activeProjectId: projectId }),

  addDataset: async (projectId: string, dataset: any) => {
    set({ isLoading: true, error: null });
    try {
      await projectApi.addDataset(projectId, dataset);
      const updatedProject = await projectApi.getProject(projectId);
      set(state => ({
        projects: state.projects.map(p => 
          p.id === projectId ? updatedProject : p
        ),
        isLoading: false
      }));
    } catch (error) {
      set({ error: 'Failed to add dataset', isLoading: false });
      throw error;
    }
  },

  getActiveProject: () => {
    const { projects, activeProjectId } = get();
    return projects.find(p => p.id === activeProjectId) || null;
  },

  getProjectById: (projectId) => {
    return get().projects.find(p => p.id === projectId) || null;
  }
}));

export default useProjects;
