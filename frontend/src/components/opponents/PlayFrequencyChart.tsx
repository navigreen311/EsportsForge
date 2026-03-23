'use client';

import { PlayFrequency } from '@/types/opponent';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface PlayFrequencyChartProps {
  data: PlayFrequency[];
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-xs text-dark-400 mb-1">{label}</p>
      <p className="text-sm font-bold text-forge-400">Used {payload[0].value}x</p>
      {payload[0]?.payload?.successRate !== undefined && (
        <p className="text-xs text-dark-300">{payload[0].payload.successRate}% success rate</p>
      )}
    </div>
  );
}

export default function PlayFrequencyChart({ data }: PlayFrequencyChartProps) {
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis type="number" stroke="#64748b" fontSize={11} />
          <YAxis
            dataKey="playName"
            type="category"
            stroke="#64748b"
            fontSize={11}
            width={110}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="count" fill="#22c55e" radius={[0, 4, 4, 0]} barSize={16} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
