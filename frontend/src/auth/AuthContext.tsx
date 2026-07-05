import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import * as authApi from "@/api/auth";
import type { LoginPayload, RegisterPayload, UserPublic } from "@/types/auth";

interface AuthContextValue {
  user: UserPublic | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await authApi.fetchCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));

    const onExpired = () => setUser(null);
    window.addEventListener("ams:session-expired", onExpired);
    return () => window.removeEventListener("ams:session-expired", onExpired);
  }, [refreshUser]);

  const handleLogin = useCallback(async (payload: LoginPayload) => {
    const response = await authApi.login(payload);
    setUser(response.user);
  }, []);

  const handleRegister = useCallback(async (payload: RegisterPayload) => {
    await authApi.register(payload);
    await handleLogin({ email: payload.email, password: payload.password });
  }, [handleLogin]);

  const handleLogout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
