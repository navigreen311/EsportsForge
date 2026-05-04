/**
 * War Room defensive-scheme panel.
 *
 * Calls /arsenal/defensive-gameplan with the active session opponent,
 * surfaces the primary scheme + top 3 opponent counters + first
 * adjustment trigger. Includes a "Read Briefing" button that pipes the
 * scheme into VoiceForge so the player can hear it pre-game.
 */

'use client';

import { useState } from 'react';
import { Shield, Loader2, Volume2, Sparkles } from 'lucide-react';
import api from '@/lib/api';
import { useSessionStore } from '@/lib/sessionStore';
import { useActiveArsenalTitle } from '@/hooks/useArsenal';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import type { DefensivePlan } from '@/components/gameplan/DefensiveGameplanView';
import Link from 'next/link';

export default function DefensiveSchemePanel() {
  const session = useSessionStore((s) => s.session);
  const titleId = useActiveArsenalTitle();
  const opponentName = session?.opponent ?? 'Next Opponent';
  const [plan, setPlan] = useState<DefensivePlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<DefensivePlan>(
        '/arsenal/defensive-gameplan',
        { title_id: titleId, opponent_id: session?.opponent ?? null }
      );
      setPlan(data);
    } catch (e: unknown) {
      type AxiosErr = { response?: { status?: number; data?: { detail?: string } } };
      const ax = e as AxiosErr;
      if (ax?.response?.status === 503) {
        setError(
          ax.response?.data?.detail ??
            'DefenseAI is offline — set ANTHROPIC_API_KEY to use this panel.'
        );
      } else {
        setError(e instanceof Error ? e.message : 'Failed to fetch defense plan.');
      }
    } finally {
      setLoading(false);
    }
  };

  const readBriefing = () => {
    if (!plan) return;
    const counters = plan.opponent_counters
      .slice(0, 3)
      .map((c) => `Counter to ${c.opponent_tendency}: ${c.your_adjustment}.`)
      .join(' ');
    VoiceForgeService.speak(
      `Defensively versus ${opponentName}: run ${plan.primary_scheme.name} as your base. ` +
        `${plan.primary_scheme.description} ${counters}`,
      { interruptCurrent: true }
    );
  };

  return (
    <div className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-5">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-sky-300" />
          <h3 className="text-sm font-bold text-sky-200">
            Defensive Scheme vs {opponentName}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {plan && (
            <button
              type="button"
              onClick={readBriefing}
              className="inline-flex items-center gap-1 rounded-md border border-sky-500/40 bg-sky-500/10 px-2 py-1 text-[11px] font-bold text-sky-200 hover:bg-sky-500/20"
            >
              <Volume2 className="h-3 w-3" />
              Read
            </button>
          )}
          <button
            type="button"
            onClick={generate}
            disabled={loading}
            className="inline-flex items-center gap-1 rounded-md bg-sky-500 px-3 py-1 text-[11px] font-bold text-dark-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
            {plan ? 'Regenerate' : 'Generate'}
          </button>
        </div>
      </div>

      {error && (
        <p className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      {!plan && !loading && !error && (
        <p className="text-xs text-dark-400">
          Click Generate to build a defensive scheme that counters this
          opponent's offensive tendencies.
        </p>
      )}

      {plan && (
        <div className="space-y-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-sky-300">
              Primary Scheme
            </p>
            <p className="text-sm font-bold text-dark-50">
              {plan.primary_scheme.name}
            </p>
            <p className="text-xs text-dark-300">
              {plan.primary_scheme.description}
            </p>
          </div>

          {plan.opponent_counters.length > 0 && (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-sky-300">
                Top Adjustments
              </p>
              <ul className="mt-1 space-y-1.5">
                {plan.opponent_counters.slice(0, 3).map((c, i) => (
                  <li
                    key={i}
                    className="rounded-md bg-dark-800/60 px-3 py-1.5 text-xs text-dark-200"
                  >
                    <span className="text-sky-300">vs. {c.opponent_tendency}</span>{' '}
                    — {c.your_adjustment}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {plan.adjustment_triggers.length > 0 && (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-300">
                Blitz Trigger
              </p>
              <p className="text-xs text-dark-200">
                <span className="text-amber-300">If {plan.adjustment_triggers[0].trigger}</span>{' '}
                — {plan.adjustment_triggers[0].adjustment}
              </p>
            </div>
          )}

          <Link
            href="/gameplan?tab=script"
            className="inline-block text-[11px] font-medium text-sky-300 hover:text-sky-200"
          >
            View Full Defensive Plan →
          </Link>
        </div>
      )}
    </div>
  );
}
