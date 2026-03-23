'use client';

import { Gamepad2, Target, Joystick } from 'lucide-react';
import type { GameSettings as GameSettingsType, GameTitle, GameMode, InputType } from '@/types/settings';
import { GAME_TITLE_LABELS } from '@/types/settings';

interface GameSettingsProps {
  settings: GameSettingsType;
  onUpdate: (settings: Partial<GameSettingsType>) => void;
}

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

export default function GameSettings({ settings, onUpdate }: GameSettingsProps) {
  return (
    <div className="space-y-6">
      {/* Active Title Selector */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-1.5">
          Active Title
        </label>
        <select
          value={settings.activeTitle}
          onChange={(e) => onUpdate({ activeTitle: e.target.value as GameTitle })}
          className="w-full rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm text-dark-100 focus:border-forge-500 focus:ring-1 focus:ring-forge-500 focus:outline-none transition-colors"
        >
          {Object.entries(GAME_TITLE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <p className="text-xs text-dark-500 mt-1">
          AI agents and analytics will focus on this title.
        </p>
      </div>

      {/* Preferred Game Mode */}
      <div>
        <label className="block text-sm font-medium text-dark-300 mb-3">
          Preferred Game Mode
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {gameModes.map((mode) => (
            <button
              key={mode.value}
              onClick={() => onUpdate({ preferredMode: mode.value })}
              className={`rounded-lg border p-3 text-left transition-all ${
                settings.preferredMode === mode.value
                  ? 'border-forge-500 bg-forge-500/10 ring-1 ring-forge-500'
                  : 'border-dark-600 bg-dark-800 hover:border-dark-500'
              }`}
            >
              <p
                className={`text-sm font-medium ${
                  settings.preferredMode === mode.value
                    ? 'text-forge-400'
                    : 'text-dark-200'
                }`}
              >
                {mode.label}
              </p>
              <p className="text-xs text-dark-500 mt-0.5">{mode.description}</p>
            </button>
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
