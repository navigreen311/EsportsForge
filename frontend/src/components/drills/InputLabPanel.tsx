'use client';

import { Gamepad2, Gauge, AlertTriangle, Clock, Pause } from 'lucide-react';

interface InputLabPanelProps {
  drillsCompleted: number;
}

/* ── mock metric data ── */
const metrics = [
  {
    key: 'efficiency',
    label: 'Stick Efficiency',
    value: '78%',
    raw: 78,
    elite: 92,
    unit: '%',
    tooltip: 'How efficiently you use stick inputs',
    Icon: Gauge,
  },
  {
    key: 'overmovement',
    label: 'Over-movement',
    value: '12 incidents',
    raw: 12,
    elite: 4,
    unit: '',
    tooltip: 'Unnecessary stick movements during reads',
    Icon: AlertTriangle,
    lowerIsBetter: true,
  },
  {
    key: 'timing',
    label: 'Input Timing',
    value: '0.34s avg',
    raw: 0.34,
    elite: 0.21,
    unit: 's',
    tooltip: 'Average time from read to input',
    Icon: Clock,
    lowerIsBetter: true,
  },
  {
    key: 'hesitation',
    label: 'Hesitation Rate',
    value: '8%',
    raw: 8,
    elite: 3,
    unit: '%',
    tooltip: 'Percentage of plays with delayed input',
    Icon: Pause,
    lowerIsBetter: true,
  },
] as const;

/**
 * Determine color tier based on how close the player value is to the elite
 * benchmark. "Better than 70% of elite" means the player has closed ≥ 70 %
 * of the gap between worst-possible and elite.
 *
 * For "lower is better" metrics we invert so the math stays the same.
 */
function getTierColor(raw: number, elite: number, lowerIsBetter = false) {
  // Normalise: ratio = how "good" the value is relative to elite (1 = elite)
  let ratio: number;
  if (lowerIsBetter) {
    // e.g. 12 incidents vs elite 4 → ratio ≈ 4/12 = 0.33
    ratio = elite === 0 ? (raw === 0 ? 1 : 0) : elite / raw;
  } else {
    // e.g. 78 % vs elite 92 % → ratio ≈ 0.85
    ratio = elite === 0 ? 1 : raw / elite;
  }

  if (ratio >= 0.7) return 'text-emerald-400';
  if (ratio >= 0.4) return 'text-amber-400';
  return 'text-red-400';
}

export default function InputLabPanel({ drillsCompleted }: InputLabPanelProps) {
  const locked = drillsCompleted < 3;

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
      {/* Header */}
      <h2 className="text-sm font-bold text-dark-300 uppercase tracking-wider mb-4 flex items-center gap-2">
        <Gamepad2 className="w-4 h-4 text-cyan-400" />
        Input Efficiency
      </h2>

      {locked ? (
        <p className="text-sm text-dark-500 text-center py-6">
          Complete 3 drills to activate InputLab tracking
        </p>
      ) : (
        <div className="space-y-2">
          {/* Metric rows */}
          {metrics.map((m) => {
            const color = getTierColor(m.raw, m.elite, 'lowerIsBetter' in m && m.lowerIsBetter);
            return (
              <div
                key={m.key}
                className="flex items-center justify-between p-2 rounded-lg bg-dark-800/40"
                title={m.tooltip}
              >
                <div className="flex items-center gap-2">
                  <m.Icon className={`w-4 h-4 ${color}`} />
                  <span className="text-xs font-medium text-dark-300">
                    {m.label}
                  </span>
                </div>
                <span className={`text-sm font-bold tabular-nums ${color}`}>
                  {m.value}
                </span>
              </div>
            );
          })}

          {/* Benchmark comparison */}
          <div className="mt-3 flex items-center justify-between p-2 rounded-lg bg-dark-800/40 border border-dark-700/60">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-dark-500">
              vs. Elite Benchmark
            </span>
            <div className="flex items-center gap-3 text-[11px] font-mono text-dark-400">
              <span>92%</span>
              <span>4</span>
              <span>0.21s</span>
              <span>3%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
