/**
 * TiltGuard pre-session mood check-in modal.
 * Shows once per day on first dashboard load; can be re-opened from the
 * mood badge dropdown to update mid-session.
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Shield, Zap, Smile, Moon, Frown, Flame, ChevronDown } from 'lucide-react';
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

const DATE_KEY = 'tiltguard-checkin-date';
const MOOD_KEY = 'tiltguard-checkin-mood';

interface TiltGuardCheckinProps {
  onMoodSelect: (mood: TiltGuardMood) => void;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export default function TiltGuardCheckin({
  onMoodSelect,
  open: controlledOpen,
  onOpenChange,
}: TiltGuardCheckinProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : internalOpen;

  const setOpen = (next: boolean) => {
    if (!isControlled) setInternalOpen(next);
    onOpenChange?.(next);
  };

  useEffect(() => {
    if (isControlled) return;
    const today = new Date().toDateString();
    const lastCheckin = localStorage.getItem(DATE_KEY);
    if (lastCheckin !== today) {
      setInternalOpen(true);
    }
  }, [isControlled]);

  const handleSelect = (mood: TiltGuardMood) => {
    localStorage.setItem(DATE_KEY, new Date().toDateString());
    localStorage.setItem(MOOD_KEY, mood);
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

/** Read the persisted mood (set during today's check-in). */
export function loadStoredMood(): TiltGuardMood | null {
  if (typeof window === 'undefined') return null;
  const today = new Date().toDateString();
  if (localStorage.getItem(DATE_KEY) !== today) return null;
  return (localStorage.getItem(MOOD_KEY) as TiltGuardMood | null) ?? null;
}

/** Compact mood badge — clickable to update mood mid-session. */
export function MoodBadge({
  mood,
  onUpdate,
}: {
  mood: TiltGuardMood | null;
  onUpdate?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  if (!mood) return null;

  const opt = MOOD_OPTIONS.find((o) => o.value === mood);
  if (!opt) return null;

  const Icon = opt.icon;
  const isWarning = mood === 'tilted' || mood === 'frustrated';

  return (
    <div className="relative flex items-center gap-2" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={clsx(
          'inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-medium transition-all hover:brightness-110',
          opt.bg
        )}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <Icon className={clsx('h-3.5 w-3.5', opt.color)} />
        <span className={opt.color}>{opt.label}</span>
        <ChevronDown className={clsx('h-3 w-3', opt.color)} />
      </button>

      {isWarning && (
        <span className="text-[10px] text-amber-400">
          Consider a 5-min reset before queuing
        </span>
      )}

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-20 mt-1.5 w-52 overflow-hidden rounded-lg border border-dark-700 bg-dark-900 shadow-xl"
        >
          <div className="border-b border-dark-700/60 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wider text-dark-500">
              Current mood
            </p>
            <p className={clsx('text-xs font-semibold', opt.color)}>{opt.label}</p>
          </div>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              onUpdate?.();
            }}
            className="block w-full px-3 py-2 text-left text-xs font-medium text-dark-200 transition-colors hover:bg-dark-800 hover:text-dark-50"
          >
            Update mood
          </button>
        </div>
      )}
    </div>
  );
}
