'use client';

import { WinRateDataPoint } from '@/types/analytics';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

interface WinRateChartProps {
  data: WinRateDataPoint[];
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-xs text-dark-400 mb-1">{label}</p>
      <p className="text-lg font-bold text-forge-400">{payload[0].value}%</p>
      <p className="text-xs text-dark-500">{payload[0].payload.sessions} sessions</p>
    </div>
  );
}

export default function WinRateChart({ data }: WinRateChartProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-dark-100">Win Rate Trend</h2>
          <p className="text-sm text-dark-400">Last 30 sessions</p>
        </div>
        {data.length > 0 && (
          <div className="text-right">
            <p className="text-2xl font-bold text-forge-400">
              {data[data.length - 1].winRate}%
            </p>
            <p className="text-xs text-dark-500">Current</p>
          </div>
        )}
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <defs>
              <linearGradient id="winRateGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="date"
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
            <Area
              type="monotone"
              dataKey="winRate"
              stroke="#22c55e"
              strokeWidth={2}
              fill="url(#winRateGradient)"
              dot={false}
              activeDot={{ r: 4, fill: '#22c55e', stroke: '#020617', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
