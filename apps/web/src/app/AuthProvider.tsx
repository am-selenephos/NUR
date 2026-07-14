import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { MeResponse } from "@nur/shared-types";
import { api, ApiError } from "../lib/api";

type Status = "loading" | "authenticated" | "anonymous";

interface AuthState {
  status: Status;
  user: MeResponse | null;
  refresh: () => Promise<void>;
  setUser: (u: MeResponse | null) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");
  const [user, setUserState] = useState<MeResponse | null>(null);

  const refresh = useCallback(async () => {
    try {
      const me = await api.me();
      setUserState(me);
      setStatus("authenticated");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setUserState(null);
        setStatus("anonymous");
      } else {
        // network/other: treat as anonymous but don't crash the shell
        setUserState(null);
        setStatus("anonymous");
      }
    }
  }, []);

  const setUser = useCallback((u: MeResponse | null) => {
    setUserState(u);
    setStatus(u ? "authenticated" : "anonymous");
  }, []);

  const logout = useCallback(async () => {
    try { await api.logout(); } finally { setUser(null); }
  }, [setUser]);

  useEffect(() => { void refresh(); }, [refresh]);

  const value = useMemo<AuthState>(
    () => ({ status, user, refresh, setUser, logout }),
    [status, user, refresh, setUser, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
