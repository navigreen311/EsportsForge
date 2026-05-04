'use client';

import { Play } from '@/types/gameplan';
import { Shield, Zap, Target, Clock, AlertTriangle } from 'lucide-react';
import PlayerTwinBadge, { PLAY_EXECUTION_PCT } from '@/components/gameplan/PlayerTwinBadge';
import MetaExpiryWarning from '@/components/gameplan/MetaExpiryWarning';

const tagIcons: Record<string, React.ReactNode> = {
  'red-zone': <Target className="w-3 h-3" />,
  'anti-blitz': <Shield className="w-3 h-3" />,
  '3rd-down': <Zap className="w-3 h-3" />,
  '2-minute': <Clock className="w-3 h-3" />,
};

const tagColors: Record<string, string> = {
  'red-zone': 'bg-red-900/40 text-red-400 border-red-800',
  'goal-line': 'bg-orange-900/40 text-orange-400 border-orange-800',
  '3rd-down': 'bg-yellow-900/40 text-yellow-400 border-yellow-800',
  '2-minute': 'bg-purple-900/40 text-purple-400 border-purple-800',
  'opening-drive': 'bg-blue-900/40 text-blue-400 border-blue-800',
  'anti-blitz': 'bg-cyan-900/40 text-cyan-400 border-cyan-800',
  'prevent': 'bg-dark-700 text-dark-300 border-dark-600',
  'hurry-up': 'bg-pink-900/40 text-pink-400 border-pink-800',
};

interface PlayCardProps {
  play: Play;
  index: number;
  isSelected: boolean;
  onSelect: (play: Play) => void;
}

export default function PlayCard({ play, index, isSelected, onSelect }: PlayCardProps) {
  const confidenceColor =
    play.confidenceScore >= 80
      ? 'text-forge-400'
      : play.confidenceScore >= 60
        ? 'text-yellow-400'
        : 'text-red-400';

  return (
    <button
      onClick={() => onSelect(play)}
      className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
        isSelected
          ? 'border-forge-500 bg-forge-950/30 shadow-lg shadow-forge-500/10'
          : play.isKillSheetPlay
            ? 'border-forge-800/50 bg-dark-900/80 hover:border-forge-600'
            : 'border-dark-700 bg-dark-900/50 hover:border-dark-500'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="flex-shrink-0 w-7 h-7 rounded-full bg-dark-800 border border-dark-600 flex items-center justify-center text-xs font-mono text-dark-300">
            {index + 1}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-dark-50 truncate">{play.name}</h3>
              {play.isKillSheetPlay && (
                <span className="flex-shrink-0 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-forge-500/20 text-forge-400 rounded border border-forge-500/30">
                  Kill
                </span>
              )}
            </div>
            <p className="text-sm text-dark-400 truncate">{play.formation}</p>
          </div>
        </div>
        <div className="flex-shrink-0 text-right">
          <div className={`text-lg font-bold font-mono ${confidenceColor}`}>
            {play.confidenceScore}%
          </div>
          <p className="text-[10px] text-dark-500 uppercase tracking-wider">Conf</p>
        </div>
      </div>

      {/* PlayerTwin + Meta badges */}
      <div className="flex flex-wrap items-center gap-1.5 mt-2">
        {(play.executionRate !== undefined || PLAY_EXECUTION_PCT[play.id] !== undefined) && (
          <PlayerTwinBadge executionPct={play.executionRate ?? PLAY_EXECUTION_PCT[play.id]} />
        )}
        {play.masteryLevel && (
          <span className="px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-dark-800 text-dark-300 border border-dark-600 rounded">
            {play.masteryLevel}
          </span>
        )}
        {play.isTrendingCountered && (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-amber-900/40 text-amber-400 border border-amber-700/40 rounded">
            <AlertTriangle className="w-2.5 h-2.5" />
            Trending Countered
          </span>
        )}
        {play.metaStatus && (
          <span className="px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider bg-dark-800/60 text-dark-400 border border-dark-700 rounded">
            Meta: {play.metaStatus}
          </span>
        )}
        <MetaExpiryWarning playId={play.id} />
      </div>

      {(play.tags && play.tags.length > 0) || play.situationTags.length > 0 ? (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {(play.tags ?? play.situationTags).map((tag) => (
            <span
              key={tag}
              className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded border ${
                tagColors[tag] || 'bg-dark-800 text-dark-300 border-dark-600'
              }`}
            >
              {tagIcons[tag]}
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {isSelected && play.description && (
        <p className="mt-3 text-sm text-dark-300 border-t border-dark-700 pt-3">
          {play.description}
        </p>
      )}
    </button>
  );
}
