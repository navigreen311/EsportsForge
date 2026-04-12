/**
 * ProofAI Evidence — Expandable per-play evidence showing
 * sample size, win rate, confidence, and data source.
 */

'use client';

import { useState } from 'react';
import { ChevronDown, ShieldCheck } from 'lucide-react';
import { clsx } from 'clsx';

interface ProofAIEvidenceProps {
  playId: string;
}

interface PlayEvidence {
  sampleSize: number;
  winRate: number;
  confidence: number;
  dataSource: string;
}

const PLAY_PROOF_DATA: Record<string, PlayEvidence> = {
  'play-1': { sampleSize: 14, winRate: 71, confidence: 87, dataSource: 'Last 3 weeks ranked matches' },
  'play-2': { sampleSize: 22, winRate: 64, confidence: 79, dataSource: 'Season career stats' },
  'play-3': { sampleSize: 9, winRate: 78, confidence: 72, dataSource: 'Last 2 weeks vs zone teams' },
  'play-4': { sampleSize: 6, winRate: 50, confidence: 58, dataSource: 'Limited sample — tournament only' },
  'play-5': { sampleSize: 18, winRate: 83, confidence: 91, dataSource: 'All-time vs Cover 2 opponents' },
  'play-6': { sampleSize: 4, winRate: 25, confidence: 41, dataSource: 'Recent 2 sessions only' },
  'play-7': { sampleSize: 11, winRate: 73, confidence: 76, dataSource: 'Last month ranked matches' },
  'play-8': { sampleSize: 19, winRate: 84, confidence: 89, dataSource: 'Spread formation dataset' },
  'play-9': { sampleSize: 7, winRate: 57, confidence: 63, dataSource: 'Anti-blitz situations only' },
  'play-10': { sampleSize: 3, winRate: 33, confidence: 35, dataSource: 'Insufficient data — learning' },
};

function getConfidenceColor(confidence: number) {
  if (confidence >= 80) return 'text-forge-400';
  if (confidence >= 60) return 'text-amber-400';
  return 'text-red-400';
}

export default function ProofAIEvidence({ playId }: ProofAIEvidenceProps) {
  const [expanded, setExpanded] = useState(false);
  const evidence = PLAY_PROOF_DATA[playId];

  if (!evidence) return null;

  return (
    <div className="rounded-lg border border-dark-700/50 bg-dark-800/30">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-3 py-2"
      >
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="h-3 w-3 text-emerald-400" />
          <span className="text-[11px] font-medium text-dark-200">ProofAI Evidence</span>
          <span className={clsx('text-[11px] font-bold tabular-nums', getConfidenceColor(evidence.confidence))}>
            {evidence.confidence}%
          </span>
        </div>
        <ChevronDown
          className={clsx(
            'h-3 w-3 text-dark-500 transition-transform',
            expanded && 'rotate-180'
          )}
        />
      </button>

      {expanded && (
        <div className="border-t border-dark-700/50 px-3 py-2.5 grid grid-cols-2 gap-3">
          <div>
            <p className="text-[10px] font-medium uppercase tracking-wider text-dark-500">Sample Size</p>
            <p className="text-sm font-bold tabular-nums text-dark-200">{evidence.sampleSize} games</p>
          </div>
          <div>
            <p className="text-[10px] font-medium uppercase tracking-wider text-dark-500">Win Rate</p>
            <p className={clsx('text-sm font-bold tabular-nums', evidence.winRate >= 60 ? 'text-forge-400' : 'text-red-400')}>
              {evidence.winRate}%
            </p>
          </div>
          <div>
            <p className="text-[10px] font-medium uppercase tracking-wider text-dark-500">Confidence</p>
            <p className={clsx('text-sm font-bold tabular-nums', getConfidenceColor(evidence.confidence))}>
              {evidence.confidence}%
            </p>
          </div>
          <div>
            <p className="text-[10px] font-medium uppercase tracking-wider text-dark-500">Data Source</p>
            <p className="text-xs text-dark-300">{evidence.dataSource}</p>
          </div>
        </div>
      )}
    </div>
  );
}
