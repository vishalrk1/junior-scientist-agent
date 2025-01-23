import { create } from 'zustand';
import { Project, ProjectStatus } from '@/lib/types';
import { dummyProjects } from '@/lib/dummyData';

interface ProjectStore {
  projects: Project[];
  activeProjectId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setProjects: (projects: Project[]) => void;
  setActiveProject: (projectId: string | null) => void;
  addProject: (project: Project) => void;
  updateProject: (projectId: string, updates: Partial<Project>) => void;
  deleteProject: (projectId: string) => void;
  setProjectStatus: (projectId: string, status: ProjectStatus) => void;

  // Getters
  getActiveProject: () => Project | null;
  getProjectById: (projectId: string) => Project | null;
}

const useProjects = create<ProjectStore>((set, get) => ({
  projects: dummyProjects, // Initialize with dummy data
  activeProjectId: null,
  isLoading: false,
  error: null,

  setProjects: (projects) => set({ projects }),
  
  setActiveProject: (projectId) => set({ activeProjectId: projectId }),
  
  addProject: (project) => set((state) => ({
    projects: [...state.projects, project]
  })),
  
  updateProject: (projectId, updates) => set((state) => ({
    projects: state.projects.map((p) =>
      p.id === projectId ? { ...p, ...updates } : p
    )
  })),
  
  deleteProject: (projectId) => set((state) => ({
    projects: state.projects.filter((p) => p.id !== projectId),
    activeProjectId: state.activeProjectId === projectId ? null : state.activeProjectId
  })),
  
  setProjectStatus: (projectId, status) => set((state) => ({
    projects: state.projects.map((p) =>
      p.id === projectId ? { ...p, status } : p
    )
  })),

  getActiveProject: () => {
    const { projects, activeProjectId } = get();
    return projects.find((p) => p.id === activeProjectId) || null;
  },

  getProjectById: (projectId) => {
    return get().projects.find((p) => p.id === projectId) || null;
  }
}));

export default useProjects;
