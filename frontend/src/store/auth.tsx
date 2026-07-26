import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { tokenStore } from "@/lib/api";
import { fetchMe, login as loginRequest } from "@/lib/endpoints-api";
import type { User } from "@/types/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, if a token exists, resolve the current user (validates the token).
  useEffect(() => {
    let active = true;
    const token = tokenStore.get();
    if (!token) {
      setIsLoading(false);
      return;
    }
    fetchMe()
      .then((u) => active && setUser(u))
      .catch(() => {
        tokenStore.clear();
        if (active) setUser(null);
      })
      .finally(() => active && setIsLoading(false));
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const token = await loginRequest(username, password);
    tokenStore.set(token.access_token);
    const me = await fetchMe();
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    window.location.assign("/login");
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, isAuthenticated: !!user, isLoading, login, logout }),
    [user, isLoading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
