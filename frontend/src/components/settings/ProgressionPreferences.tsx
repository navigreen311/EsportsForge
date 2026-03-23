'use client';

import { useState } from 'react';
import { Package } from 'lucide-react';

const paceOptions = [
  { value: 'aggressive', label: 'Aggressive', description: 'Add new content quickly' },
  { value: 'standard', label: 'Standard', description: 'Balanced progression' },
  { value: 'steady', label: 'Steady', description: 'Fully master before advancing' },
] as const;

const focusOptions = [
  { value: 'auto', label: 'Auto', description: 'ImpactRank decides' },
  { value: 'offense', label: 'Offense', description: '' },
  { value: 'defense', label: 'Defense', description: '' },
  { value: 'mechanical', label: 'Mechanical', description: '' },
  { value: 'mental', label: 'Mental', description: '' },
] as const;

const thresholdOptions = [
  { value: 'conservative', label: 'Conservative', description: '90% before moving on' },
  { value: 'standard', label: 'Standard', description: '75%' },
  { value: 'aggressive', label: 'Aggressive', description: '60%' },
] as const;

type Pace = (typeof paceOptions)[number]['value'];
type Focus = (typeof focusOptions)[number]['value'];
type Threshold = (typeof thresholdOptions)[number]['value'];

export default function ProgressionPreferences() {
  const [pace, setPace] = useState<Pace>('standard');
  const [focus, setFocus] = useState<Focus>('auto');
  const [throttle, setThrottle] = useState(true);
  const [threshold, setThreshold] = useState<Threshold>('standard');

  const cardClass = (selected: boolean) =>
    `rounded-lg border p-3 cursor-pointer transition-colors text-sm ${
      selected
        ? 'border-forge-500 bg-forge-500/5 text-dark-100'
        : 'border-dark-700 bg-dark-800/50 text-dark-400 hover:border-dark-500'
    }`;

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Package className="h-5 w-5 text-forge-400" />
        <h3 className="text-sm font-bold text-dark-200">Progression Preferences</h3>
      </div>

      <div className="space-y-6">
        {/* 1. Progression pace */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Progression pace
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {paceOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setPace(opt.value)}
                className={cardClass(pace === opt.value)}
              >
                <span className="font-medium">{opt.label}</span>
                <span className="block text-xs mt-0.5 opacity-70">{opt.description}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 2. Focus area */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Focus area
          </label>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {focusOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setFocus(opt.value)}
                className={cardClass(focus === opt.value)}
              >
                <span className="font-medium">{opt.label}</span>
                {opt.description && (
                  <span className="block text-xs mt-0.5 opacity-70">{opt.description}</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* 3. Throttle toggle */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-dark-200">
              Allow ProgressionOS to throttle new installs
            </p>
            <p className="text-xs text-dark-500 mt-0.5">
              When enabled, new content is held until current packages reach mastery threshold
            </p>
          </div>
          <button
            role="switch"
            aria-checked={throttle}
            onClick={() => setThrottle(!throttle)}
            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
              throttle ? 'bg-forge-600' : 'bg-dark-600'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition-transform ${
                throttle ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* 4. Mastery threshold before advancing */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Mastery threshold before advancing
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {thresholdOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setThreshold(opt.value)}
                className={cardClass(threshold === opt.value)}
              >
                <span className="font-medium">{opt.label}</span>
                <span className="block text-xs mt-0.5 opacity-70">{opt.description}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
