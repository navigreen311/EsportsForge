/**
 * LoopAI Last Game Debrief card — shows what happened, was advice followed, outcome.
 */

'use client';

import { RefreshCw, Check, X, Trophy, Skull } from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import type { LoopAIDebrief } from '@/types/dashboard';

interface LoopAIDebriefCardProps {
  debrief: LoopAIDebrief | null;
}

export default function LoopAIDebriefCard({ debrief }: LoopAIDebriefCardProps) {
  if (!debrief) {
    return (
      <Card padding="md">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-dark-800">
            <RefreshCw className="h-5 w-5 text-dark-500" />
          </div>
          <div>
            <p className="text-sm font-bold text-dark-300">Last Game Debrief</p>
            <p className="text-xs text-dark-500">
              Log your next game to activate LoopAI feedback
            </p>
          </div>
        </div>
      </Card>
    );
  }

  const outcomeIcon = debrief.outcome === 'won' ? Trophy : Skull;
  const OutcomeIcon = outcomeIcon;
  const outcomeColor = debrief.outcome === 'won' ? 'text-forge-400' : 'text-red-400';
  const outcomeBg = debrief.outcome === 'won' ? 'bg-forge-500/10' : 'bg-red-500/10';

  return (
    <Card padding="md">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 text-purple-400" />
            <span className="text-sm font-bold text-dark-100">Last Game Debrief</span>
          </div>
          <span className="text-[10px] text-dark-500">{debrief.gameTimestamp}</span>
        </div>

        <p className="text-sm leading-relaxed text-dark-200">
          {debrief.recommendation}
        </p>

        <div className="flex flex-wrap items-center gap-2">
          {/* Followed indicator */}
          {debrief.wasFollowed !== null && (
            <Badge
              variant={debrief.wasFollowed ? 'success' : 'danger'}
              size="sm"
            >
              {debrief.wasFollowed ? (
                <Check className="h-3 w-3" />
              ) : (
                <X className="h-3 w-3" />
              )}
              {debrief.wasFollowed ? 'Followed' : 'Ignored'}
            </Badge>
          )}

          {/* Outcome */}
          <span
            className={clsx(
              'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
              outcomeBg, outcomeColor
            )}
          >
            <OutcomeIcon className="h-3 w-3" />
            {debrief.outcome === 'won' ? 'Won' : 'Lost'}
          </span>
        </div>

        {/* LoopAI update */}
        <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 px-3 py-2">
          <p className="text-[11px] text-purple-300">
            <span className="font-bold">LoopAI updated:</span> {debrief.loopUpdate}
          </p>
        </div>
      </div>
    </Card>
  );
}
