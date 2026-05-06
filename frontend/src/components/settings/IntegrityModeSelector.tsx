'use client';

import { useState } from 'react';
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
  const [pendingEnv, setPendingEnv] = useState<IntegrityEnvironment | null>(null);
  const [showAntiCheatDetail, setShowAntiCheatDetail] = useState(false);

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
                onClick={() => {
                  if (env.value === settings.environment) return;
                  setPendingEnv(env.value);
                }}
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

      {/* Anti-Cheat Status (clickable for detail) */}
      <button
        type="button"
        onClick={() => setShowAntiCheatDetail(true)}
        className="w-full rounded-lg border border-dark-700 bg-dark-800 p-4 flex items-center gap-3 hover:border-forge-500/40 transition-colors text-left"
      >
        <StatusIcon className={`w-6 h-6 ${antiCheatColors[settings.antiCheatStatus]}`} />
        <div>
          <p className="text-sm font-medium text-dark-200">Anti-Cheat Status</p>
          <p className={`text-xs font-medium capitalize ${antiCheatColors[settings.antiCheatStatus]}`}>
            {settings.antiCheatStatus} — click for details
          </p>
        </div>
      </button>

      {/* Switch-mode confirm modal */}
      {pendingEnv && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setPendingEnv(null)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-dark-50 mb-1">
              Switch to {environments.find((e) => e.value === pendingEnv)?.label} mode?
            </h3>
            <p className="text-sm text-dark-400 mb-5">
              Some AI features will be {pendingEnv === 'tournament' ? 'restricted' : 'reconfigured'}. Active mode reflects in the TopBar badge.
            </p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setPendingEnv(null)} className="rounded-lg border border-dark-600 bg-dark-800 px-4 py-2 text-sm text-dark-200 hover:bg-dark-700">Cancel</button>
              <button
                onClick={() => { onUpdate({ environment: pendingEnv }); setPendingEnv(null); }}
                className="rounded-lg bg-forge-500/15 border border-forge-500/40 px-4 py-2 text-sm font-semibold text-forge-300 hover:bg-forge-500/25"
              >
                Switch mode
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Anti-Cheat detail modal */}
      {showAntiCheatDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowAntiCheatDetail(false)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-bold text-dark-50">Anti-Cheat Details</h3>
              <button onClick={() => setShowAntiCheatDetail(false)} className="text-dark-500 hover:text-dark-200"><X className="w-5 h-5" /></button>
            </div>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-dark-400">Last verification</dt><dd className="text-dark-200">{new Date().toLocaleString()}</dd></div>
              <div className="flex justify-between"><dt className="text-dark-400">Status</dt><dd className={`font-semibold capitalize ${antiCheatColors[settings.antiCheatStatus]}`}>{settings.antiCheatStatus}</dd></div>
              <div><dt className="text-dark-400">Active services</dt><dd className="text-dark-200 mt-1 ml-2">&middot; Ricochet (Warzone)<br/>&middot; Easy Anti-Cheat (Fortnite)<br/>&middot; Vanguard (Valorant)</dd></div>
            </dl>
            <a href="/legal/anti-cheat" className="block mt-4 text-xs text-forge-400 hover:text-forge-300">View privacy policy &rarr;</a>
          </div>
        </div>
      )}
    </div>
  );
}
