'use client';

import { useState, useEffect } from 'react';
import { Mic } from 'lucide-react';
import { VoiceForgeService } from '@/lib/services/voiceforge';

type CheckInMode = 'voice' | 'text' | 'off';
type BriefingSpeed = 'slow' | 'normal' | 'fast';

interface RadioOption<T extends string> {
  value: T;
  label: string;
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
        </button>
      ))}
    </div>
  );
}

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
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
  );
}

export default function VoiceSettings() {
  const [enableVoiceForge, setEnableVoiceForge] = useState(true);
  const [voiceCoaching, setVoiceCoaching] = useState(true);
  const [checkInMode, setCheckInMode] = useState<CheckInMode>('voice');
  const [briefingSpeed, setBriefingSpeed] = useState<BriefingSpeed>('normal');
  const [volume, setVolume] = useState(75);
  const [available, setAvailable] = useState(false);

  useEffect(() => {
    setAvailable(VoiceForgeService.isAvailable());
  }, []);

  const checkInOptions: RadioOption<CheckInMode>[] = [
    { value: 'voice', label: 'Voice' },
    { value: 'text', label: 'Text' },
    { value: 'off', label: 'Off' },
  ];

  const speedOptions: RadioOption<BriefingSpeed>[] = [
    { value: 'slow', label: 'Slow' },
    { value: 'normal', label: 'Normal' },
    { value: 'fast', label: 'Fast' },
  ];

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Mic className="w-5 h-5 text-forge-400" />
          <h3 className="text-lg font-semibold text-dark-100">Voice Settings</h3>
        </div>
        <span className="flex items-center gap-1.5 text-xs font-medium">
          {available ? (
            <>
              <span className="text-emerald-400">VoiceForge: Connected</span>
              <span className="text-emerald-400">●</span>
            </>
          ) : (
            <>
              <span className="text-dark-500">VoiceForge: Offline</span>
              <span className="text-dark-500">○</span>
            </>
          )}
        </span>
      </div>

      <div className="space-y-6">
        {/* 1. Enable VoiceForge */}
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm font-medium text-dark-200">Enable VoiceForge</p>
          <Toggle checked={enableVoiceForge} onChange={setEnableVoiceForge} />
        </div>

        {/* 2. Voice coaching during drills */}
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm font-medium text-dark-200">Voice coaching during drills</p>
          <Toggle checked={voiceCoaching} onChange={setVoiceCoaching} />
        </div>

        {/* 3. Pre-session check-in mode */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Pre-session check-in mode
          </label>
          <RadioCards options={checkInOptions} value={checkInMode} onChange={setCheckInMode} />
        </div>

        {/* 4. Briefing speed */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Briefing speed
          </label>
          <RadioCards options={speedOptions} value={briefingSpeed} onChange={setBriefingSpeed} />
        </div>

        {/* 5. Volume */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Volume — {volume}%
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            className="w-full h-2 rounded-full appearance-none cursor-pointer bg-dark-700 accent-forge-500"
          />
          <div className="flex justify-between text-xs text-dark-500 mt-1">
            <span>0</span>
            <span>100</span>
          </div>
        </div>
      </div>
    </div>
  );
}
