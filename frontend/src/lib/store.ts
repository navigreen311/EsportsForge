/**
 * Global UI state store using Zustand.
 * Manages title selection, game mode, and sidebar visibility.
 */

import { create } from 'zustand';

export type GameTitle = 'madden26' | 'cfb26' | 'nba2k26' | 'fc26' | 'mlbtheshow26' | 'warzone' | 'fortnite' | 'ufc5' | 'pga2k25' | 'undisputed' | 'videopoker';
export type GameMode = 'ranked' | 'tournament' | 'training';
export type UserTier = 'free' | 'competitive' | 'elite' | 'team';
export type IntegrityStatus = 'safe' | 'caution' | 'restricted';

export interface TitleOption {
  id: GameTitle;
  label: string;
  icon: string;
}

export const TITLE_OPTIONS: TitleOption[] = [
  { id: 'madden26', label: 'Madden 26', icon: '🏈' },
  { id: 'cfb26', label: 'CFB 26', icon: '🎓' },
  { id: 'nba2k26', label: 'NBA 2K26', icon: '🏀' },
  { id: 'fc26', label: 'EA FC 26', icon: '⚽' },
  { id: 'mlbtheshow26', label: 'MLB 26', icon: '⚾' },
  { id: 'warzone', label: 'Warzone', icon: '🎯' },
  { id: 'fortnite', label: 'Fortnite', icon: '⚡' },
  { id: 'ufc5', label: 'UFC 5', icon: '🥊' },
  { id: 'pga2k25', label: 'PGA 2K25', icon: '⛳' },
  { id: 'undisputed', label: 'Undisputed', icon: '🥊' },
  { id: 'videopoker', label: 'Video Poker', icon: '🃏' },
];

export const MODE_CONFIG: Record<GameMode, { label: string; color: string }> = {
  ranked: { label: 'Ranked', color: 'bg-forge-500' },
  tournament: { label: 'Tournament', color: 'bg-amber-500' },
  training: { label: 'Training', color: 'bg-sky-500' },
};

export const TIER_CONFIG: Record<UserTier, { label: string; color: string; textColor: string }> = {
  free: { label: 'Free', color: 'bg-dark-600', textColor: 'text-dark-300' },
  competitive: { label: 'Competitive', color: 'bg-forge-900', textColor: 'text-forge-400' },
  elite: { label: 'Elite', color: 'bg-amber-900', textColor: 'text-amber-400' },
  team: { label: 'Team', color: 'bg-purple-900', textColor: 'text-purple-400' },
};

interface UIState {
  // Title selection
  selectedTitle: GameTitle;
  setTitle: (title: GameTitle) => void;

  // Game mode
  currentMode: GameMode;
  setMode: (mode: GameMode) => void;

  // Sidebar
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebarCollapse: () => void;

  // Integrity
  integrityStatus: IntegrityStatus;
  setIntegrityStatus: (status: IntegrityStatus) => void;

  // User tier (mock)
  userTier: UserTier;
  setUserTier: (tier: UserTier) => void;

  // Notifications
  unreadCount: number;
  setUnreadCount: (count: number) => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedTitle: (typeof window !== 'undefined' ? localStorage.getItem('esportsforge_active_title') as GameTitle : null) || 'madden26',
  setTitle: (title) => {
    if (typeof window !== 'undefined') localStorage.setItem('esportsforge_active_title', title);
    set({ selectedTitle: title });
  },

  currentMode: 'ranked',
  setMode: (mode) => set({ currentMode: mode }),

  sidebarOpen: false,
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebarCollapse: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  integrityStatus: 'safe',
  setIntegrityStatus: (status) => set({ integrityStatus: status }),

  userTier: 'competitive',
  setUserTier: (tier) => set({ userTier: tier }),

  unreadCount: 3,
  setUnreadCount: (count) => set({ unreadCount: count }),
}));
