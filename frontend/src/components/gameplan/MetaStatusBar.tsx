'use client';

import { clsx } from 'clsx';
import { Shield, Clock } from 'lucide-react';
import type { MetaStatus, MetaRating } from '@/types/gameplan';

interface MetaStatusBarProps {
  metaStatus: MetaStatus;
}

const ratingStyles: Record<MetaRating, { bg: string; text: string; border: string; dot: string }> = {
  Exploit: {
    bg: 'bg-purple-500/20',
    text: 'text-purple-400',
    border: 'border-purple-500/30',
    dot: 'bg-purple-400',
  },
  Strong: {
    bg: 'bg-forge-500/20',
    text: 'text-forge-400',
    border: 'border-forge-500/30',
    dot: 'bg-forge-400',
  },
  Neutral: {
    bg: 'bg-dark-700/50',
    text: 'text-dark-300',
    border: 'border-dark-600/50',
    dot: 'bg-dark-400',
  },
  Countered: {
    bg: 'bg-red-500/20',
    text: 'text-red-400',
    border: 'border-red-500/30',
    dot: 'bg-red-400',
  },
};

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffHours < 1) return 'Just now';
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return 'Yesterday';
  return `${diffDays}d ago`;
}

export default function MetaStatusBar({ metaStatus }: MetaStatusBarProps) {
  const style = ratingStyles[metaStatus.rating];

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-dark-700/50 bg-dark-900/60 px-4 py-3">
      {/* Meta Rating Badge */}
      <div className="flex items-center gap-3">
        <Shield className={clsx('h-4 w-4', style.text)} />
        <span className="text-sm font-medium text-dark-400">Meta Status</span>
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-bold',
            style.bg,
            style.text,
            style.border
          )}
        >
          <span className={clsx('h-1.5 w-1.5 rounded-full', style.dot)} />
          {metaStatus.rating}
        </span>
      </div>

      {/* Patch + Last Updated */}
      <div className="flex items-center gap-4 text-xs text-dark-400">
        <span className="rounded bg-dark-800 px-2 py-1 font-mono text-dark-300">
          {metaStatus.patchVersion}
        </span>
        <span className="flex items-center gap-1.5">
          <Clock className="h-3 w-3" />
          Last updated {formatTimestamp(metaStatus.lastUpdated)}
        </span>
      </div>
    </div>
  );
}
