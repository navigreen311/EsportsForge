'use client';

import { RadarDimension } from '@/hooks/useProfile';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface PerformanceRadarProps {
  data: RadarDimension[];
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 shadow-xl">
      <p className="text-xs text-dark-400">{payload[0].payload.dimension}</p>
      <p className="text-lg font-bold text-forge-400">{payload[0].value}</p>
    </div>
  );
}

export default function PerformanceRadar({ data }: PerformanceRadarProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <h2 className="text-lg font-bold text-dark-100 mb-4">
        Performance Radar
      </h2>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: '#475569', fontSize: 9 }}
              axisLine={false}
            />
            <Radar
              name="Player"
              dataKey="value"
              stroke="#22c55e"
              fill="#22c55e"
              fillOpacity={0.2}
              strokeWidth={2}
            />
            <Tooltip content={<CustomTooltip />} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
