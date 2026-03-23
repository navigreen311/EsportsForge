'use client';

import { clsx } from 'clsx';
import { Skull } from 'lucide-react';
import { Badge } from '@/components/shared/Badge';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
import { ExecutionGateBadge, PLAY_EXECUTION_STATUS } from '@/components/gameplan/ExecutionGateBadge';
import { ImpactScore } from '@/components/gameplan/ImpactScore';
import { MasteryDot } from '@/components/gameplan/MasteryDot';
import MetaVersionExpiry from '@/components/gameplan/MetaVersionExpiry';
import type { Play } from '@/types/gameplan';

const conceptColors: Record<string, { variant: 'success' | 'warning' | 'danger' | 'info' | 'tier' | 'neutral' }> = {
  'man-beater': { variant: 'info' },
  'zone-beater': { variant: 'success' },
  screen: { variant: 'warning' },
  rpo: { variant: 'tier' },
  'play-action': { variant: 'tier' },
  'quick-pass': { variant: 'info' },
  'deep-shot': { variant: 'danger' },
  run: { variant: 'warning' },
  draw: { variant: 'neutral' },
  misdirection: { variant: 'neutral' },
};

interface GameplanListProps {
  plays: Play[];
  selectedPlayId: string | null;
  onSelectPlay: (play: Play) => void;
}

export default function GameplanList({ plays, selectedPlayId, onSelectPlay }: GameplanListProps) {
  return (
    <div className="space-y-2 overflow-y-auto max-h-[calc(100vh-360px)] pr-1 scrollbar-thin scrollbar-track-dark-900 scrollbar-thumb-dark-700">
      {plays.length === 0 && (
        <div className="rounded-xl border border-dark-700/50 bg-dark-900/50 p-8 text-center">
          <p className="text-sm text-dark-500">No plays in this package</p>
        </div>
      )}

      {plays.map((play) => {
        const isSelected = play.id === selectedPlayId;
        const execStatus = PLAY_EXECUTION_STATUS[play.id];
        const isNotReady = execStatus && execStatus !== 'competition-ready';

        return (
          <button
            key={play.id}
            onClick={() => onSelectPlay(play)}
            className={clsx(
              'relative w-full text-left rounded-lg border p-3 transition-all duration-200',
              isSelected
                ? 'border-forge-500 bg-forge-950/30 shadow-lg shadow-forge-500/10'
                : 'border-dark-700/50 bg-dark-900/80 hover:border-dark-500 hover:bg-dark-800/80',
              play.isKillSheetPlay && !isSelected && 'border-l-2 border-l-forge-500',
              isNotReady && !isSelected && 'opacity-75'
            )}
          >
            {/* 10. ProgressionOS Mastery Dot */}
            <MasteryDot playId={play.id} />

            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5 min-w-0">
                {play.isKillSheetPlay && (
                  <Skull className="mt-0.5 h-4 w-4 flex-shrink-0 text-forge-400" />
                )}
                <div className="min-w-0">
                  <p className="font-semibold text-dark-50 truncate text-sm">{play.name}</p>
                  <p className="text-xs text-dark-400 truncate">{play.formation}</p>
                </div>
              </div>
            </div>

            {/* Concept Tags */}
            <div className="mt-2 flex flex-wrap gap-1">
              {play.conceptTags.map((tag) => (
                <Badge
                  key={tag}
                  variant={conceptColors[tag]?.variant ?? 'neutral'}
                  size="sm"
                >
                  {tag}
                </Badge>
              ))}
            </div>

            {/* Confidence Bar + 6. ImpactRank Score */}
            <div className="mt-2">
              <ConfidenceBar value={play.confidenceScore} size="sm" showValue label="" />
              <div className="mt-1 flex items-center gap-2">
                <ImpactScore playId={play.id} layout="inline" />
                {/* 9. MetaVersion Expiry Risk */}
                <MetaVersionExpiry playId={play.id} />
              </div>
            </div>

            {/* 1. PlayerTwin Execution Gate Badge */}
            {execStatus && (
              <div className="mt-2">
                <ExecutionGateBadge status={execStatus} />
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
