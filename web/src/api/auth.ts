import { apiClient } from './client';
import type { LoginRequest, RegisterRequest, TokenResponse } from '@/types/user';

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const r = await apiClient.post('/auth/login', data);
    return r.data;
  },
  register: async (data: RegisterRequest): Promise<void> => {
    await apiClient.post('/auth/register', data);
  },
};
