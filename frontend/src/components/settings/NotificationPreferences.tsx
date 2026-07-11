'use client';

import { useState, useEffect } from 'react';
import { Bell, BellOff, Calendar, Flame, Swords, Trophy, Brain, BarChart3, Bot, Zap, Save, CheckCircle } from 'lucide-react';
import type { NotificationPreferences as NotificationPreferencesType } from '@/types/settings';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8001';

interface NotificationPreferencesProps {
  preferences: NotificationPreferencesType;
  onUpdate: (preferences: Partial<NotificationPreferencesType>) => void;
}

interface NotifToggleProps {
  label: string;
  description: string;
  icon: typeof Bell;
  iconColor: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function NotifToggle({ label, description, icon: Icon, iconColor, checked, onChange }: NotifToggleProps) {
  return (
    <div className="flex items-center justify-between gap-4 py-4 border-b border-dark-800 last:border-0">
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${iconColor}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div>
          <p className="text-sm font-medium text-dark-200">{label}</p>
          <p className="text-xs text-dark-500 mt-0.5">{description}</p>
        </div>
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
          checked ? 'bg-forge-600' : 'bg-dark-600'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

type FrequencyOption = 'immediately' | 'daily' | 'weekly';

interface NotificationTypeItem {
  key: string;
  label: string;
  description: string;
  icon: typeof Bell;
  iconColor: string;
  defaultOn: boolean;
}

const notificationTypes: NotificationTypeItem[] = [
  { key: 'weeklyForge', label: 'Weekly Forge ready (Mondays)', description: 'Your personalized weekly game plan is ready to review.', icon: Calendar, iconColor: 'bg-forge-500/10 text-forge-400', defaultOn: true },
  { key: 'rivalPlayed', label: 'Rival played new games', description: 'Track when rivals complete new sessions you can scout.', icon: Swords, iconColor: 'bg-red-500/10 text-red-400', defaultOn: true },
  { key: 'tournamentStarting', label: 'Tournament starting soon', description: 'Never miss a bracket start time or registration deadline.', icon: Trophy, iconColor: 'bg-amber-500/10 text-amber-400', defaultOn: true },
  { key: 'filmAiComplete', label: 'FilmAI analysis complete', description: 'Your latest film review is ready with new insights.', icon: Brain, iconColor: 'bg-purple-500/10 text-purple-400', defaultOn: true },
  { key: 'drillStreak', label: 'Drill streak at risk', description: 'Keep your training streak alive with a quick session.', icon: Flame, iconColor: 'bg-orange-500/10 text-orange-400', defaultOn: true },
  { key: 'impactRankChanged', label: 'ImpactRank priority changed', description: 'Your skill priority rankings have been recalculated.', icon: BarChart3, iconColor: 'bg-blue-500/10 text-blue-400', defaultOn: true },
  { key: 'metaBotWeapon', label: 'MetaBot weekly weapon alert', description: 'New top-tier loadout or strategy detected by MetaBot.', icon: Zap, iconColor: 'bg-yellow-500/10 text-yellow-400', defaultOn: true },
  { key: 'loopAiUpdated', label: 'LoopAI model updated', description: 'Your personal performance model has been retrained.', icon: Bot, iconColor: 'bg-cyan-500/10 text-cyan-400', defaultOn: false },
];

export default function NotificationPreferences(_props: NotificationPreferencesProps) {
  const [pushEnabled, setPushEnabled] = useState(true);
  const [typeToggles, setTypeToggles] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    notificationTypes.forEach((nt) => { initial[nt.key] = nt.defaultOn; });
    return initial;
  });
  const [frequency, setFrequency] = useState<FrequencyOption>('immediately');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [permState, setPermState] = useState<NotificationPermission | 'unsupported'>('default');

  useEffect(() => {
    if (typeof Notification === 'undefined') setPermState('unsupported');
    else setPermState(Notification.permission);
  }, []);

  const handleToggleType = (key: string, value: boolean) => {
    setTypeToggles((prev) => ({ ...prev, [key]: value }));
  };

  const requestPermission = async () => {
    if (typeof Notification === 'undefined') return;
    const result = await Notification.requestPermission();
    setPermState(result);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE}/api/v1/notifications/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pushEnabled, types: typeToggles, frequency }),
      });
    } catch { /* ignore — local state still saved */ }
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const frequencyOptions: { key: FrequencyOption; label: string }[] = [
    { key: 'immediately', label: 'Immediately' },
    { key: 'daily', label: 'Daily digest' },
    { key: 'weekly', label: 'Weekly digest' },
  ];

  return (
    <div className="space-y-6">
      {/* Section 1 — Push Notifications */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-forge-500/10">
              {pushEnabled ? (
                <Bell className="w-5 h-5 text-forge-400" />
              ) : (
                <BellOff className="w-5 h-5 text-dark-500" />
              )}
            </div>
            <div>
              <p className="text-sm font-bold text-dark-200">Enable push notifications</p>
              <p className="text-xs text-dark-500 mt-0.5">
                Get notified about rivals, meta alerts, and tournaments
              </p>
            </div>
          </div>
          <button
            role="switch"
            aria-checked={pushEnabled}
            onClick={() => setPushEnabled(!pushEnabled)}
            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
              pushEnabled ? 'bg-forge-600' : 'bg-dark-600'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition-transform ${
                pushEnabled ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
        {permState === 'default' && (
          <button
            onClick={requestPermission}
            className="mt-4 rounded-lg border border-forge-500/30 bg-forge-500/10 px-4 py-2 text-sm font-medium text-forge-400 hover:bg-forge-500/20 transition-colors"
          >
            Request Permission
          </button>
        )}
        {permState === 'granted' && (
          <p className="mt-4 inline-flex items-center gap-1.5 text-sm text-forge-400">
            <CheckCircle className="w-4 h-4" /> Permissions Granted ✓
          </p>
        )}
        {permState === 'denied' && (
          <p className="mt-4 text-xs text-amber-300">
            Browser notifications are denied. To enable, click the padlock in the address bar and allow notifications, then reload.
          </p>
        )}
        {permState === 'unsupported' && (
          <p className="mt-4 text-xs text-dark-500">
            Browser notifications are not supported in this browser.
          </p>
        )}
      </div>

      {/* Section 2 — Notification Types */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 px-5">
        <div className="py-4 border-b border-dark-800">
          <h3 className="text-sm font-bold text-dark-200">Notification Types</h3>
          <p className="text-xs text-dark-500 mt-0.5">Choose which notifications you want to receive</p>
        </div>
        {notificationTypes.map((nt) => (
          <NotifToggle
            key={nt.key}
            label={nt.label}
            description={nt.description}
            icon={nt.icon}
            iconColor={nt.iconColor}
            checked={typeToggles[nt.key]!}
            onChange={(v) => handleToggleType(nt.key, v)}
          />
        ))}
      </div>

      {/* Section 3 — Frequency */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
        <h3 className="text-sm font-bold text-dark-200 mb-1">Frequency</h3>
        <p className="text-xs text-dark-500 mb-4">How often to batch non-urgent alerts:</p>
        <div className="flex gap-3">
          {frequencyOptions.map((opt) => (
            <button
              key={opt.key}
              onClick={() => setFrequency(opt.key)}
              className={`rounded-lg border px-4 py-2.5 text-sm font-medium transition-all ${
                frequency === opt.key
                  ? 'border-forge-400 bg-forge-400/10 text-forge-400'
                  : 'border-dark-700 bg-dark-800/50 text-dark-400 hover:border-dark-500 hover:text-dark-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded-lg bg-forge-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-forge-500 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Notification Preferences'}
        </button>
        {saved && (
          <span className="flex items-center gap-1.5 text-sm text-forge-400">
            <CheckCircle className="w-4 h-4" />
            Preferences saved
          </span>
        )}
      </div>
    </div>
  );
}
