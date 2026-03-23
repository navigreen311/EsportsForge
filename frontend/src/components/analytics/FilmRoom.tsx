'use client';

import { useState } from 'react';
import { Camera, History, Eye } from 'lucide-react';
import ReplayUploader from '@/components/film/ReplayUploader';
import FilmBreakdown from '@/components/film/FilmBreakdown';

const PAST_REPLAYS = [
  { date: '2026-03-20', opponent: 'xXDragonSlayerXx', grade: 'B+', topFix: 'Speed up pre-snap reads' },
  { date: '2026-03-18', opponent: 'BlitzMaster99', grade: 'A-', topFix: 'Check down earlier' },
  { date: '2026-03-15', opponent: 'GridironGhost', grade: 'C+', topFix: 'Avoid forced throws' },
];

function gradeColor(grade: string): string {
  if (grade.startsWith('A')) return 'text-forge-400';
  if (grade.startsWith('B')) return 'text-amber-400';
  return 'text-red-400';
}

export default function FilmRoom() {
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [pastReplays] = useState(PAST_REPLAYS);

  const handleReset = () => {
    setAnalysisResult(null);
  };

  return (
    <div className="space-y-6">
      {/* Main Content */}
      {!analysisResult && pastReplays.length === 0 ? (
        /* Empty state — no analysis, no past replays */
        <div className="flex min-h-[400px] flex-col items-center justify-center text-center">
          <Camera className="mb-4 h-14 w-14 text-dark-600" />
          <h2 className="text-xl font-bold text-white">Film Room</h2>
          <p className="mb-1 text-sm text-dark-400">Powered by VisionAudioForge</p>
          <p className="mb-6 max-w-md text-dark-300">
            Upload a game replay and let FilmAI break down every play, tag mistakes,
            and give you a prioritized fix list so you improve faster.
          </p>
          <ReplayUploader onAnalysisComplete={setAnalysisResult} />
        </div>
      ) : !analysisResult ? (
        /* No current analysis but past replays exist */
        <div className="flex min-h-[400px] flex-col items-center justify-center text-center">
          <Camera className="mb-4 h-14 w-14 text-dark-600" />
          <h2 className="text-xl font-bold text-white">Film Room</h2>
          <p className="mb-1 text-sm text-dark-400">Powered by VisionAudioForge</p>
          <p className="mb-6 max-w-md text-dark-300">
            Upload a game replay and let FilmAI break down every play, tag mistakes,
            and give you a prioritized fix list so you improve faster.
          </p>
          <ReplayUploader onAnalysisComplete={setAnalysisResult} />
        </div>
      ) : (
        /* Analysis complete */
        <div>
          <FilmBreakdown result={analysisResult} />
          <div className="mt-4 text-center">
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

      {/* Past Replays Section */}
      {pastReplays.length > 0 && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <History className="h-4 w-4 text-dark-400" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-300">
              Previous Analyses
            </h3>
          </div>

          <div className="space-y-2">
            {pastReplays.map((replay, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-lg bg-dark-800/40 border border-dark-700/50"
              >
                <span className="text-sm text-dark-400 w-24 shrink-0">{replay.date}</span>
                <span className="text-sm font-medium text-white w-40 shrink-0">{replay.opponent}</span>
                <span className={`text-sm font-bold w-10 shrink-0 ${gradeColor(replay.grade)}`}>
                  {replay.grade}
                </span>
                <span className="text-sm text-dark-300 flex-1">{replay.topFix}</span>
                <button
                  type="button"
                  className="ml-3 flex items-center gap-1 rounded-md border border-dark-600 px-3 py-1 text-xs font-medium text-dark-300 transition-colors hover:border-dark-400 hover:text-white"
                >
                  <Eye className="h-3 w-3" />
                  View
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
