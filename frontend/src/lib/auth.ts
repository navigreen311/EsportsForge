/**
 * NextAuth configuration with credentials provider calling FastAPI backend.
 */

import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import type { AuthTokens, User } from "@/types/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          // Authenticate against FastAPI backend
          const tokenRes = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!tokenRes.ok) {
            return null;
          }

          const tokens: AuthTokens = await tokenRes.json();

          // Fetch user profile with the new access token
          const userRes = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
            headers: { Authorization: `Bearer ${tokens.access_token}` },
          });

          if (!userRes.ok) {
            return null;
          }

          const user: User = await userRes.json();

          return {
            id: user.id,
            email: user.email,
            name: user.display_name || user.username,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            username: user.username,
            tier: user.tier,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // On initial sign-in, persist tokens and user data into the JWT
      if (user) {
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.userId = user.id;
        token.username = user.username;
        token.tier = user.tier;
      }
      return token;
    },
    async session({ session, token }) {
      // Expose custom fields on the session object
      session.accessToken = token.accessToken as string;
      session.refreshToken = token.refreshToken as string;
      session.user = {
        ...session.user,
        id: token.userId as string,
        username: token.username as string,
        tier: token.tier as string,
      };
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 60, // 30 minutes to match access token expiry
  },
  secret: process.env.NEXTAUTH_SECRET,
};
