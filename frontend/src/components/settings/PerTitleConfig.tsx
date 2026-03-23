'use client';

import { useState } from 'react';

interface PerTitleConfigProps {
  activeTitle: string;
}

type TitleKey = 'madden-26' | 'cfb-26';

interface TitleConfig {
  preferredMode: string;
  inputType: string;
  agentPriorities: string[];
}

const titles: { key: TitleKey; label: string }[] = [
  { key: 'madden-26', label: 'Madden 26' },
  { key: 'cfb-26', label: 'CFB 26' },
];

const modes = ['Ranked', 'Tournament', 'Training', 'Casual'];
const inputTypes = ['Controller', 'KBM', 'Fight Stick'];
const allAgents = [
  'GameplanAgent',
  'OpponentScout',
  'DrillCoach',
  'SituationAnalyzer',
  'MetaBot',
  'TiltGuard',
];

const defaultConfigs: Record<TitleKey, TitleConfig> = {
  'madden-26': {
    preferredMode: 'Tournament',
    inputType: 'Controller',
    agentPriorities: [...allAgents],
  },
  'cfb-26': {
    preferredMode: 'Ranked',
    inputType: 'Controller',
    agentPriorities: [...allAgents],
  },
};

export default function PerTitleConfig({ activeTitle }: PerTitleConfigProps) {
  const [selectedTab, setSelectedTab] = useState<TitleKey>('madden-26');
  const [configs, setConfigs] = useState<Record<TitleKey, TitleConfig>>(defaultConfigs);

  const current = configs[selectedTab];

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

      {/* Tab Row */}
      <div className="flex gap-1 mb-6">
        {titles.map((title) => (
          <button
            key={title.key}
            onClick={() => setSelectedTab(title.key)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              selectedTab === title.key
                ? 'bg-dark-700 text-dark-50'
                : 'text-dark-400 hover:text-dark-200'
            }`}
          >
            {title.label}
          </button>
        ))}
      </div>

      <div className="space-y-6">
        {/* Preferred Mode */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Preferred Mode
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {modes.map((mode) => (
              <button
                key={mode}
                onClick={() => updateConfig({ preferredMode: mode })}
                className={`rounded-lg border p-3 text-left text-sm font-medium transition-all ${
                  current.preferredMode === mode
                    ? 'border-forge-500 bg-forge-500/5 text-forge-400'
                    : 'border-dark-700 bg-dark-800/50 text-dark-200 hover:border-dark-500'
                }`}
              >
                {mode}
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
            {allAgents.map((agent) => {
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
