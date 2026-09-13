/** Axios instance with automatic access-token refresh on 401. */

import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import type { ApiError } from "@/types/api";

export const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const store = useAuthStore.getState();
  const refreshToken = store.getRefreshToken();
  if (!refreshToken) return null;
  try {
    const resp = await axios.post("/api/v1/auth/refresh", { refresh_token: refreshToken });
    const { access_token, refresh_token, user } = resp.data;
    store.setSession(user, access_token, refresh_token);
    return access_token;
  } catch {
    store.clearSession();
    return null;
  }
}

api.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retried) {
      original._retried = true;
      refreshPromise = refreshPromise ?? refreshAccessToken().finally(() => (refreshPromise = null));
      const token = await refreshPromise;
      if (token) {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  }
);

/** Extract a human-readable message from an API error response. */
export function apiErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError | undefined;
    if (data?.error?.message) return data.error.message;
    if (error.message) return error.message;
  }
  return fallback;
}
