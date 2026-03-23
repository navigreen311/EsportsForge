/**
 * TiltGuard pre-session mood check-in modal.
 * Shows once per day on first dashboard load.
 */

'use client';

import { useState, useEffect } from 'react';
import { Shield, Zap, Smile, Moon, Frown, Flame } from 'lucide-react';
import { clsx } from 'clsx';
import { Modal } from '@/components/shared/Modal';
import type { TiltGuardMood } from '@/types/dashboard';

const MOOD_OPTIONS: {
  value: TiltGuardMood;
  label: string;
  icon: typeof Zap;
  color: string;
  bg: string;
}[] = [
  { value: 'locked-in', label: 'Locked In', icon: Zap, color: 'text-forge-400', bg: 'bg-forge-500/20 border-forge-500/30' },
  { value: 'good', label: 'Good', icon: Smile, color: 'text-sky-400', bg: 'bg-sky-500/20 border-sky-500/30' },
  { value: 'tired', label: 'Tired', icon: Moon, color: 'text-amber-400', bg: 'bg-amber-500/20 border-amber-500/30' },
  { value: 'frustrated', label: 'Frustrated', icon: Frown, color: 'text-orange-400', bg: 'bg-orange-500/20 border-orange-500/30' },
  { value: 'tilted', label: 'Tilted', icon: Flame, color: 'text-red-400', bg: 'bg-red-500/20 border-red-500/30' },
];

const STORAGE_KEY = 'tiltguard-checkin-date';

interface TiltGuardCheckinProps {
  onMoodSelect: (mood: TiltGuardMood) => void;
}

export default function TiltGuardCheckin({ onMoodSelect }: TiltGuardCheckinProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const today = new Date().toDateString();
    const lastCheckin = localStorage.getItem(STORAGE_KEY);
    if (lastCheckin !== today) {
      setOpen(true);
    }
  }, []);

  const handleSelect = (mood: TiltGuardMood) => {
    localStorage.setItem(STORAGE_KEY, new Date().toDateString());
    onMoodSelect(mood);
    setOpen(false);
  };

  return (
    <Modal open={open} onClose={() => setOpen(false)} title="Pre-Session Check-In" size="sm">
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-dark-300">
          <Shield className="h-4 w-4 text-forge-400" />
          <span>How are you feeling before this session?</span>
        </div>

        <div className="grid grid-cols-1 gap-2">
          {MOOD_OPTIONS.map((opt) => {
            const Icon = opt.icon;
            return (
              <button
                key={opt.value}
                onClick={() => handleSelect(opt.value)}
                className={clsx(
                  'flex items-center gap-3 rounded-lg border px-4 py-3 text-left transition-all hover:scale-[1.02]',
                  opt.bg
                )}
              >
                <Icon className={clsx('h-5 w-5', opt.color)} />
                <span className={clsx('text-sm font-medium', opt.color)}>
                  {opt.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </Modal>
  );
}

/** Compact mood badge for top bar */
export function MoodBadge({ mood }: { mood: TiltGuardMood | null }) {
  if (!mood) return null;

  const opt = MOOD_OPTIONS.find((o) => o.value === mood);
  if (!opt) return null;

  const Icon = opt.icon;
  const isWarning = mood === 'tilted' || mood === 'frustrated';

  return (
    <div className="flex items-center gap-2">
      <span
        className={clsx(
          'inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-medium',
          opt.bg
        )}
      >
        <Icon className={clsx('h-3.5 w-3.5', opt.color)} />
        {opt.label}
      </span>
      {isWarning && (
        <span className="text-[10px] text-amber-400">
          Consider a 5-min reset before queuing
        </span>
      )}
    </div>
  );
}
