'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Brain } from 'lucide-react';

const data = Array.from({ length: 30 }, (_, i) => ({
  day: `Day ${i + 1}`,
  accuracy: Math.round(55 + i * 0.9 + Math.random() * 5),
}));

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-xs text-dark-400 mb-1">{label}</p>
      <p className="text-sm text-green-400">
        Accuracy: {payload[0].value}%
      </p>
    </div>
  );
}

export default function PlayerTwinEvolution() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center gap-3 mb-5">
        <Brain className="w-5 h-5 text-cyan-400" />
        <div>
          <h2 className="text-lg font-bold text-dark-100">
            PlayerTwin Model Evolution
          </h2>
          <p className="text-sm text-dark-400">
            The more you play, the smarter your twin gets
          </p>
        </div>
      </div>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="day"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#374151' }}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#374151' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="accuracy"
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-4 text-xs text-purple-400">
        Twin updated after game vs xXDragonSlayerXx — coverage pattern learned
      </p>
    </div>
  );
}
