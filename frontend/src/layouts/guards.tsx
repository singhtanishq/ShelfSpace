import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import { authApi } from "@/api/endpoints";
import { PageLoader } from "@/components/ui/states";

/** Blocks rendering until the session has been validated against the API. */
export function RequireAuth() {
  const { accessToken, user, setUser, clearSession } = useAuthStore();
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
    queryFn: restoreSession,
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

/** Restore the session once at the app root so public pages also see the
 * signed-in state after a full page reload (the refresh token survives in
 * localStorage; the access token does not). */
export function SessionRestore() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const hasRefresh = !!useAuthStore.getState().getRefreshToken();

  useQuery({
    queryKey: ["session-restore"],
    queryFn: restoreSession,
    enabled: !accessToken && hasRefresh,
    retry: false,
    staleTime: Infinity,
    gcTime: 0,
  });

  return null;
}

async function restoreSession(): Promise<boolean> {
  const refreshToken = useAuthStore.getState().getRefreshToken();
  const resp = await axios.post("/api/v1/auth/refresh", { refresh_token: refreshToken });
  useAuthStore.getState().setSession(resp.data.user, resp.data.access_token, resp.data.refresh_token);
  return true;
}

export function RequireAdmin() {
  const user = useAuthStore((s) => s.user);
  if (user?.role !== "admin") return <Navigate to="/" replace />;
  return <Outlet />;
}

export function GuestOnly() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const location = useLocation();
  if (accessToken) {
    // If sign-in just completed, the login page's own navigate() races this
    // render-phase redirect — route to the intended destination (carried in
    // route state by RequireAuth and the guest-cart CTA) so it always wins.
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from ?? "/"} replace />;
  }
  return <Outlet />;
}

