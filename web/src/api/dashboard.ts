import { apiClient } from './client';
import type { DashboardStats } from '@/types/dashboard';

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const r = await apiClient.get('/dashboard/stats');
    return r.data;
  },
};