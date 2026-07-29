import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { clearTokens, hydrateTokens, setTokens, type Tokens } from "./tokenStore";

type UserOut = components["schemas"]["UserOut"];

type AuthState = {
  isHydrating: boolean;
  isAuthenticated: boolean;
  user: UserOut | null;
  login: (tokens: Tokens) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isHydrating, setHydrating] = useState(true);
  const [user, setUser] = useState<UserOut | null>(null);

  async function loadUser() {
    const { data, error } = await api.GET("/v1/users/me");
    if (error) {
      await clearTokens();
      setUser(null);
      return;
    }
    setUser(data);
  }

  useEffect(() => {
    (async () => {
      const tokens = await hydrateTokens();
      if (tokens) await loadUser();
      setHydrating(false);
    })();
  }, []);

  async function login(tokens: Tokens) {
    await setTokens(tokens);
    await loadUser();
  }

  async function logout() {
    await clearTokens();
    setUser(null);
  }

  const value = useMemo<AuthState>(
    () => ({
      isHydrating,
      isAuthenticated: user !== null,
      user,
      login,
      logout,
      refreshUser: loadUser,
    }),
    [isHydrating, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
