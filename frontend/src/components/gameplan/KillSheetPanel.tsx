'use client';

import { Play } from '@/types/gameplan';
import { Crosshair, TrendingUp } from 'lucide-react';

interface KillSheetPanelProps {
  plays: Play[];
  opponentName: string;
}

export default function KillSheetPanel({ plays, opponentName }: KillSheetPanelProps) {
  return (
    <div className="rounded-xl border border-forge-800/50 bg-gradient-to-b from-forge-950/40 to-dark-900/80 p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-forge-500/20 border border-forge-500/30 flex items-center justify-center">
          <Crosshair className="w-5 h-5 text-forge-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-forge-400">Kill Sheet</h2>
          <p className="text-sm text-dark-400">
            Top plays vs <span className="text-dark-200 font-medium">{opponentName}</span>
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {plays.map((play, i) => (
          <div
            key={play.id}
            className="flex items-center gap-3 p-3 rounded-lg bg-dark-900/60 border border-forge-900/30 hover:border-forge-700/50 transition-colors"
          >
            <span className="w-6 h-6 rounded-full bg-forge-500/20 flex items-center justify-center text-xs font-bold text-forge-400">
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-dark-100 truncate">{play.name}</p>
              <p className="text-xs text-dark-500">{play.formation}</p>
            </div>
            <div className="flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-forge-500" />
              <span className="text-sm font-mono font-bold text-forge-400">
                {play.confidenceScore}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {plays.length === 0 && (
        <div className="text-center py-8 text-dark-500">
          <Crosshair className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No kill sheet plays generated yet</p>
        </div>
      )}
    </div>
  );
}
