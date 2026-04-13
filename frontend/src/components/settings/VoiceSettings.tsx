'use client';

import { useState, useEffect, useCallback } from 'react';
import { Mic, Wifi, WifiOff, AlertTriangle, Loader2 } from 'lucide-react';
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
  const [isChecking, setIsChecking] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [showDocs, setShowDocs] = useState(false);

  useEffect(() => {
    setAvailable(VoiceForgeService.isAvailable());
  }, []);

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  }, []);

  const handleReconnect = useCallback(() => {
    setIsChecking(true);
    // Simulate async check
    setTimeout(() => {
      const result = VoiceForgeService.isAvailable();
      setAvailable(result);
      setIsChecking(false);
      showToast(result ? 'VoiceForge connected successfully' : 'VoiceForge is still offline');
    }, 1000);
  }, [showToast]);

  const handleTestConnection = useCallback(() => {
    setIsChecking(true);
    setTimeout(() => {
      const result = VoiceForgeService.isAvailable();
      setAvailable(result);
      setIsChecking(false);
      showToast(
        result
          ? 'Connection test passed — VoiceForge is reachable'
          : 'Connection test failed — VoiceForge is not reachable'
      );
    }, 1000);
  }, [showToast]);

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
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs font-medium">
            {available ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-forge-400" />
                <span className="text-forge-400">VoiceForge: Connected</span>
                <span className="text-forge-400">●</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-dark-500" />
                <span className="text-dark-500">VoiceForge: Offline</span>
                <span className="text-dark-500">○</span>
              </>
            )}
          </span>
          {!available && (
            <button
              onClick={handleReconnect}
              disabled={isChecking}
              className="flex items-center gap-1.5 rounded-lg border border-forge-400 px-3 py-1 text-xs font-medium text-forge-400 hover:bg-forge-400/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isChecking ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : null}
              Reconnect
            </button>
          )}
        </div>
      </div>

      {/* Offline Troubleshooting Box */}
      {!available && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-900/20 p-4 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <p className="text-sm font-semibold text-amber-400">VoiceForge is offline</p>
          </div>
          <p className="text-xs text-dark-400 mb-3">
            Voice coaching and briefings are unavailable.
          </p>

          <div className="mb-3">
            <p className="text-xs font-medium text-dark-300 mb-1.5">Troubleshooting:</p>
            <ol className="list-decimal list-inside space-y-1 text-xs text-dark-400">
              <li>Ensure VoiceForge is running (port 3001)</li>
              <li>Check VOICEFORGE_API_URL in your .env</li>
              <li>Verify no firewall is blocking the connection</li>
            </ol>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleTestConnection}
              disabled={isChecking}
              className="flex items-center gap-1.5 rounded-lg border border-dark-700 bg-dark-800 px-4 py-2 text-xs font-medium text-dark-300 hover:bg-dark-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isChecking && <Loader2 className="w-3 h-3 animate-spin" />}
              Test Connection
            </button>
            <button
              onClick={() => setShowDocs((prev) => !prev)}
              className="rounded-lg border border-dark-700 bg-dark-800 px-4 py-2 text-xs font-medium text-dark-300 hover:bg-dark-700 transition-colors"
            >
              View Setup Docs
            </button>
          </div>

          {showDocs && (
            <div className="mt-3 rounded-lg border border-dark-700 bg-dark-800 p-3">
              <p className="text-xs text-dark-300">
                Setup documentation is available at:{' '}
                <a
                  href="https://docs.esportsforge.gg/voiceforge/setup"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-forge-400 underline hover:text-forge-300"
                >
                  https://docs.esportsforge.gg/voiceforge/setup
                </a>
              </p>
            </div>
          )}
        </div>
      )}

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

      {/* Toast notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 rounded-lg border border-forge-400/30 bg-dark-800 px-5 py-3 shadow-lg">
          <p className="text-sm text-forge-400">{toastMessage}</p>
        </div>
      )}
    </div>
  );
}
