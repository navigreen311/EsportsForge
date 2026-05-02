/**
 * ArsenalAlert — surfaces an ArsenalAI trigger inside the competition card.
 * Speaks the alert via VoiceForge when the trigger first fires.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Zap, X, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';
import { useArsenalAI } from '@/hooks/useArsenalAI';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import { useSessionStore } from '@/lib/sessionStore';
import api from '@/lib/api';

const URGENCY_TONE: Record<'now' | 'soon' | 'watch', string> = {
  now: 'border-forge-500/60 bg-forge-500/15 text-forge-300',
  soon: 'border-amber-500/60 bg-amber-500/15 text-amber-300',
  watch: 'border-dark-700 bg-dark-800 text-dark-300',
};

const URGENCY_LABEL: Record<'now' | 'soon' | 'watch', string> = {
  now: 'NOW',
  soon: 'SOON',
  watch: 'WATCH FOR IT',
};

function speakAlert(titleId: string | undefined, reason: string, weaponName: string, timing: string, urgency: string) {
  if (!titleId) return;
  let text = `ArsenalAI: ${reason}. ${weaponName}.`;
  if (titleId.startsWith('madden') || titleId.startsWith('cfb')) {
    text = `ArsenalAI: ${reason}. ${weaponName}. Element of surprise: ${urgency}.`;
  } else if (titleId === 'nba-2k26') {
    text = `ArsenalAI: ${weaponName}. ${reason}. ${timing}`;
  } else if (titleId === 'warzone' || titleId === 'fortnite') {
    text = `ArsenalAI: ${weaponName}. ${reason}. Use it now.`;
  } else if (titleId === 'ufc-5' || titleId === 'undisputed') {
    text = `ArsenalAI: ${weaponName}. ${reason}. Now.`;
  }
  VoiceForgeService.speak(text, { interruptCurrent: true, priority: 'high' });
}

export function ArsenalAlert() {
  const { last, visible, dismiss } = useArsenalAI();
  const session = useSessionStore((s) => s.session);
  const router = useRouter();
  const lastSpokenRef = useRef<string | null>(null);
  const [showResultPrompt, setShowResultPrompt] = useState(false);
  const followupTimer = useRef<number | null>(null);

  useEffect(() => {
    if (!visible) return;
    if (!last.weapon || !last.urgency) return;
    if (lastSpokenRef.current === last.weapon_id) return;
    lastSpokenRef.current = last.weapon_id ?? null;
    speakAlert(
      session?.opponent ? last.weapon.title_id : last.weapon.title_id,
      last.reason ?? '',
      last.weapon.name,
      last.timing ?? '',
      last.urgency
    );
  }, [visible, last, session?.opponent]);

  if (!visible || !last.weapon) return null;

  const tone = URGENCY_TONE[last.urgency ?? 'watch'];

  const handleGotIt = async () => {
    if (!last.weapon_id || !last.weapon) return;
    try {
      await api.post('/arsenal/usage-log', {
        weapon_id: last.weapon_id,
        title_id: last.weapon.title_id,
        deployed: true,
        session_id: session?.startTime?.toString(),
      });
    } catch {
      /* non-fatal */
    }
    if (followupTimer.current) window.clearTimeout(followupTimer.current);
    followupTimer.current = window.setTimeout(() => setShowResultPrompt(true), 60_000);
  };

  const handleSkip = async () => {
    if (!last.weapon_id || !last.weapon) return;
    try {
      await api.post('/arsenal/usage-log', {
        weapon_id: last.weapon_id,
        title_id: last.weapon.title_id,
        deployed: false,
        session_id: session?.startTime?.toString(),
      });
    } catch {
      /* non-fatal */
    }
    dismiss();
  };

  const handleResult = async (outcome: 'yes' | 'no' | 'not-used') => {
    if (!last.weapon_id || !last.weapon) return;
    try {
      await api.post('/arsenal/usage-log', {
        weapon_id: last.weapon_id,
        title_id: last.weapon.title_id,
        deployed: outcome !== 'not-used',
        outcome,
        opponent_adjusted: outcome === 'no',
        session_id: session?.startTime?.toString(),
      });
    } catch {
      /* non-fatal */
    }
    setShowResultPrompt(false);
    dismiss();
  };

  return (
    <div className={clsx('mx-5 my-3 overflow-hidden rounded-lg border', tone)}>
      <div className="flex items-center justify-between border-b border-current/30 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider">
        <span className="inline-flex items-center gap-1.5">
          <Zap className="h-3 w-3" />
          Secret Weapon Moment
        </span>
        <span>Urgency: {URGENCY_LABEL[last.urgency ?? 'watch']}</span>
        <button
          type="button"
          onClick={dismiss}
          className="text-current opacity-70 hover:opacity-100"
          aria-label="Dismiss"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
      <div className="space-y-1.5 px-3 py-2.5">
        <p className="text-sm font-bold text-dark-50">{last.weapon.name}</p>
        {last.reason && <p className="text-xs text-dark-200">{last.reason}</p>}
        {last.timing && (
          <p className="text-[11px] text-dark-300">
            <span className="font-semibold">Timing: </span>
            {last.timing}
          </p>
        )}

        {!showResultPrompt ? (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <button
              type="button"
              onClick={() => router.push(`/arsenal?weapon=${last.weapon_id}`)}
              className="inline-flex items-center gap-1 rounded-md border border-current/30 bg-dark-900/40 px-2 py-1 text-[11px] font-medium hover:bg-dark-900/60"
            >
              View Setup
              <ChevronRight className="h-3 w-3" />
            </button>
            <button
              type="button"
              onClick={handleGotIt}
              className="rounded-md bg-forge-500 px-2 py-1 text-[11px] font-bold text-dark-950 hover:bg-forge-400"
            >
              Got It
            </button>
            <button
              type="button"
              onClick={handleSkip}
              className="rounded-md border border-current/30 px-2 py-1 text-[11px] font-medium hover:bg-dark-900/40"
            >
              Skip
            </button>
          </div>
        ) : (
          <div className="space-y-1.5 pt-1">
            <p className="text-[11px] font-semibold">Did {last.weapon.name} work?</p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => handleResult('yes')}
                className="rounded-md bg-forge-500 px-2 py-1 text-[11px] font-bold text-dark-950 hover:bg-forge-400"
              >
                ✓ Yes — worked!
              </button>
              <button
                type="button"
                onClick={() => handleResult('no')}
                className="rounded-md border border-red-500/40 bg-red-500/10 px-2 py-1 text-[11px] font-bold text-red-300 hover:bg-red-500/20"
              >
                ✗ No — they read it
              </button>
              <button
                type="button"
                onClick={() => handleResult('not-used')}
                className="rounded-md border border-current/30 px-2 py-1 text-[11px] font-medium hover:bg-dark-900/40"
              >
                Did not use
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
