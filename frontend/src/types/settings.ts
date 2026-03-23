/** TypeScript types for settings and notifications. */

import type { UserTier } from './auth';

// --- Profile ---
export interface ProfileSettings {
  username: string;
  email: string;
  displayName: string;
  avatarUrl: string | null;
}

// --- Game Settings ---
export type GameTitle =
  | 'madden26'
  | 'cfb26'
  | 'fc26'
  | 'nba2k26'
  | 'mlbtheshow26'
  | 'nhl26'
  | 'sf6'
  | 'tekken8'
  | 'mk1'
  | 'ggstrive'
  | 'valorant';

export const GAME_TITLE_LABELS: Record<GameTitle, string> = {
  madden26: 'Madden NFL 26',
  cfb26: 'EA Sports College Football 26',
  fc26: 'EA Sports FC 26',
  nba2k26: 'NBA 2K26',
  mlbtheshow26: 'MLB The Show 26',
  nhl26: 'NHL 26',
  sf6: 'Street Fighter 6',
  tekken8: 'Tekken 8',
  mk1: 'Mortal Kombat 1',
  ggstrive: 'Guilty Gear Strive',
  valorant: 'Valorant',
};

export type GameMode = 'ranked' | 'tournament' | 'training' | 'casual';
export type InputType = 'controller' | 'kbm' | 'fight-stick';

export interface GameSettings {
  activeTitle: GameTitle;
  preferredMode: GameMode;
  inputType: InputType;
}

// --- Integrity Mode ---
export type IntegrityEnvironment = 'offline-lab' | 'ranked' | 'tournament' | 'broadcast';

export interface IntegrityRestriction {
  feature: string;
  offlineLab: boolean;
  ranked: boolean;
  tournament: boolean;
  broadcast: boolean;
}

export type AntiCheatStatus = 'active' | 'inactive' | 'warning';

export interface IntegrityModeSettings {
  environment: IntegrityEnvironment;
  antiCheatStatus: AntiCheatStatus;
}

// --- Privacy ---
export interface PrivacySettings {
  shareOpponentData: boolean;
  shareCommunityData: boolean;
  shareAnalytics: boolean;
}

// --- Notifications ---
export interface NotificationPreferences {
  metaAlerts: boolean;
  patchNotes: boolean;
  sessionReminders: boolean;
  tiltWarnings: boolean;
  milestoneAchievements: boolean;
  tournamentReminders: boolean;
}

// --- Subscription ---
export interface SubscriptionTier {
  id: UserTier;
  name: string;
  price: number;
  priceLabel: string;
  titleLimit: number | string;
  features: string[];
  highlighted?: boolean;
}

// --- Combined Settings ---
export interface UserSettings {
  profile: ProfileSettings;
  game: GameSettings;
  integrity: IntegrityModeSettings;
  privacy: PrivacySettings;
  notifications: NotificationPreferences;
  subscription: UserTier;
}

// --- Notifications (Bell/Toast) ---
export type NotificationType =
  | 'meta-alert'
  | 'patch-note'
  | 'session-reminder'
  | 'tilt-warning'
  | 'milestone'
  | 'tournament-reminder'
  | 'system';

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// --- Settings Tab ---
export type SettingsTab =
  | 'profile'
  | 'identity'
  | 'playertwin'
  | 'game'
  | 'integrity'
  | 'privacy'
  | 'notifications'
  | 'subscription';
