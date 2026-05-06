'use client';

import { Gamepad2, Target, Joystick, Lock, Info } from 'lucide-react';
import type { GameSettings as GameSettingsType, GameTitle, GameMode, InputType } from '@/types/settings';
import { GAME_TITLE_LABELS } from '@/types/settings';
import InfoTooltip from '@/components/global/InfoTooltip';

export const GAME_MODE_TOOLTIPS: Record<GameMode, string> = {
  ranked:
    'Competitive ladder play. Most AI features active. Some restrictions for fair play — no live formation prediction, no auto-audible AI. Counts toward your competitive record.',
  tournament:
    'Bracket-based competition. Stricter rules — only pre-approved AI tools allowed. No real-time AI suggestions, no opponent scouting during matches. Anti-cheat compliance enforced. Used for sanctioned events.',
  training:
    'Practice and skill building. Full AI suite available. Drills, SimLab scenarios, gameplan testing. No competitive impact. Best for learning new schemes or working on weaknesses.',
  casual:
    'Unranked play. All AI features active, no competitive pressure. Use for warm-ups, friendly matches, or trying experimental gameplans without affecting your record.',
};

interface GameSettingsProps {
  settings: GameSettingsType;
  onUpdate: (settings: Partial<GameSettingsType>) => void;
  tier?: 'free' | 'competitive' | 'elite' | 'team';
}

// Tier gating: free unlocks 2 titles, competitive 5, elite/team all
const TIER_UNLOCKS: Record<NonNullable<GameSettingsProps['tier']>, number> = {
  free: 2,
  competitive: 5,
  elite: 99,
  team: 99,
};
const TIER_REQUIRED_FOR_INDEX = (idx: number): string => {
  if (idx < 2) return 'Free';
  if (idx < 5) return 'Competitive';
  return 'Elite';
};

const gameModes: { value: GameMode; label: string; description: string }[] = [
  { value: 'ranked', label: 'Ranked', description: 'Competitive ladder play' },
  { value: 'tournament', label: 'Tournament', description: 'Bracket-based competition' },
  { value: 'training', label: 'Training', description: 'Practice and skill building' },
  { value: 'casual', label: 'Casual', description: 'Unranked play' },
];

const inputTypes: { value: InputType; label: string; icon: typeof Gamepad2 }[] = [
  { value: 'controller', label: 'Controller', icon: Gamepad2 },
  { value: 'kbm', label: 'Keyboard & Mouse', icon: Target },
  { value: 'fight-stick', label: 'Fight Stick', icon: Joystick },
];

export default function GameSettings({ settings, onUpdate, tier = 'free' }: GameSettingsProps) {
  const unlockCount = TIER_UNLOCKS[tier];
  const titleEntries = Object.entries(GAME_TITLE_LABELS);

  return (
    <div className="space-y-6">
      {/* Active Title Selector */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-1.5">
          Active Title
        </label>
        <select
          value={settings.activeTitle}
          onChange={(e) => {
            const idx = titleEntries.findIndex(([v]) => v === e.target.value);
            if (idx >= unlockCount) {
              alert(`This title requires ${TIER_REQUIRED_FOR_INDEX(idx)} tier or higher.`);
              return;
            }
            onUpdate({ activeTitle: e.target.value as GameTitle });
          }}
          className="w-full rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm text-dark-100 focus:border-forge-500 focus:ring-1 focus:ring-forge-500 focus:outline-none transition-colors"
        >
          {titleEntries.map(([value, label], idx) => {
            const locked = idx >= unlockCount;
            return (
              <option key={value} value={value} disabled={locked}>
                {locked ? `🔒 ${label} — ${TIER_REQUIRED_FOR_INDEX(idx)} tier` : label}
              </option>
            );
          })}
        </select>
        <p className="text-xs text-dark-500 mt-1 flex items-center gap-1">
          <Lock className="w-3 h-3" /> Locked titles require an upgraded tier. AI agents and analytics will focus on the active title.
        </p>
      </div>

      {/* Preferred Game Mode */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-3">
          Preferred Game Mode
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {gameModes.map((mode) => (
            <InfoTooltip
              key={mode.value}
              content={GAME_MODE_TOOLTIPS[mode.value]}
              mobileTitle={mode.label}
            >
              <button
                onClick={() => onUpdate({ preferredMode: mode.value })}
                className={`relative rounded-lg border p-3 text-left transition-all cursor-help hover:bg-dark-800/80 ${
                  settings.preferredMode === mode.value
                    ? 'border-forge-500 bg-forge-500/10 ring-1 ring-forge-500'
                    : 'border-dark-600 bg-dark-800 hover:border-dark-500'
                }`}
              >
                <Info className="absolute top-2 right-2 h-3 w-3 text-dark-500 hover:text-dark-300 transition-colors" />
                <p
                  className={`text-sm font-medium pr-4 ${
                    settings.preferredMode === mode.value
                      ? 'text-forge-400'
                      : 'text-dark-200'
                  }`}
                >
                  {mode.label}
                </p>
                <p className="text-xs text-dark-500 mt-0.5">{mode.description}</p>
              </button>
            </InfoTooltip>
          ))}
        </div>
      </div>

      {/* Input Type */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-3">
          Input Type
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {inputTypes.map((input) => {
            const Icon = input.icon;
            return (
              <button
                key={input.value}
                onClick={() => onUpdate({ inputType: input.value })}
                className={`flex items-center gap-3 rounded-lg border p-4 transition-all ${
                  settings.inputType === input.value
                    ? 'border-forge-500 bg-forge-500/10 ring-1 ring-forge-500'
                    : 'border-dark-600 bg-dark-800 hover:border-dark-500'
                }`}
              >
                <Icon
                  className={`w-5 h-5 ${
                    settings.inputType === input.value
                      ? 'text-forge-400'
                      : 'text-dark-400'
                  }`}
                />
                <span
                  className={`text-sm font-medium ${
                    settings.inputType === input.value
                      ? 'text-forge-400'
                      : 'text-dark-200'
                  }`}
                >
                  {input.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
