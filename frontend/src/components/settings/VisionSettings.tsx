'use client';

import { useState, useEffect } from 'react';
import { Eye } from 'lucide-react';

const STORAGE_KEY = 'esportsforge_vision_settings';
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8001';

type ClipFormat = 'mp4' | 'gif' | 'both';
type ReplayStorage = '10' | '25' | 'unlimited';

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
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
        checked ? 'bg-forge-500' : 'bg-dark-600'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-lg ring-0 transition-transform ${
          checked ? 'translate-x-4' : 'translate-x-0'
        }`}
      />
    </button>
  );
}

export default function VisionSettings() {
  const [replayAutoAnalysis, setReplayAutoAnalysis] = useState(false);
  const [visualInputLab, setVisualInputLab] = useState(false);
  const [clipFormat, setClipFormat] = useState<ClipFormat>('mp4');
  const [replayStorage, setReplayStorage] = useState<ReplayStorage>('25');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearStatus, setClearStatus] = useState<string | null>(null);

  // Hydrate
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const d = JSON.parse(raw);
        if (typeof d.replayAutoAnalysis === 'boolean') setReplayAutoAnalysis(d.replayAutoAnalysis);
        if (typeof d.visualInputLab === 'boolean') setVisualInputLab(d.visualInputLab);
        if (d.clipFormat) setClipFormat(d.clipFormat);
        if (d.replayStorage) setReplayStorage(d.replayStorage);
      }
    } catch { /* ignore */ }
  }, []);

  // Persist (debounced backend PUT)
  useEffect(() => {
    const payload = { replayAutoAnalysis, visualInputLab, clipFormat, replayStorage };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    const t = setTimeout(() => {
      fetch(`${API_BASE}/api/v1/vision/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).catch(() => {});
    }, 400);
    return () => clearTimeout(t);
  }, [replayAutoAnalysis, visualInputLab, clipFormat, replayStorage]);

  const clipFormatOptions: RadioOption<ClipFormat>[] = [
    { value: 'mp4', label: 'MP4' },
    { value: 'gif', label: 'GIF' },
    { value: 'both', label: 'Both' },
  ];

  const storageOptions: RadioOption<ReplayStorage>[] = [
    { value: '10', label: '10 replays' },
    { value: '25', label: '25 replays' },
    { value: 'unlimited', label: 'Unlimited' },
  ];

  async function handleClearData() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/vision/replays`, { method: 'DELETE' });
      if (res.ok) setClearStatus('All replays deleted.');
      else setClearStatus('Could not reach server — local cache cleared.');
    } catch {
      setClearStatus('Network error — local cache cleared.');
    } finally {
      try { localStorage.removeItem('esportsforge_replays_cache'); } catch { /* ignore */ }
      setShowClearConfirm(false);
      setTimeout(() => setClearStatus(null), 3500);
    }
  }

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-forge-400" />
          <h3 className="text-lg font-semibold text-dark-100">Vision Settings</h3>
        </div>
        <p className="text-sm text-dark-500 mt-1 ml-7">VisionAudioForge configuration</p>
      </div>

      <div className="space-y-6">
        {/* 1. Replay auto-analysis */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-dark-200">Replay auto-analysis</p>
            <p className="text-xs text-dark-500 mt-0.5">
              Automatically analyze replays after every session
            </p>
          </div>
          <Toggle checked={replayAutoAnalysis} onChange={setReplayAutoAnalysis} />
        </div>

        {/* 2. Visual InputLab */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-dark-200">Visual InputLab</p>
            <p className="text-xs text-dark-500 mt-0.5">
              Enable visual input recording during drills (Offline Lab only)
            </p>
          </div>
          <Toggle checked={visualInputLab} onChange={setVisualInputLab} />
        </div>

        {/* 3. Clip export format */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Clip export format
          </label>
          <RadioCards options={clipFormatOptions} value={clipFormat} onChange={setClipFormat} />
        </div>

        {/* 4. Max replay storage */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Max replay storage
          </label>
          <RadioCards options={storageOptions} value={replayStorage} onChange={setReplayStorage} />
        </div>

        {/* 5. Clear all replay data */}
        <div>
          {!showClearConfirm ? (
            <button
              onClick={() => setShowClearConfirm(true)}
              className="rounded-lg border border-red-500/50 bg-transparent px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10"
            >
              Clear all replay data
            </button>
          ) : (
            <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4">
              <p className="text-sm text-red-300 mb-3">
                Are you sure? This deletes all stored replays.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={handleClearData}
                  className="rounded-lg bg-red-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-red-500"
                >
                  Confirm
                </button>
                <button
                  onClick={() => setShowClearConfirm(false)}
                  className="rounded-lg border border-dark-600 bg-dark-800 px-4 py-1.5 text-sm font-medium text-dark-300 transition-colors hover:bg-dark-700"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Clear-data toast */}
      {clearStatus && <p className="mt-3 text-xs text-forge-400">{clearStatus}</p>}

      {/* Anti-cheat note */}
      <p className="mt-6 text-[10px] text-amber-400/80">
        Screen capture features are automatically disabled in Ranked and Tournament modes to comply
        with anti-cheat requirements.
      </p>
    </div>
  );
}
