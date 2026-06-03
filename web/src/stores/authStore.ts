import { create } from 'zustand';
import type { User, UpdateUserDefaultsRequest } from '@/types/user';
import { usersApi } from '@/api/users';

interface AuthState {
  token: string | null;
  user: User | null;
  setToken: (token: string) => void;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateDefaults: (data: UpdateUserDefaultsRequest) => Promise<void>;
  clearUser: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('easybx_token'),
  user: null,

  setToken: (token: string) => {
    localStorage.setItem('easybx_token', token);
    set({ token });
  },

  logout: () => {
    localStorage.removeItem('easybx_token');
    set({ token: null, user: null });
  },

  fetchUser: async () => {
    try {
      const user = await usersApi.getMe();
      set({ user });
    } catch {
      set({ user: null });
    }
  },

  updateDefaults: async (data) => {
    const user = await usersApi.updateDefaults(data);
    set({ user });
  },

  clearUser: () => set({ user: null }),
}));
