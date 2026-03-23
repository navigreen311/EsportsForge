/**
 * Custom hook for authentication state and actions.
 */

"use client";

import { useSession, signIn, signOut } from "next-auth/react";
import { useCallback, useMemo } from "react";
import type { AuthState, LoginCredentials, RegisterCredentials } from "@/types/auth";
import api from "@/lib/api";

export function useAuth() {
  const { data: session, status } = useSession();

  const authState: AuthState = useMemo(
    () => ({
      user: session?.user
        ? {
            id: session.user.id,
            email: session.user.email || "",
            username: session.user.username,
            display_name: session.user.name || null,
            tier: session.user.tier as AuthState["user"] extends null ? never : NonNullable<AuthState["user"]>["tier"],
            is_active: true,
            is_verified: false,
            created_at: "",
            updated_at: "",
          }
        : null,
      isAuthenticated: status === "authenticated",
      isLoading: status === "loading",
      error: null,
    }),
    [session, status]
  );

  const login = useCallback(async (credentials: LoginCredentials) => {
    const result = await signIn("credentials", {
      redirect: false,
      email: credentials.email,
      password: credentials.password,
    });
    if (result?.error) {
      throw new Error("Invalid email or password");
    }
    return result;
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials) => {
    // Register via FastAPI, then auto-login
    const res = await api.post("/auth/register", credentials);
    if (res.status === 201) {
      return login({ email: credentials.email, password: credentials.password });
    }
    throw new Error("Registration failed");
  }, [login]);

  const logout = useCallback(async () => {
    await signOut({ callbackUrl: "/login" });
  }, []);

  return {
    ...authState,
    login,
    register,
    logout,
    session,
  };
}
