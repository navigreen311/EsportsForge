/**
 * ImpactScore — displays the ImpactRank score for a play.
 * Supports compact inline rendering (play list) and detailed layout (detail panel).
 */

"use client";

import { clsx } from 'clsx';

interface ImpactScoreProps {
  playId: string;
  layout: 'inline' | 'detail';
}

/** Mock mapping of play IDs to their impact scores (1-10). */
export const PLAY_IMPACT_SCORES: Record<string, number> = {
  'play-1': 8.4,
  'play-2': 7.1,
  'play-3': 8.9,
  'play-4': 6.2,
  'play-5': 7.5,
  'play-6': 5.8,
  'play-7': 6.9,
  'play-8': 8.1,
  'play-9': 4.3,
  'play-10': 5.5,
};

export function ImpactScore({ playId, layout }: ImpactScoreProps) {
  const score = PLAY_IMPACT_SCORES[playId] ?? 0;

  if (layout === 'inline') {
    return (
      <span className="text-[10px] text-amber-400 font-bold tabular-nums">
        Impact {score}
      </span>
    );
  }

  const barWidth = (score / 10) * 100;

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs text-dark-500">Win Impact</span>
      <span className="text-xl font-black tabular-nums text-amber-400">
        {score}/10
      </span>
      <div className="h-1.5 rounded-full bg-dark-800">
        <div
          className={clsx('h-full rounded-full bg-amber-500')}
          style={{ width: `${barWidth}%` }}
        />
      </div>
    </div>
  );
}
