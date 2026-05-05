/**
 * AnimaForge Settings Panel — Agent #10.
 *
 * Per-user toggles for AnimaForge auto-generation + render quality. Mounted
 * inside the existing Settings > Game tab.
 *
 * Persistence: settings round-trip through `/api/v1/animaforge/settings` and
 * are also mirrored to localStorage so they survive even when the backend
 * cannot persist them (the User model has no JSON settings column yet).
 *
 * Offline handling: when AnimaForge is offline the panel still mounts but
 * surfaces a clear "Offline" banner instead of the toggles, per the contract
 * (graceful degradation, no error toasts).
 */

'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import {
  CheckCircle2,
  Film,
  Loader2,
  Sparkles,
  WifiOff,
  XCircle,
} from 'lucide-react';

import api from '@/lib/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Quality = 'standard' | 'high' | 'low';

interface AnimaForgeSettings {
  auto_arsenal: boolean;
  auto_drill: boolean;
  auto_share: boolean;
  quality: Quality;
}

interface ConnectionResult {
  available: boolean;
  latency_ms: number;
  message: string;
}

const STORAGE_KEY = 'animaforge.settings';
const DEFAULT_SETTINGS: AnimaForgeSettings = {
  auto_arsenal: true,
  auto_drill: true,
  auto_share: true,
  quality: 'standard',
};

// ---------------------------------------------------------------------------
// Subcomponents
// ---------------------------------------------------------------------------

