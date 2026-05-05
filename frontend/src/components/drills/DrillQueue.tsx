'use client';

import { useState } from 'react';
import { DrillRecord } from '@/types/analytics';
import { Flame, ListOrdered, Play, Sparkles } from 'lucide-react';
import { DrillMasteryDot } from '@/components/drills/DrillMasteryDot';
import SimLabLaunchButton from '@/components/drills/SimLabLaunchButton';
import { useAnimaForgeAvailable } from '@/hooks/useAnimaForge';
import { animaforgeApi } from '@/lib/animaforge/api';
import { useActiveTitle } from '@/hooks/useActiveTitle';

interface DrillQueueProps {
  queue: DrillRecord[];
  currentDrill: DrillRecord | null;
}

/**
 * Per-drill cached thumbnail metadata. Fetched lazily on first hover so the
 * queue mounts cheaply (no N parallel requests for an entire session).
 */
interface DrillThumbState {
  loaded: boolean;
  thumbnailUrl: string | null;
  videoUrl: string | null;
}

const difficultyColors: Record<string, string> = {
  beginner: 'text-green-400',
  intermediate: 'text-yellow-400',
  advanced: 'text-orange-400',
  elite: 'text-red-400',
};

export default function DrillQueue({ queue, currentDrill }: DrillQueueProps) {
  const { available: animaAvailable } = useAnimaForgeAvailable();
  const { activeTitleId } = useActiveTitle();
  const [thumbs, setThumbs] = useState<Record<string, DrillThumbState>>({});
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const showAnimaForgeUI = animaAvailable === true;

  const ensureThumb = (drillId: string) => {
    if (!showAnimaForgeUI) return;
    if (thumbs[drillId]?.loaded) return;
    // Mark as loaded immediately to avoid duplicate requests on rapid hovers.
    setThumbs((prev) => ({
      ...prev,
      [drillId]: { loaded: true, thumbnailUrl: null, videoUrl: null },
    }));
    animaforgeApi
      .getDrillStatus({ title_id: activeTitleId, drill_type: drillId })
      .then((data) => {
        setThumbs((prev) => ({
          ...prev,
          [drillId]: {
            loaded: true,
            thumbnailUrl: data.thumbnail_url ?? null,
            videoUrl: data.video_url ?? null,
          },
        }));
      })
      .catch(() => {
        // Stay silent.
      });
  };

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
      <h2 className="text-sm font-bold text-dark-300 uppercase tracking-wider mb-4 flex items-center gap-2">
        <ListOrdered className="w-4 h-4 text-forge-400" />
        Drill Queue
      </h2>

      {/* Current Drill Indicator */}
      {currentDrill && (
        <div className="mb-4 p-3 rounded-lg border border-forge-500/30 bg-forge-950/20">
          <p className="text-[10px] text-forge-400 uppercase tracking-wider font-bold mb-1">
            Now Playing
          </p>
          <p className="text-sm font-bold text-dark-50 truncate">
            {currentDrill.name}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <Flame className="w-3 h-3 text-orange-400" />
            <span className="text-xs font-mono text-dark-400">
              IR {currentDrill.impactRank}
            </span>
          </div>
        </div>
      )}

      {/* Queued Drills */}
      {queue.length > 0 ? (
        <div className="space-y-2">
          {queue.map((drill, index) => {
            const thumb = thumbs[drill.id];
            const isHovered = hoveredId === drill.id;
            return (
              <div
                key={drill.id}
                onMouseEnter={() => {
                  setHoveredId(drill.id);
                  ensureThumb(drill.id);
                }}
                onMouseLeave={() => {
                  setHoveredId((curr) => (curr === drill.id ? null : curr));
                }}
                className="relative flex items-center gap-3 p-3 rounded-lg bg-dark-800/40 border border-dark-700/50 hover:border-dark-600 transition-colors min-h-[56px]"
              >
                {/* Position */}
                <span className="text-xs font-mono text-dark-600 w-5 text-center">
                  {index + 1}
                </span>
                <DrillMasteryDot drillId={drill.id} inline />

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <p className="text-sm font-medium text-dark-200 line-clamp-2" title={drill.name}>
                      {drill.name}
                    </p>
                    {drill.isDynamicCalibration && (
                      <Sparkles className="w-3 h-3 text-purple-400 shrink-0" />
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-2 mt-0.5">
                    <span
                      className={`text-[10px] font-medium ${difficultyColors[drill.difficulty]}`}
                    >
                      {drill.difficulty}
                    </span>
                    <span className="text-dark-700">·</span>
                    <span className="text-[10px] text-dark-500">
                      {drill.reps} reps
                    </span>
                  </div>
                </div>

                {/* Impact Rank + SimLab */}
                <div className="flex items-center gap-2 shrink-0">
                  <SimLabLaunchButton drillId={drill.id} drillName={drill.name} variant="icon" />
                  <div className="flex items-center gap-1">
                    <Flame className="w-3 h-3 text-orange-400" />
                    <span className="text-sm font-mono font-bold text-dark-300">
                      {drill.impactRank}
                    </span>
                  </div>
                </div>

                {/* AnimaForge: hover thumbnail preview */}
                {showAnimaForgeUI && isHovered && (
                  <div
                    className="pointer-events-none absolute right-0 top-full z-20 mt-1 w-44 rounded-md border border-dark-700 bg-dark-900 p-2 shadow-lg"
                    aria-hidden="true"
                  >
                    <div className="relative w-full aspect-video rounded bg-dark-800 overflow-hidden flex items-center justify-center">
                      {thumb?.thumbnailUrl ? (
                        <img
                          src={thumb.thumbnailUrl}
                          alt=""
                          className="absolute inset-0 w-full h-full object-cover"
                        />
                      ) : null}
                      <div className="relative flex h-7 w-7 items-center justify-center rounded-full bg-dark-950/70 border border-forge-500/40">
                        <Play className="h-3.5 w-3.5 text-forge-400" />
                      </div>
                    </div>
                    <p className="mt-1.5 text-[10px] uppercase tracking-wider text-dark-500">
                      Preview
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-6">
          <p className="text-sm text-dark-500">Queue empty</p>
          <p className="text-xs text-dark-600 mt-1">
            All drills completed or in progress
          </p>
        </div>
      )}

      {/* Queue Stats */}
      {queue.length > 0 && (
        <div className="mt-4 pt-3 border-t border-dark-700/50">
          <div className="flex justify-between text-xs text-dark-500">
            <span>{queue.length} drills remaining</span>
            <span>
              {queue.reduce((sum, d) => sum + d.reps, 0)} total reps
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
