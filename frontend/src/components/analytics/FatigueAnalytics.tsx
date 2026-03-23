'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Battery } from 'lucide-react';

const sessionData = [
  { range: '0-30min', winRate: 72, color: '#22c55e' },
  { range: '30-60min', winRate: 68, color: '#22c55e' },
  { range: '60-90min', winRate: 55, color: '#f59e0b' },
  { range: '90min+', winRate: 38, color: '#ef4444' },
];

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const timeBlocks = ['Morning', 'Afternoon', 'Evening', 'Night'];
const timeLabels = ['6-12', '12-6', '6-10', '10-2'];

// Mock heatmap data: [day][timeBlock] => winRate | null
const heatmapData: (number | null)[][] = [
  [32, 55, 71, 48], // Mon
  [28, 52, 68, 44], // Tue
  [35, 58, 73, 50], // Wed
  [30, 48, 70, 42], // Thu
  [40, 60, 75, 55], // Fri
  [38, 62, 78, 52], // Sat
  [42, 50, 69, null], // Sun
];

function getCellColor(value: number | null): string {
  if (value === null) return 'bg-dark-700 text-dark-500';
  if (value > 65) return 'bg-green-500/30 text-green-300';
  if (value >= 45) return 'bg-amber-500/30 text-amber-300';
  return 'bg-red-500/30 text-red-300';
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-xs text-dark-400 mb-1">{label}</p>
      <p className="text-lg font-bold text-forge-400">{payload[0].value}%</p>
    </div>
  );
}

export default function FatigueAnalytics() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Battery className="h-5 w-5 text-forge-400" />
        <h2 className="text-lg font-bold text-dark-100">
          Performance &amp; Fatigue Patterns
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* A) Win Rate by Session Length */}
        <div>
          <h3 className="text-sm font-semibold text-dark-300 mb-3">
            Win Rate by Session Length
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={sessionData}
                margin={{ top: 5, right: 5, bottom: 5, left: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="range"
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="winRate" radius={[4, 4, 0, 0]}>
                  {sessionData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* B) Peak Performance Hours */}
        <div>
          <h3 className="text-sm font-semibold text-dark-300 mb-3">
            Peak Performance Hours
          </h3>
          <div>
            {/* Header row */}
            <div className="grid grid-cols-[auto_1fr_1fr_1fr_1fr] gap-1 mb-1">
              <div className="w-8" />
              {timeBlocks.map((block, i) => (
                <div
                  key={block}
                  className="text-[9px] text-dark-500 text-center"
                >
                  {block}
                  <br />
                  <span className="text-dark-600">{timeLabels[i]}</span>
                </div>
              ))}
            </div>

            {/* Data rows */}
            {days.map((day, dayIdx) => (
              <div
                key={day}
                className="grid grid-cols-[auto_1fr_1fr_1fr_1fr] gap-1 mb-1"
              >
                <div className="w-8 text-[9px] text-dark-500 flex items-center">
                  {day}
                </div>
                {heatmapData[dayIdx].map((value, colIdx) => (
                  <div
                    key={colIdx}
                    className={`h-6 w-full rounded text-[9px] flex items-center justify-center ${getCellColor(value)}`}
                  >
                    {value !== null ? `${value}%` : '—'}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendation box */}
      <div className="rounded-lg border border-forge-500/20 bg-forge-500/5 p-3 text-sm text-forge-300 mt-6">
        Recommended session: 60-75 min | Peak hours: 7pm-10pm | Avoid: sessions
        over 90 min
      </div>
    </div>
  );
}
