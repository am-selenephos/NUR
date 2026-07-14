import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthProvider";

function Splash({ label }: { label: string }) {
  return <div className="nur-splash"><p>{label}</p></div>;
}

export function ProtectedRoute() {
  const { status } = useAuth();
  if (status === "loading") return <Splash label="Aligning your orbit…" />;
  if (status === "anonymous") return <Navigate to="/?sheet=signin" replace />;
  return <Outlet />;
}

export function PublicOnlyRoute() {
  const { status } = useAuth();
  if (status === "loading") return <Splash label="…" />;
  if (status === "authenticated") return <Navigate to="/today" replace />;
  return <Outlet />;
}
