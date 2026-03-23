'use client';

import { useState, useCallback } from 'react';
import type {
  UserSettings,
  ProfileSettings,
  GameSettings,
  IntegrityModeSettings,
  PrivacySettings,
  NotificationPreferences,
} from '@/types/settings';

const defaultSettings: UserSettings = {
  profile: {
    username: 'ForgePlayer01',
    email: 'player@esportsforge.gg',
    displayName: 'Forge Player',
    avatarUrl: null,
  },
  game: {
    activeTitle: 'madden26',
    preferredMode: 'ranked',
    inputType: 'controller',
  },
  integrity: {
    environment: 'ranked',
    antiCheatStatus: 'active',
  },
  privacy: {
    shareOpponentData: true,
    shareCommunityData: false,
    shareAnalytics: true,
  },
  notifications: {
    metaAlerts: true,
    patchNotes: true,
    sessionReminders: true,
    tiltWarnings: false,
    milestoneAchievements: true,
    tournamentReminders: true,
  },
  subscription: 'competitive',
};

export function useSettings() {
  const [settings, setSettings] = useState<UserSettings>(defaultSettings);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const updateProfile = useCallback((profile: Partial<ProfileSettings>) => {
    setSettings((prev) => ({
      ...prev,
      profile: { ...prev.profile, ...profile },
    }));
  }, []);

  const updateGame = useCallback((game: Partial<GameSettings>) => {
    setSettings((prev) => ({
      ...prev,
      game: { ...prev.game, ...game },
    }));
  }, []);

  const updateIntegrity = useCallback((integrity: Partial<IntegrityModeSettings>) => {
    setSettings((prev) => ({
      ...prev,
      integrity: { ...prev.integrity, ...integrity },
    }));
  }, []);

  const updatePrivacy = useCallback((privacy: Partial<PrivacySettings>) => {
    setSettings((prev) => ({
      ...prev,
      privacy: { ...prev.privacy, ...privacy },
    }));
  }, []);

  const updateNotifications = useCallback((notifications: Partial<NotificationPreferences>) => {
    setSettings((prev) => ({
      ...prev,
      notifications: { ...prev.notifications, ...notifications },
    }));
  }, []);

  const saveSettings = useCallback(async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    // Mock API call
    await new Promise((resolve) => setTimeout(resolve, 800));
    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  }, []);

  return {
    settings,
    isSaving,
    saveSuccess,
    updateProfile,
    updateGame,
    updateIntegrity,
    updatePrivacy,
    updateNotifications,
    saveSettings,
  };
}
