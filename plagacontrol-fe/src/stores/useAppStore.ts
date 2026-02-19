// src/stores/useAppStore.ts
import { create } from 'zustand';
import { User, Company } from '@/types';

interface AppState {
  user: User | null;
  company: Company | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  sidebarOpen: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  setCompany: (company: Company | null) => void;
  setLoading: (loading: boolean) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  login: (user: User, company: Company) => void;
  logout: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  company: null,
  isAuthenticated: false,
  isLoading: false,
  sidebarOpen: true,

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  
  setCompany: (company) => set({ company }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  
  login: (user, company) => set({ 
    user, 
    company, 
    isAuthenticated: true,
    isLoading: false 
  }),
  
  logout: () => set({ 
    user: null, 
    company: null, 
    isAuthenticated: false 
  }),
}));
