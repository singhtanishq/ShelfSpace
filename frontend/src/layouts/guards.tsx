import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import { authApi } from "@/api/endpoints";
import { PageLoader } from "@/components/ui/states";

/** Blocks rendering until the session has been validated against the API. */
export function RequireAuth() {
  const { accessToken, user, setSession, setUser, clearSession } = useAuthStore();
  const location = useLocation();
  const hasRefresh = !!useAuthStore.getState().getRefreshToken();

  // Validate the token once per mount; the interceptor refreshes on 401.
  const { isLoading, isError } = useQuery({
    queryKey: ["me"],
    queryFn: () => authApi.me().then((r) => { setUser(r.data); return r.data; }),
    enabled: !!accessToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  // Restore the session from the persisted refresh token after a page reload.
  const { isPending: restoring } = useQuery({
    queryKey: ["session-restore"],
    queryFn: async () => {
      const refreshToken = useAuthStore.getState().getRefreshToken();
      const resp = await axios.post("/api/v1/auth/refresh", { refresh_token: refreshToken });
      setSession(resp.data.user, resp.data.access_token, resp.data.refresh_token);
      return true;
    },
    enabled: !accessToken && hasRefresh,
    retry: false,
    staleTime: Infinity,
    gcTime: 0,
  });

  useEffect(() => {
    if (isError) clearSession();
  }, [isError, clearSession]);

  if (accessToken && (isLoading || (!user && !isError))) return <PageLoader label="Checking your session…" />;
  if (!accessToken && hasRefresh && restoring) return <PageLoader label="Signing you back in…" />;
  if (!accessToken) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <Outlet />;
}

export function RequireAdmin() {
  const user = useAuthStore((s) => s.user);
  if (user?.role !== "admin") return <Navigate to="/" replace />;
  return <Outlet />;
}

export function GuestOnly() {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (accessToken) return <Navigate to="/" replace />;
  return <Outlet />;
}

