import { create } from 'zustand';
import type { DashboardStats } from '@/types/dashboard';
import { dashboardApi } from '@/api/dashboard';

interface DashboardState {
  stats: DashboardStats | null;
  loading: boolean;
  error: boolean;
  fetchStats: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  loading: false,
  error: false,

  fetchStats: async () => {
    set({ loading: true, error: false });
    try {
      const stats = await dashboardApi.getStats();
      set({ stats, loading: false });
    } catch {
      set({ error: true, loading: false });
    }
  },
}));