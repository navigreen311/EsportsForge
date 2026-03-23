'use client';

import { useState } from 'react';
import { Shield } from 'lucide-react';

type CheckInPrompt = 'every-session' | 'first-session' | 'off';
type Sensitivity = 'aggressive' | 'standard' | 'minimal';
type MoodOptions = 'all-5' | 'simplified';
type WarningContext = 'drills' | 'ranked' | 'both' | 'neither';

interface RadioOption<T extends string> {
  value: T;
  label: string;
  description?: string;
}

function RadioCards<T extends string>({
  options,
  value,
  onChange,
}: {
  options: RadioOption<T>[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`rounded-lg border p-3 cursor-pointer transition-colors text-sm ${
            value === opt.value
              ? 'border-forge-500 bg-forge-500/5 text-dark-100'
              : 'border-dark-700 bg-dark-800/50 text-dark-400 hover:border-dark-500'
          }`}
        >
          <span className="font-medium">{opt.label}</span>
          {opt.description && (
            <span className="block text-xs mt-0.5 opacity-70">{opt.description}</span>
          )}
        </button>
      ))}
    </div>
  );
}

export default function TiltGuardConfig() {
  const [checkIn, setCheckIn] = useState<CheckInPrompt>('first-session');
  const [sensitivity, setSensitivity] = useState<Sensitivity>('standard');
  const [moodOptions, setMoodOptions] = useState<MoodOptions>('all-5');
  const [warningContext, setWarningContext] = useState<WarningContext>('both');
  const [sessionEndReflection, setSessionEndReflection] = useState(true);

  const checkInOptions: RadioOption<CheckInPrompt>[] = [
    { value: 'every-session', label: 'Every session' },
    { value: 'first-session', label: 'First session of day' },
    { value: 'off', label: 'Off' },
  ];

  const sensitivityOptions: RadioOption<Sensitivity>[] = [
    { value: 'aggressive', label: 'Aggressive', description: 'Intervene early' },
    { value: 'standard', label: 'Standard' },
    { value: 'minimal', label: 'Minimal', description: 'Rarely' },
  ];

  const moodOpts: RadioOption<MoodOptions>[] = [
    { value: 'all-5', label: 'All 5' },
    { value: 'simplified', label: 'Simplified', description: '3 options' },
  ];

  const warningOpts: RadioOption<WarningContext>[] = [
    { value: 'drills', label: 'Drills' },
    { value: 'ranked', label: 'Ranked' },
    { value: 'both', label: 'Both' },
    { value: 'neither', label: 'Neither' },
  ];

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-6">
        <Shield className="w-5 h-5 text-amber-400" />
        <h3 className="text-lg font-semibold text-dark-100">TiltGuard Configuration</h3>
      </div>

      <div className="space-y-6">
        {/* 1. Check-in prompt */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Check-in prompt
          </label>
          <RadioCards options={checkInOptions} value={checkIn} onChange={setCheckIn} />
        </div>

        {/* 2. Intervention sensitivity */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Intervention sensitivity
          </label>
          <RadioCards options={sensitivityOptions} value={sensitivity} onChange={setSensitivity} />
        </div>

        {/* 3. Mood options shown */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Mood options shown
          </label>
          <RadioCards options={moodOpts} value={moodOptions} onChange={setMoodOptions} />
        </div>

        {/* 4. Show TiltGuard warnings during */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Show TiltGuard warnings during:
          </label>
          <RadioCards options={warningOpts} value={warningContext} onChange={setWarningContext} />
        </div>

        {/* 5. Session end reflection prompt — toggle */}
        <div className="flex items-center justify-between gap-4 pt-2">
          <div>
            <p className="text-sm font-medium text-dark-200">Session end reflection prompt</p>
            <p className="text-xs text-dark-500 mt-0.5">
              Show a reflection prompt when you finish a session
            </p>
          </div>
          <button
            role="switch"
            aria-checked={sessionEndReflection}
            onClick={() => setSessionEndReflection(!sessionEndReflection)}
            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
              sessionEndReflection ? 'bg-forge-600' : 'bg-dark-600'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition-transform ${
                sessionEndReflection ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
