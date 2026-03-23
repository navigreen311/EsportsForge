'use client';

import { useState } from 'react';
import {
  Settings,
  User,
  Gamepad2,
  Shield,
  Lock,
  Bell,
  CreditCard,
  Save,
  Loader2,
  CheckCircle,
} from 'lucide-react';
import type { SettingsTab } from '@/types/settings';
import { useSettings } from '@/hooks/useSettings';
import ProfileForm from '@/components/settings/ProfileForm';
import GameSettings from '@/components/settings/GameSettings';
import IntegrityModeSelector from '@/components/settings/IntegrityModeSelector';
import PrivacyControls from '@/components/settings/PrivacyControls';
import NotificationPreferences from '@/components/settings/NotificationPreferences';
import SubscriptionCard from '@/components/settings/SubscriptionCard';

const tabs: { id: SettingsTab; label: string; icon: typeof Settings }[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'game', label: 'Game Settings', icon: Gamepad2 },
  { id: 'integrity', label: 'Integrity Mode', icon: Shield },
  { id: 'privacy', label: 'Privacy', icon: Lock },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'subscription', label: 'Subscription', icon: CreditCard },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const {
    settings,
    isSaving,
    saveSuccess,
    updateProfile,
    updateGame,
    updateIntegrity,
    updatePrivacy,
    updateNotifications,
    saveSettings,
  } = useSettings();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-50 flex items-center gap-3">
            <Settings className="w-8 h-8 text-forge-400" />
            Settings
          </h1>
          <p className="text-dark-400 mt-1">Manage your account, preferences, and subscriptions</p>
        </div>
        <button
          onClick={saveSettings}
          disabled={isSaving}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-forge-600 text-white text-sm font-medium hover:bg-forge-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : saveSuccess ? (
            <CheckCircle className="w-4 h-4" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {isSaving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Changes'}
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-dark-700">
        <nav className="flex gap-1 -mb-px overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? 'border-forge-500 text-forge-400'
                    : 'border-transparent text-dark-500 hover:text-dark-300 hover:border-dark-600'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'profile' && (
          <ProfileForm profile={settings.profile} onUpdate={updateProfile} />
        )}
        {activeTab === 'game' && (
          <GameSettings settings={settings.game} onUpdate={updateGame} />
        )}
        {activeTab === 'integrity' && (
          <IntegrityModeSelector settings={settings.integrity} onUpdate={updateIntegrity} />
        )}
        {activeTab === 'privacy' && (
          <PrivacyControls settings={settings.privacy} onUpdate={updatePrivacy} />
        )}
        {activeTab === 'notifications' && (
          <NotificationPreferences
            preferences={settings.notifications}
            onUpdate={updateNotifications}
          />
        )}
        {activeTab === 'subscription' && (
          <SubscriptionCard currentTier={settings.subscription} />
        )}
      </div>
    </div>
  );
}
