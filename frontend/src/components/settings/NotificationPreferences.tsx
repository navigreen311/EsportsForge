'use client';

import { Bell, FileText, Clock, AlertTriangle, Award, Trophy } from 'lucide-react';
import type { NotificationPreferences as NotificationPreferencesType } from '@/types/settings';

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

export default function NotificationPreferences({ preferences, onUpdate }: NotificationPreferencesProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 px-5">
      <NotifToggle
        label="Meta Alerts"
        description="Get notified when the meta shifts for your active title."
        icon={Bell}
        iconColor="bg-forge-500/10 text-forge-400"
        checked={preferences.metaAlerts}
        onChange={(v) => onUpdate({ metaAlerts: v })}
      />
      <NotifToggle
        label="Patch Notes"
        description="Receive updates when new game patches or EsportsForge updates drop."
        icon={FileText}
        iconColor="bg-blue-500/10 text-blue-400"
        checked={preferences.patchNotes}
        onChange={(v) => onUpdate({ patchNotes: v })}
      />
      <NotifToggle
        label="Session Reminders"
        description="Reminders to practice based on your training schedule."
        icon={Clock}
        iconColor="bg-purple-500/10 text-purple-400"
        checked={preferences.sessionReminders}
        onChange={(v) => onUpdate({ sessionReminders: v })}
      />
      <NotifToggle
        label="Tilt Warnings"
        description="LoopAI alerts when it detects declining performance patterns."
        icon={AlertTriangle}
        iconColor="bg-yellow-500/10 text-yellow-400"
        checked={preferences.tiltWarnings}
        onChange={(v) => onUpdate({ tiltWarnings: v })}
      />
      <NotifToggle
        label="Milestone Achievements"
        description="Celebrate rank-ups, win streaks, and skill breakthroughs."
        icon={Award}
        iconColor="bg-amber-500/10 text-amber-400"
        checked={preferences.milestoneAchievements}
        onChange={(v) => onUpdate({ milestoneAchievements: v })}
      />
      <NotifToggle
        label="Tournament Reminders"
        description="Never miss a bracket start time or registration deadline."
        icon={Trophy}
        iconColor="bg-red-500/10 text-red-400"
        checked={preferences.tournamentReminders}
        onChange={(v) => onUpdate({ tournamentReminders: v })}
      />
    </div>
  );
}
