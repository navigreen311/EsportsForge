/**
 * MetaExpiryWarning — Warning badge on at-risk plays showing
 * "Meta risk: win rate declining" when a play's effectiveness is dropping.
 */

'use client';

import { AlertTriangle } from 'lucide-react';

interface MetaExpiryWarningProps {
  playId: string;
}

/** Mock data: which plays have declining win rates */
export const PLAYS_AT_META_RISK: Record<string, { message: string; decline: number } | null> = {
  'play-1': null,
  'play-2': null,
  'play-3': null,
  'play-4': { message: 'Meta risk: win rate declining', decline: 12 },
  'play-5': null,
  'play-6': { message: 'Meta risk: win rate declining', decline: 18 },
  'play-7': null,
  'play-8': null,
  'play-9': { message: 'Meta risk: win rate declining', decline: 8 },
  'play-10': null,
};

export default function MetaExpiryWarning({ playId }: MetaExpiryWarningProps) {
  const risk = PLAYS_AT_META_RISK[playId];
  if (!risk) return null;

  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium text-amber-400">
      <AlertTriangle className="h-3 w-3" />
      {risk.message} (-{risk.decline}%)
    </span>
  );
}
