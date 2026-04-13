'use client';

import { useState } from 'react';
import { Camera, History, Eye, ChevronDown } from 'lucide-react';
import ReplayUploader from '@/components/film/ReplayUploader';
import FilmBreakdown from '@/components/film/FilmBreakdown';

const PAST_REPLAYS = [
  { date: '2026-03-20', opponent: 'xXDragonSlayerXx', grade: 'B+', topFix: 'Speed up pre-snap reads' },
  { date: '2026-03-18', opponent: 'BlitzMaster99', grade: 'A-', topFix: 'Check down earlier' },
  { date: '2026-03-15', opponent: 'GridironGhost', grade: 'C+', topFix: 'Avoid forced throws' },
  { date: '2026-03-10', opponent: 'PocketPasser22', grade: 'B', topFix: 'Improve hot route timing' },
  { date: '2026-03-06', opponent: 'ZoneBreaker7', grade: 'A', topFix: 'Tighten red zone audibles' },
  { date: '2026-03-01', opponent: 'NanoBlitz44', grade: 'C', topFix: 'Stop telegraphing throws' },
  { date: '2026-02-25', opponent: 'SlideMaster_QB', grade: 'B-', topFix: 'Use play-action more' },
];

const REPLAYS_PER_PAGE = 5;

function gradeColor(grade: string): string {
  if (grade.startsWith('A')) return 'text-forge-400';
  if (grade.startsWith('B')) return 'text-amber-400';
  return 'text-red-400';
}

export default function FilmRoom() {
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [pastReplays] = useState(PAST_REPLAYS);
  const [visibleCount, setVisibleCount] = useState(REPLAYS_PER_PAGE);

  const handleReset = () => {
    setAnalysisResult(null);
  };

  const handleLoadMore = () => {
    setVisibleCount((prev) => prev + REPLAYS_PER_PAGE);
  };

  const visibleReplays = pastReplays.slice(0, visibleCount);
  const hasMore = visibleCount < pastReplays.length;

  return (
    <div className="space-y-8">
      {/* Main Content */}
      {!analysisResult ? (
        /* STATE 1 — Upload zone (shown when no analysis is active) */
        <div className="flex min-h-[420px] flex-col items-center justify-center text-center">
          <Camera className="mb-4 h-14 w-14 text-dark-600" />
          <h2 className="text-xl font-bold text-white">Film Room</h2>
          <p className="mb-1 text-sm text-dark-400">Powered by VisionAudioForge</p>
          <p className="mb-8 max-w-md text-dark-300">
            Upload a replay and FilmAI watches it, tags every mistake, and tells you what cost you the game.
          </p>
          <ReplayUploader onAnalysisComplete={setAnalysisResult} />
        </div>
      ) : (
        /* STATE 3 — Analysis complete */
        <div>
          <FilmBreakdown result={analysisResult} />
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={handleReset}
              className="rounded-lg border border-dark-600 px-5 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-400 hover:text-white"
            >
              Upload Another Replay
            </button>
          </div>
        </div>
      )}

      {/* Previous Replays Section — always shown */}
      {pastReplays.length > 0 && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <History className="h-4 w-4 text-dark-400" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-300">
              Previous Analyses
            </h3>
          </div>

          {/* Table header */}
          <div className="hidden sm:grid grid-cols-[100px_1fr_60px_1fr_70px] gap-3 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-dark-500">
            <span>Date</span>
            <span>Opponent</span>
            <span>Grade</span>
            <span>Top Fix</span>
            <span></span>
          </div>

          <div className="space-y-2">
            {visibleReplays.map((replay, i) => (
              <div
                key={i}
                className="grid grid-cols-1 sm:grid-cols-[100px_1fr_60px_1fr_70px] gap-2 sm:gap-3 items-center p-3 rounded-lg bg-dark-800/40 border border-dark-700/50"
              >
                <span className="text-sm text-dark-400">{replay.date}</span>
                <span className="text-sm font-medium text-white">{replay.opponent}</span>
                <span className={`text-sm font-bold ${gradeColor(replay.grade)}`}>
                  {replay.grade}
                </span>
                <span className="text-sm text-dark-300">{replay.topFix}</span>
                <button
                  type="button"
                  className="flex items-center gap-1 rounded-md border border-dark-600 px-3 py-1 text-xs font-medium text-dark-300 transition-colors hover:border-dark-400 hover:text-white justify-self-start sm:justify-self-end"
                >
                  <Eye className="h-3 w-3" />
                  View
                </button>
              </div>
            ))}
          </div>

          {hasMore && (
            <div className="mt-4 text-center">
              <button
                type="button"
                onClick={handleLoadMore}
                className="inline-flex items-center gap-1.5 rounded-lg border border-dark-600 px-4 py-2 text-sm font-medium text-dark-300 transition-colors hover:border-dark-400 hover:text-white"
              >
                <ChevronDown className="h-4 w-4" />
                Load More
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
