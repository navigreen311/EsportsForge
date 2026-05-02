/**
 * Settings card for Arsenal voice coaching — toggles for read,
 * guided practice, post-deploy debrief, pre-exec brief, and a tone
 * selector. Backed by localStorage via useArsenalVoiceSettings.
 */

'use client';

import { Volume2 } from 'lucide-react';
import { clsx } from 'clsx';
import {
  useArsenalVoice,
  useArsenalVoiceSettings,
  type CoachTone,
} from '@/lib/arsenal/voiceSettings';

const TONE_OPTIONS: { value: CoachTone; label: string; hint: string }[] = [
  { value: 'intense', label: 'Intense', hint: 'urgent and direct' },
  { value: 'standard', label: 'Standard', hint: 'balanced' },
  { value: 'calm', label: 'Calm', hint: 'measured and quiet' },
];

function Toggle({
  on,
  onChange,
  label,
  hint,
}: {
  on: boolean;
  onChange: (v: boolean) => void;
  label: string;
  hint?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <div className="min-w-0">
        <p className="text-sm font-medium text-dark-100">{label}</p>
        {hint && <p className="text-[11px] text-dark-400">{hint}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={on}
        onClick={() => onChange(!on)}
        className={clsx(
          'relative h-5 w-9 flex-shrink-0 rounded-full transition-colors',
          on ? 'bg-forge-500' : 'bg-dark-700'
        )}
      >
        <span
          className={clsx(
            'absolute top-0.5 h-4 w-4 rounded-full bg-dark-50 transition-transform',
            on ? 'translate-x-4' : 'translate-x-0.5'
          )}
        />
      </button>
    </div>
  );
}

export function ArsenalVoiceSettings() {
  const settings = useArsenalVoice();
  const update = useArsenalVoiceSettings((s) => s.update);

  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/60 p-5">
      <div className="mb-3 flex items-center gap-2">
        <Volume2 className="h-4 w-4 text-forge-400" />
        <h3 className="text-sm font-bold text-dark-100">
          Arsenal Voice Coaching
        </h3>
      </div>
      <p className="mb-4 text-[11px] text-dark-400">
        Hands-free coaching for trick plays and unstoppable concepts —
        the coach reads instructions aloud so you can keep your hands on
        the controller.
      </p>

      <div className="divide-y divide-dark-800">
        <Toggle
          on={settings.enabled}
          onChange={(v) => update({ enabled: v })}
          label="Coach voice during Arsenal"
          hint="Master toggle — disables everything below when off."
        />
        <Toggle
          on={settings.guidedPractice}
          onChange={(v) => update({ guidedPractice: v })}
          label="Step-by-step guidance"
          hint="Walks you through each step and waits for confirmation."
        />
        <Toggle
          on={settings.postDebrief}
          onChange={(v) => update({ postDebrief: v })}
          label="Post-deployment debrief"
          hint="Coach feedback after each weapon deployment."
        />
        <Toggle
          on={settings.preExecBrief}
          onChange={(v) => update({ preExecBrief: v })}
          label="Pre-execution brief"
          hint="30-second spoken brief before deploying a weapon live."
        />
      </div>

      <div className="mt-4">
        <p className="mb-1 text-[11px] font-bold uppercase tracking-wider text-dark-500">
          Coaching tone
        </p>
        <div className="flex flex-wrap gap-2">
          {TONE_OPTIONS.map((o) => (
            <button
              key={o.value}
              type="button"
              onClick={() => update({ tone: o.value })}
              className={clsx(
                'rounded-md border px-3 py-1.5 text-xs font-semibold transition-colors',
                settings.tone === o.value
                  ? 'border-forge-500 bg-forge-500/15 text-forge-300'
                  : 'border-dark-700 bg-dark-800 text-dark-300 hover:border-dark-600'
              )}
            >
              {o.label}
              <span className="ml-1 text-[10px] font-normal text-dark-500">
                {o.hint}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
