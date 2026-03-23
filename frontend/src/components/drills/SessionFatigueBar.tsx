'use client';

import { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

interface SessionFatigueBarProps {
  sessionStartTime: Date | null;
  onPause?: () => void;
}

type Zone = 'green' | 'amber' | 'red';

const zoneConfig: Record<Zone, { bar: string; label: string }> = {
  green: { bar: 'bg-forge-500', label: 'Peak performance window' },
  amber: { bar: 'bg-amber-500', label: 'Fatigue building — maintain focus' },
  red: { bar: 'bg-red-500', label: 'Cognitive load high — consider ending session' },
};

function getZone(minutes: number): Zone {
  if (minutes < 45) return 'green';
  if (minutes < 75) return 'amber';
  return 'red';
}

export default function SessionFatigueBar({
  sessionStartTime,
  onPause,
}: SessionFatigueBarProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!sessionStartTime) {
      setElapsed(0);
      return;
    }

    const tick = () => {
      const now = new Date();
      const diffMs = now.getTime() - sessionStartTime.getTime();
      setElapsed(Math.floor(diffMs / 60_000));
    };

    tick();
    const id = setInterval(tick, 30_000);
    return () => clearInterval(id);
  }, [sessionStartTime]);

  if (!sessionStartTime) {
    return (
      <div className="flex items-center gap-2 text-xs text-dark-500">
        <Clock className="h-3.5 w-3.5" />
        <span>Start a session to track fatigue</span>
      </div>
    );
  }

  const zone = getZone(elapsed);
  const config = zoneConfig[zone];
  const fillWidth = Math.min(100, (elapsed / 90) * 100);

  return (
    <div className="space-y-1.5">
      {/* Compact row: label + time + bar */}
      <div className="flex items-center gap-3">
        <span className="shrink-0 text-xs font-medium text-dark-300">
          Session Health
        </span>

        <span className="shrink-0 flex items-center gap-1 text-[10px] text-dark-400">
          <Clock className="h-3 w-3" />
          {elapsed} min
        </span>

        <div className="h-1.5 w-full overflow-hidden rounded-full bg-dark-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${config.bar}`}
            style={{ width: `${fillWidth}%` }}
          />
        </div>
      </div>

      {/* Zone label */}
      <p className="text-[10px] text-dark-500">{config.label}</p>

      {/* Amber banner */}
      {zone === 'amber' && (
        <div className="rounded bg-amber-500/15 px-3 py-1.5 text-xs text-amber-400">
          You've been drilling for {elapsed} min — fatigue may affect precision.
          Consider a 5-min break.
        </div>
      )}

      {/* Red warning */}
      {zone === 'red' && (
        <div className="flex items-center justify-between rounded bg-red-500/15 px-3 py-2 text-xs text-red-400">
          <span>
            You've been drilling for {elapsed} min — fatigue may affect
            precision. Consider a 5-min break.
          </span>
          {onPause && (
            <button
              type="button"
              onClick={onPause}
              className="ml-3 shrink-0 rounded bg-red-500 px-3 py-1 text-xs font-semibold text-white transition-colors hover:bg-red-600"
            >
              Take a Break
            </button>
          )}
        </div>
      )}
    </div>
  );
}
