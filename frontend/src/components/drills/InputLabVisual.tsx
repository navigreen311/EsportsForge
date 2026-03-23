'use client';

import { useState } from 'react';
import { Camera, Check } from 'lucide-react';

const measuredResults = [
  { label: 'Stick Efficiency', value: '81%' },
  { label: 'Over-movement', value: '9' },
  { label: 'Input Timing', value: '0.31s' },
  { label: 'Hesitation', value: '6%' },
] as const;

export default function InputLabVisual() {
  const [recording, setRecording] = useState(false);
  const [completed, setCompleted] = useState(false);

  function handleToggle() {
    if (recording) {
      setRecording(false);
      return;
    }
    setRecording(true);
    setCompleted(false);

    // Mock: drill completes after 4 seconds
    setTimeout(() => {
      setRecording(false);
      setCompleted(true);
    }, 4000);
  }

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
      {/* Header */}
      <h2 className="text-sm font-bold text-dark-300 uppercase tracking-wider mb-4 flex items-center gap-2">
        <Camera className="w-4 h-4 text-cyan-400" />
        Visual Input Analysis
      </h2>

      {/* Toggle */}
      <label className="flex items-center gap-3 cursor-pointer select-none">
        <button
          type="button"
          role="switch"
          aria-checked={recording}
          onClick={handleToggle}
          className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${
            recording ? 'bg-forge-500' : 'bg-dark-700'
          }`}
        >
          <span
            className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
              recording ? 'translate-x-[18px]' : 'translate-x-[3px]'
            }`}
          />
        </button>
        <span className="text-xs text-dark-300">
          Record this drill session for visual input analysis
        </span>
      </label>

      {/* Recording active indicator */}
      {recording && (
        <div className="mt-3 flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-pulse absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
          </span>
          <span className="text-xs font-medium text-red-400">Recording active</span>
        </div>
      )}

      {/* Anti-cheat note */}
      <p className="mt-2 text-[10px] text-dark-500">
        Recording is only active in Drill (Offline) mode
      </p>

      {/* Completed state */}
      {completed && (
        <div className="mt-4 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400">
            <Check className="w-4 h-4" />
            <span className="text-xs font-medium">
              Visual analysis completed — InputLab data updated
            </span>
          </div>

          {/* Measured results */}
          <div className="space-y-1.5">
            {measuredResults.map((m) => (
              <div
                key={m.label}
                className="flex items-center justify-between p-2 rounded-lg bg-dark-800/40"
              >
                <span className="text-xs font-medium text-dark-300">{m.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold tabular-nums text-emerald-400">
                    {m.value}
                  </span>
                  <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-emerald-400">
                    Measured
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