function Toggle({
  checked,
  onChange,
  disabled = false,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
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

function QualitySelect({
  value,
  onChange,
}: {
  value: Quality;
  onChange: (q: Quality) => void;
}) {
  const options: Quality[] = ['standard', 'high', 'low'];
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => onChange(opt)}
          className={`rounded-lg border px-3 py-2 text-sm font-medium capitalize transition-colors ${
            value === opt
              ? 'border-forge-500 bg-forge-500/5 text-dark-100'
              : 'border-dark-700 bg-dark-800/50 text-dark-400 hover:border-dark-500'
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

function StatusBadge({
  status,
}: {
  status: 'unknown' | 'online' | 'offline';
}) {
  if (status === 'online') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        AnimaForge: Online
      </span>
    );
  }
  if (status === 'offline') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
        AnimaForge: Offline
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-dark-700/40 px-2.5 py-1 text-xs font-medium text-dark-400">
      <Loader2 className="h-3 w-3 animate-spin" />
      Checking…
    </span>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AnimaForgeSettingsPanel() {
  const [status, setStatus] = useState<'unknown' | 'online' | 'offline'>(
    'unknown'
  );
  const [settings, setSettings] = useState<AnimaForgeSettings>(DEFAULT_SETTINGS);
  const [saving, setSaving] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionResult | null>(null);

  // ----- Load: localStorage first, then backend overwrites if available
  useEffect(() => {
    try {
      const cached = window.localStorage.getItem(STORAGE_KEY);
      if (cached) {
        const parsed = JSON.parse(cached) as Partial<AnimaForgeSettings>;
        setSettings({ ...DEFAULT_SETTINGS, ...parsed });
      }
    } catch {
      // ignore
    }

    let cancelled = false;
    (async () => {
      try {
        const res = await api.get<AnimaForgeSettings>('/animaforge/settings');
        if (!cancelled) {
          setSettings({ ...DEFAULT_SETTINGS, ...res.data });
        }
      } catch {
        // backend not yet wired — stick with cached/defaults
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // ----- Status probe
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await api.get<{ available: boolean }>('/animaforge/status');
        if (!cancelled) {
          setStatus(res.data.available ? 'online' : 'offline');
        }
      } catch {
        if (!cancelled) {
          setStatus('offline');
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // ----- Persist on change (debounced via fire-and-forget POST + localStorage)
  const persist = useCallback(async (next: AnimaForgeSettings) => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // ignore quota errors
    }
    setSaving(true);
    try {
      await api.post<AnimaForgeSettings>('/animaforge/settings', next);
      setSavedFlash(true);
      setTimeout(() => setSavedFlash(false), 1500);
    } catch {
      // Backend unavailable — localStorage still holds the value.
    } finally {
      setSaving(false);
    }
  }, []);

  const update = useCallback(
    <K extends keyof AnimaForgeSettings>(key: K, value: AnimaForgeSettings[K]) => {
      setSettings((prev) => {
        const next = { ...prev, [key]: value };
        void persist(next);
        return next;
      });
    },
    [persist]
  );

  const handleTest = useCallback(async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post<ConnectionResult>(
        '/animaforge/test-connection'
      );
      setTestResult(res.data);
      setStatus(res.data.available ? 'online' : 'offline');
    } catch {
      setTestResult({
        available: false,
        latency_ms: 0,
        message: 'Could not reach the EsportsForge API.',
      });
      setStatus('offline');
    } finally {
      setTesting(false);
    }
  }, []);

  const offline = status === 'offline';

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Film className="h-5 w-5 text-forge-400" />
            <h3 className="text-lg font-semibold text-dark-100">AnimaForge</h3>
          </div>
          <p className="mt-1 ml-7 text-sm text-dark-500">
            Animated visual breakdowns for Arsenal, Drills, Gameplan and Share Your Win
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      {offline ? (
        <div className="mb-2 flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-sm">
          <WifiOff className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <div className="space-y-1">
            <p className="font-medium text-amber-300">AnimaForge is offline</p>
            <p className="text-xs text-amber-200/80">
              Animation generation is paused. Toggles will reactivate
              automatically once the service comes back online.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* 1. Auto-generate Arsenal */}
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-dark-200">
                Auto-generate Arsenal animations
              </p>
              <p className="mt-0.5 text-xs text-dark-500">
                Generate animations when weapons are saved
              </p>
            </div>
            <Toggle
              checked={settings.auto_arsenal}
              onChange={(v) => update('auto_arsenal', v)}
            />
          </div>

          {/* 2. Auto-generate drill demos */}
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-dark-200">
                Auto-generate drill demos
              </p>
              <p className="mt-0.5 text-xs text-dark-500">
                Generate before first rep of each drill
              </p>
            </div>
            <Toggle
              checked={settings.auto_drill}
              onChange={(v) => update('auto_drill', v)}
            />
          </div>

          {/* 3. Share Your Win cards */}
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-dark-200">
                Share Your Win cards
              </p>
              <p className="mt-0.5 text-xs text-dark-500">
                Generate animated cards on milestone achievements
              </p>
            </div>
            <Toggle
              checked={settings.auto_share}
              onChange={(v) => update('auto_share', v)}
            />
          </div>

          {/* 4. Quality */}
          <div>
            <label className="mb-3 block text-sm font-medium text-dark-300">
              Animation quality
            </label>
            <QualitySelect
              value={settings.quality}
              onChange={(q) => update('quality', q)}
            />
            <p className="mt-2 text-xs text-dark-500">
              Higher quality = longer render time
            </p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-dark-700/60 pt-5">
        <button
          type="button"
          onClick={handleTest}
          disabled={testing}
          className="inline-flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-500 hover:bg-dark-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {testing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4 text-forge-400" />
          )}
          {testing ? 'Testing…' : 'Test Connection'}
        </button>

        <Link
          href="/dashboard/settings/animations"
          className="inline-flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-500 hover:bg-dark-700"
        >
          <Film className="h-4 w-4 text-forge-400" />
          View My Animations
        </Link>

        <div className="ml-auto flex items-center gap-2 text-xs">
          {saving && (
            <span className="flex items-center gap-1 text-dark-400">
              <Loader2 className="h-3 w-3 animate-spin" />
              Saving…
            </span>
          )}
          {savedFlash && !saving && (
            <span className="flex items-center gap-1 text-emerald-400">
              <CheckCircle2 className="h-3 w-3" />
              Saved
            </span>
          )}
        </div>
      </div>

      {testResult && (
        <div
          className={`mt-3 flex items-center gap-2 rounded-lg border px-3 py-2 text-xs ${
            testResult.available
              ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300'
              : 'border-amber-500/30 bg-amber-500/5 text-amber-300'
          }`}
        >
          {testResult.available ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : (
            <XCircle className="h-3.5 w-3.5" />
          )}
          <span>{testResult.message}</span>
        </div>
      )}
    </div>
  );
}
