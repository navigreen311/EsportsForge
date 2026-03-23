'use client';

import { Shield, ShieldCheck, ShieldAlert, FlaskConical, Trophy, Swords, Radio, Check, X } from 'lucide-react';
import type { IntegrityModeSettings, IntegrityEnvironment, IntegrityRestriction } from '@/types/settings';

interface IntegrityModeSelectorProps {
  settings: IntegrityModeSettings;
  onUpdate: (settings: Partial<IntegrityModeSettings>) => void;
}

const environments: {
  value: IntegrityEnvironment;
  label: string;
  description: string;
  icon: typeof Shield;
  color: string;
}[] = [
  {
    value: 'offline-lab',
    label: 'Offline Lab',
    description: 'Full access. Experiment freely with all AI tools.',
    icon: FlaskConical,
    color: 'text-blue-400 border-blue-500 bg-blue-500/10',
  },
  {
    value: 'ranked',
    label: 'Ranked',
    description: 'Standard competitive. Some AI features restricted.',
    icon: Trophy,
    color: 'text-yellow-400 border-yellow-500 bg-yellow-500/10',
  },
  {
    value: 'tournament',
    label: 'Tournament',
    description: 'Strict rules. Only pre-approved tools allowed.',
    icon: Swords,
    color: 'text-red-400 border-red-500 bg-red-500/10',
  },
  {
    value: 'broadcast',
    label: 'Broadcast',
    description: 'Streaming-safe. Overlay-compatible, no opponent data shown.',
    icon: Radio,
    color: 'text-purple-400 border-purple-500 bg-purple-500/10',
  },
];

const restrictions: IntegrityRestriction[] = [
  { feature: 'Real-time AI suggestions', offlineLab: true, ranked: true, tournament: false, broadcast: false },
  { feature: 'Opponent scouting data', offlineLab: true, ranked: true, tournament: false, broadcast: false },
  { feature: 'Live play prediction', offlineLab: true, ranked: false, tournament: false, broadcast: false },
  { feature: 'Auto-audible AI', offlineLab: true, ranked: false, tournament: false, broadcast: false },
  { feature: 'Post-game analysis', offlineLab: true, ranked: true, tournament: true, broadcast: true },
  { feature: 'Drill recommendations', offlineLab: true, ranked: true, tournament: true, broadcast: true },
  { feature: 'Gameplan builder', offlineLab: true, ranked: true, tournament: true, broadcast: false },
  { feature: 'Kill sheet access', offlineLab: true, ranked: true, tournament: false, broadcast: false },
];

const antiCheatColors = {
  active: 'text-forge-400',
  inactive: 'text-dark-500',
  warning: 'text-yellow-400',
};

const antiCheatIcons = {
  active: ShieldCheck,
  inactive: Shield,
  warning: ShieldAlert,
};

export default function IntegrityModeSelector({ settings, onUpdate }: IntegrityModeSelectorProps) {
  const StatusIcon = antiCheatIcons[settings.antiCheatStatus];

  return (
    <div className="space-y-6">
      {/* Environment Selector */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-3">
          Environment
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {environments.map((env) => {
            const Icon = env.icon;
            const isSelected = settings.environment === env.value;
            return (
              <button
                key={env.value}
                onClick={() => onUpdate({ environment: env.value })}
                className={`rounded-lg border p-4 text-left transition-all ${
                  isSelected
                    ? `${env.color} ring-1`
                    : 'border-dark-600 bg-dark-800 hover:border-dark-500'
                }`}
              >
                <div className="flex items-center gap-2.5 mb-1.5">
                  <Icon
                    className={`w-5 h-5 ${
                      isSelected ? '' : 'text-dark-400'
                    }`}
                  />
                  <span
                    className={`text-sm font-bold ${
                      isSelected ? '' : 'text-dark-200'
                    }`}
                  >
                    {env.label}
                  </span>
                </div>
                <p className="text-xs text-dark-400">{env.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Feature Restrictions Preview */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 overflow-hidden">
        <div className="px-4 py-3 border-b border-dark-700">
          <h3 className="text-sm font-bold text-dark-200">Feature Access by Mode</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700">
                <th className="text-left py-2.5 px-4 text-dark-500 font-medium text-xs uppercase tracking-wider">
                  Feature
                </th>
                {environments.map((env) => (
                  <th
                    key={env.value}
                    className={`text-center py-2.5 px-3 text-xs font-medium uppercase tracking-wider ${
                      settings.environment === env.value ? 'text-forge-400' : 'text-dark-500'
                    }`}
                  >
                    {env.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {restrictions.map((r) => (
                <tr key={r.feature} className="border-b border-dark-800 last:border-0">
                  <td className="py-2.5 px-4 text-dark-300 text-xs">{r.feature}</td>
                  {(['offlineLab', 'ranked', 'tournament', 'broadcast'] as const).map((env) => (
                    <td key={env} className="text-center py-2.5 px-3">
                      {r[env] ? (
                        <Check className="w-4 h-4 text-forge-400 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-red-400/60 mx-auto" />
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Anti-Cheat Status */}
      <div className="rounded-lg border border-dark-700 bg-dark-800 p-4 flex items-center gap-3">
        <StatusIcon className={`w-6 h-6 ${antiCheatColors[settings.antiCheatStatus]}`} />
        <div>
          <p className="text-sm font-medium text-dark-200">Anti-Cheat Status</p>
          <p className={`text-xs font-medium capitalize ${antiCheatColors[settings.antiCheatStatus]}`}>
            {settings.antiCheatStatus}
          </p>
        </div>
      </div>
    </div>
  );
}
