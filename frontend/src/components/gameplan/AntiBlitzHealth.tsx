/**
 * Anti-Blitz Package Health Indicator — badge and banner showing package completeness.
 */

"use client";

import { clsx } from 'clsx';
import { Check, AlertTriangle } from 'lucide-react';
import type { Play } from '@/types/gameplan';

interface AntiBlitzHealthProps {
  plays: Play[];
}

function evaluateHealth(plays: Play[]) {
  const hasScreen = plays.some((p) => p.conceptTags.includes('screen'));
  const hasQuickPass = plays.some((p) => p.conceptTags.includes('quick-pass'));
  const hasRpo = plays.some((p) => p.conceptTags.includes('rpo'));

  const missing: string[] = [];
  if (!hasScreen) missing.push('screen');
  if (!hasQuickPass) missing.push('quick-pass');
  if (!hasRpo) missing.push('rpo');

  return { complete: missing.length === 0, missing };
}

export function AntiBlitzHealthBadge({ plays }: AntiBlitzHealthProps) {
  const { complete } = evaluateHealth(plays);

  if (complete) {
    return <Check className="h-3 w-3 text-forge-400" />;
  }

  return <AlertTriangle className="h-3 w-3 text-amber-400" />;
}

const missingLabels: Record<string, string> = {
  screen: 'a RB screen or TE hot route',
  'quick-pass': 'a quick-pass concept',
  rpo: 'an RPO play',
};

export function AntiBlitzHealthBanner({ plays }: AntiBlitzHealthProps) {
  const { complete, missing } = evaluateHealth(plays);

  if (complete) return null;

  const suggestions = missing.map((m) => missingLabels[m] ?? m);
  const suggestionText =
    suggestions.length === 1
      ? suggestions[0]
      : suggestions.slice(0, -1).join(', ') + ' and ' + suggestions[suggestions.length - 1];

  return (
    <div
      className={clsx(
        'rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3 mb-3',
        'flex items-start gap-2 text-sm text-amber-200/90'
      )}
    >
      <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
      <p>
        <span className="font-medium text-amber-300">Package incomplete:</span>{' '}
        Add {suggestionText} to protect against all-out blitzes.
      </p>
    </div>
  );
}
