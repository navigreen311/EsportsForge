'use client';

import { useState } from 'react';
import { Info } from 'lucide-react';
import InfoTooltip from '@/components/global/InfoTooltip';
import { GAME_MODE_TOOLTIPS } from './GameSettings';
import type { GameMode } from '@/types/settings';

interface PerTitleConfigProps {
  activeTitle: string;
}

type TitleKey = 'madden-26' | 'cfb-26' | 'nba-2k26' | 'ea-fc-26' | 'mlb-26' | 'warzone' | 'fortnite';

interface TitleConfig {
  preferredMode: string;
  inputType: string;
  agentPriorities: string[];
}

const titles: { key: TitleKey; label: string }[] = [
  { key: 'madden-26', label: 'Madden 26' },
  { key: 'cfb-26', label: 'CFB 26' },
  { key: 'nba-2k26', label: 'NBA 2K26' },
  { key: 'ea-fc-26', label: 'EA FC 26' },
  { key: 'mlb-26', label: 'MLB 26' },
  { key: 'warzone', label: 'Warzone' },
  { key: 'fortnite', label: 'Fortnite' },
];

const modes = ['Ranked', 'Tournament', 'Training', 'Casual'];
const inputTypes = ['Controller', 'KBM', 'Fight Stick'];

const agentsByTitle: Record<TitleKey, string[]> = {
  'madden-26': ['GameplanAgent', 'OpponentScout', 'DrillCoach', 'SituationAnalyzer', 'MetaBot', 'TiltGuard'],
  'cfb-26': ['GameplanAgent', 'OpponentScout', 'DrillCoach', 'SituationAnalyzer', 'MetaBot', 'TiltGuard'],
  'nba-2k26': ['BuildForge', 'ShotForge', 'PositioningAI'],
  'ea-fc-26': ['SquadForge', 'TacticsForge', 'SkillForge'],
  'mlb-26': ['PitchForge', 'HitForge', 'BaserunningAI'],
  'warzone': ['ZoneForge', 'LoadoutForge', 'GunfightAI'],
  'fortnite': ['BuildForge', 'EditForge', 'ZoneForge'],
};

const defaultConfigs: Record<TitleKey, TitleConfig> = {
  'madden-26': {
    preferredMode: 'Tournament',
    inputType: 'Controller',
    agentPriorities: [...agentsByTitle['madden-26']],
  },
  'cfb-26': {
    preferredMode: 'Ranked',
    inputType: 'Controller',
    agentPriorities: [...agentsByTitle['cfb-26']],
  },
  'nba-2k26': {
    preferredMode: 'Ranked',
    inputType: 'Controller',
    agentPriorities: [...agentsByTitle['nba-2k26']],
  },
  'ea-fc-26': {
    preferredMode: 'Ranked',
    inputType: 'Controller',
    agentPriorities: [...agentsByTitle['ea-fc-26']],
  },
  'mlb-26': {
    preferredMode: 'Ranked',
    inputType: 'Controller',
    agentPriorities: [...agentsByTitle['mlb-26']],
  },
  'warzone': {
    preferredMode: 'Ranked',
    inputType: 'KBM',
    agentPriorities: [...agentsByTitle['warzone']],
  },
  'fortnite': {
    preferredMode: 'Ranked',
    inputType: 'KBM',
    agentPriorities: [...agentsByTitle['fortnite']],
  },
};

export default function PerTitleConfig({ activeTitle }: PerTitleConfigProps) {
  const [selectedTab, setSelectedTab] = useState<TitleKey>('madden-26');
  const [configs, setConfigs] = useState<Record<TitleKey, TitleConfig>>(defaultConfigs);

  const current = configs[selectedTab];
  const currentAgents = agentsByTitle[selectedTab];

  const updateConfig = (patch: Partial<TitleConfig>) => {
    setConfigs((prev) => ({
      ...prev,
      [selectedTab]: { ...prev[selectedTab], ...patch },
    }));
  };

  const toggleAgent = (agent: string) => {
    const agents = current.agentPriorities.includes(agent)
      ? current.agentPriorities.filter((a) => a !== agent)
      : [...current.agentPriorities, agent];
    updateConfig({ agentPriorities: agents });
  };

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <h3 className="text-sm font-bold text-dark-200 mb-4">Per-Title Configuration</h3>

      {/* Tab Row — horizontally scrollable */}
      <div className="overflow-x-auto mb-6 -mx-1 px-1">
        <div className="flex gap-1 min-w-max">
          {titles.map((title) => (
            <button
              key={title.key}
              onClick={() => setSelectedTab(title.key)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                selectedTab === title.key
                  ? 'bg-dark-700 text-dark-50'
                  : 'text-dark-400 hover:text-dark-200'
              }`}
            >
              {title.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-6">
        {/* Preferred Mode */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Preferred Mode
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {modes.map((mode) => {
              const tipKey = mode.toLowerCase() as GameMode;
              return (
                <InfoTooltip
                  key={mode}
                  content={GAME_MODE_TOOLTIPS[tipKey]}
                  mobileTitle={mode}
                >
                  <button
                    onClick={() => updateConfig({ preferredMode: mode })}
                    className={`relative rounded-lg border p-3 text-left text-sm font-medium transition-all cursor-help hover:bg-dark-800/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-forge-500/40 ${
                      current.preferredMode === mode
                        ? 'border-forge-500 bg-forge-500/5 text-forge-400'
                        : 'border-dark-700 bg-dark-800/50 text-dark-200 hover:border-dark-500'
                    }`}
                  >
                    <Info className="absolute top-1.5 right-1.5 h-3 w-3 text-dark-500 hover:text-dark-300 transition-colors" />
                    <span className="pr-3">{mode}</span>
                  </button>
                </InfoTooltip>
              );
            })}
          </div>
        </div>

        {/* Input Type */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Input Type
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {inputTypes.map((type) => (
              <button
                key={type}
                onClick={() => updateConfig({ inputType: type })}
                className={`rounded-lg border p-3 text-left text-sm font-medium transition-all ${
                  current.inputType === type
                    ? 'border-forge-500 bg-forge-500/5 text-forge-400'
                    : 'border-dark-700 bg-dark-800/50 text-dark-200 hover:border-dark-500'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Agent Priority */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Agent Priority
          </label>
          <div className="flex flex-wrap gap-2">
            {currentAgents.map((agent) => {
              const isSelected = current.agentPriorities.includes(agent);
              return (
                <button
                  key={agent}
                  onClick={() => toggleAgent(agent)}
                  className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
                    isSelected
                      ? 'bg-forge-500/20 text-forge-400 border-forge-500/30'
                      : 'bg-dark-800/50 text-dark-500 border-dark-700 hover:text-dark-300'
                  }`}
                >
                  {agent}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
