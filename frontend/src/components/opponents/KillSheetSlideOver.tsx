'use client';

import { X, Crosshair } from 'lucide-react';
import { Opponent } from '@/types/opponent';

interface KillSheetSlideOverProps {
  open: boolean;
  onClose: () => void;
  opponent: Opponent | null;
}

export default function KillSheetSlideOver({
  open,
  onClose,
  opponent,
}: KillSheetSlideOverProps) {
  if (!open || !opponent) return null;

  const plays = opponent.killSheet.slice(0, 5);

  function confidenceColor(score: number): string {
    if (score >= 85) return 'text-forge-400';
    if (score >= 70) return 'text-amber-400';
    return 'text-dark-300';
  }

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-dark-950/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-full max-w-md border-l border-dark-700 bg-dark-900 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-dark-700 px-6 py-4">
          <div>
            <p className="text-sm text-dark-400">{opponent.gamertag}</p>
            <div className="flex items-center gap-2">
              <Crosshair className="h-5 w-5 text-forge-400" />
              <h2 className="text-lg font-semibold text-white">Kill Sheet</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-dark-400 transition-colors hover:bg-dark-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Play List */}
        <div className="flex flex-col gap-4 p-6">
          {plays.length === 0 && (
            <p className="text-sm text-dark-400">No kill sheet plays scouted yet.</p>
          )}

          {plays.map((play, index) => (
            <div
              key={play.id}
              className="rounded-lg border border-dark-700 bg-dark-800 p-4"
            >
              {/* Rank & Play Name */}
              <div className="mb-2 flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-dark-700 text-sm font-bold text-dark-300">
                    {index + 1}
                  </span>
                  <div>
                    <p className="font-bold text-white">{play.playName}</p>
                    <p className="text-xs text-dark-400">{play.formation}</p>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="mb-2 flex items-center gap-4 text-sm">
                <span className={confidenceColor(play.confidenceScore)}>
                  {play.confidenceScore}% confidence
                </span>
                <span className="text-dark-400">
                  {play.successRate}% success rate
                </span>
              </div>

              {/* Description */}
              <p className="text-sm leading-relaxed text-dark-300">
                {play.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
