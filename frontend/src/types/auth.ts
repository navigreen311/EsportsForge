/** TypeScript types for authentication and user data. */

export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string | null;
  tier: UserTier;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export type UserTier = "free" | "competitive" | "elite" | "team";

export interface UserProfile extends User {
  title_limit: number | null;
}

export interface UserPublic {
  id: string;
  username: string;
  display_name: string | null;
  tier: UserTier;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  username: string;
  password: string;
  display_name?: string;
}
