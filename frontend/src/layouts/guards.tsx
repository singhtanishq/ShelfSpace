import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";
import { authApi } from "@/api/endpoints";
import { PageLoader } from "@/components/ui/states";

/** Blocks rendering until the session has been validated against the API. */
export function RequireAuth() {
  const { accessToken, user, setUser, clearSession, hydrated } = useAuthStore();
  const location = useLocation();

  // Validate the token once per mount; the interceptor refreshes on 401.
  const { isLoading, isError } = useQuery({
    queryKey: ["me"],
    queryFn: () => authApi.me().then((r) => { setUser(r.data); return r.data; }),
    enabled: !!accessToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (isError) clearSession();
  }, [isError, clearSession]);

  if (accessToken && (isLoading || (!user && !isError))) return <PageLoader label="Checking your session…" />;
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

