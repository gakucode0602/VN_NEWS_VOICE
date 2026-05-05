import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;
  setAuth: (access: string, user: AuthUser) => void;
  updateAccessToken: (access: string) => void;
  logout: () => void;
}

interface AuthUser {
  id: number;
  username: string;
  role: string;
  avatarUrl: string | null;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,

      setAuth: (access, userData) =>
        set({
          accessToken: access,
          user: userData,
        }),

      updateAccessToken: (access) =>
        set({
          accessToken: access,
        }),

      logout: () =>
        set({
          accessToken: null,
          user: null,
        }),
    }),
    {
      name: 'admin-auth-storage', // Key lưu trên localStorage
      partialize: (state) => ({ user: state.user }), // Chỉ persist user info, KHÔNG lưu accessToken (chống XSS)
    }
  )
);
