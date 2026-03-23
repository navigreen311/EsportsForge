/**
 * NextAuth type augmentations for custom session/token fields.
 */

import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface User {
    accessToken: string;
    refreshToken: string;
    username: string;
    tier: string;
  }

  interface Session {
    accessToken: string;
    refreshToken: string;
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      username: string;
      tier: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    userId?: string;
    username?: string;
    tier?: string;
  }
}
