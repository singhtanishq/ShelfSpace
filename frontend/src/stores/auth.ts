/** Auth state (zustand): access token in memory, refresh token persisted. */

import { create } from "zustand";
import type { User } from "@/types/api";

const REFRESH_KEY = "shelfspace.refresh";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  hydrated: boolean;
  setSession: (user: User, accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  setAccessToken: (token: string) => void;
  getRefreshToken: () => string | null;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  hydrated: false,

  setSession: (user, accessToken, refreshToken) => {
    localStorage.setItem(REFRESH_KEY, refreshToken);
    set({ user, accessToken, hydrated: true });
  },

  setUser: (user) => set({ user }),

  setAccessToken: (accessToken) => set({ accessToken }),

  getRefreshToken: () => localStorage.getItem(REFRESH_KEY),

  clearSession: () => {
    localStorage.removeItem(REFRESH_KEY);
    set({ user: null, accessToken: null, hydrated: true });
  },
}));

/** Mark the store hydrated at startup (refresh token present or not). */
export function hydrateAuth() {
  if (!useAuthStore.getState().user) {
    useAuthStore.setState({ hydrated: true });
  }
}
