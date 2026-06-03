import { apiClient } from './client';
import type { User, UpdateUserDefaultsRequest } from '@/types/user';

export const usersApi = {
  getMe: async (): Promise<User> => {
    const r = await apiClient.get('/auth/me');
    return r.data;
  },

  updateDefaults: async (data: UpdateUserDefaultsRequest): Promise<User> => {
    const r = await apiClient.put('/auth/me', data);
    return r.data;
  },
};
