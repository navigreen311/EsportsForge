/**
 * LoopAI Debrief — "Last Session Debrief" with bullet points showing:
 * what was recommended, what happened, outcome, what LoopAI learned.
 *
 * Fetches `/sessions/last-debrief` on mount. Renders an empty state when
 * the user has no logged sessions yet.
 */

'use client';

import { useEffect, useState } from 'react';
import { RefreshCw, Lightbulb, PlayCircle, Trophy, Brain } from 'lucide-react';
import api from '@/lib/api';
import { Card } from '@/components/shared/Card';
import type { LoopAIDebrief as LoopAIDebriefData } from '@/types/dashboard';

interface DebriefBullet {
  icon: React.ReactNode;
  label: string;
  text: string;
  color: string;
}

interface LastDebriefResponse {
  debrief: LoopAIDebriefData | null;
}

function buildBullets(debrief: LoopAIDebriefData): DebriefBullet[] {
  const bullets: DebriefBullet[] = [
    {
      icon: <Lightbulb className="h-3.5 w-3.5" />,
      label: 'Recommended',
      text: debrief.recommendation,
      color: 'text-purple-400',
    },
  ];

  if (debrief.wasFollowed !== null && debrief.wasFollowed !== undefined) {
    bullets.push({
      icon: <PlayCircle className="h-3.5 w-3.5" />,
      label: 'What happened',
      text: debrief.wasFollowed
        ? 'You followed the recommended approach in your last session.'
        : 'You went with a different approach than the recommendation.',
      color: 'text-sky-400',
    });
  }

  bullets.push({
    icon: <Trophy className="h-3.5 w-3.5" />,
    label: 'Outcome',
    text: debrief.outcome === 'won' ? 'Won the match.' : 'Lost the match.',
    color: debrief.outcome === 'won' ? 'text-forge-400' : 'text-red-400',
  });

  bullets.push({
    icon: <Brain className="h-3.5 w-3.5" />,
    label: 'LoopAI learned',
    text: debrief.loopUpdate,
    color: 'text-amber-400',
  });

  return bullets;
}

export default function LoopAIDebrief() {
  const [debrief, setDebrief] = useState<LoopAIDebriefData | null>(null);
  const [loading, setLoading] = useState(true);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .get<LastDebriefResponse>('/sessions/last-debrief')
      .then((res) => {
        if (cancelled) return;
        setDebrief(res.data.debrief ?? null);
        setErrored(false);
      })
      .catch(() => {
        if (cancelled) return;
        setErrored(true);
        setDebrief(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Card padding="md">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10">
            <RefreshCw
              className={`h-4 w-4 text-purple-400 ${loading ? 'animate-spin' : ''}`}
            />
          </div>
          <div>
            <span className="text-sm font-bold text-dark-100">
              Last Session Debrief
            </span>
            <p className="text-[10px] text-dark-500">LoopAI feedback cycle</p>
          </div>
        </div>

        {loading ? (
          <p className="text-xs text-dark-500">Loading your last session…</p>
        ) : !debrief ? (
          <p className="text-xs text-dark-400 leading-relaxed">
            {errored
              ? 'Could not load your last session debrief — try again later.'
              : 'Play a ranked game and log your result to see your debrief here'}
          </p>
        ) : (
          <div className="space-y-2.5">
            {buildBullets(debrief).map((bullet, idx) => (
              <div key={idx} className="flex items-start gap-2.5">
                <div className={`mt-0.5 ${bullet.color}`}>{bullet.icon}</div>
                <div className="min-w-0 flex-1">
                  <p
                    className={`text-[10px] font-semibold uppercase tracking-wider ${bullet.color}`}
                  >
                    {bullet.label}
                  </p>
                  <p className="text-xs text-dark-300 leading-relaxed">
                    {bullet.text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
