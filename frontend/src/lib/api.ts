/**
 * Axios client configured with base URL and JWT interceptor.
 * Automatically attaches the access token from NextAuth session.
 */

import axios from "axios";
import { getSession } from "next-auth/react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach JWT token
api.interceptors.request.use(async (config) => {
  const session = await getSession();
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`;
  }
  return config;
});

// Response interceptor: handle 401 globally
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired — NextAuth will handle refresh via its own mechanism
      if (typeof window !== "undefined") {
        const { signOut } = await import("next-auth/react");
        await signOut({ callbackUrl: "/login" });
      }
    }
    return Promise.reject(error);
  }
);

export default api;
