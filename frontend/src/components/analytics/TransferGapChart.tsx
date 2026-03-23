'use client';

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
import { ArrowRightLeft } from 'lucide-react';
import { useState } from 'react';

const skills = [
  'Read Speed',
  'Execution',
  'Clutch',
  'Anti-Meta',
  'Mental',
  'Game Knowledge',
] as const;

type Skill = (typeof skills)[number];

function generateData(seed: number) {
  return Array.from({ length: 30 }, (_, i) => {
    const pseudoRandom = (offset: number) =>
      Math.sin(seed * 1000 + i * 37 + offset) * 0.5 + 0.5;

    return {
      name: `Day ${i + 1}`,
      drill: Math.round(70 + pseudoRandom(1) * 25),
      ranked: Math.round(40 + pseudoRandom(2) * 30),
      tournament: Math.round(25 + pseudoRandom(3) * 30),
    };
  });
}

const dataBySkill: Record<Skill, ReturnType<typeof generateData>> = {
  'Read Speed': generateData(1),
  Execution: generateData(2),
  Clutch: generateData(3),
  'Anti-Meta': generateData(4),
  Mental: generateData(5),
  'Game Knowledge': generateData(6),
};

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-xs text-dark-400 mb-1">{label}</p>
      {payload.map((entry: any, idx: number) => (
        <p key={idx} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.value}%
        </p>
      ))}
    </div>
  );
}

export default function TransferGapChart() {
  const [selectedSkill, setSelectedSkill] = useState<Skill>('Read Speed');
  const data = dataBySkill[selectedSkill];

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ArrowRightLeft className="h-5 w-5 text-forge-400" />
          <h3 className="text-lg font-semibold text-white">
            Skill Transfer Analysis
          </h3>
        </div>
        <select
          value={selectedSkill}
          onChange={(e) => setSelectedSkill(e.target.value as Skill)}
          className="rounded-lg border border-dark-600 bg-dark-800 px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-forge-400"
        >
          {skills.map((skill) => (
            <option key={skill} value={skill}>
              {skill}
            </option>
          ))}
        </select>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="name"
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

            {/* Shaded transfer gap area between drill and ranked */}
            <Area
              type="monotone"
              dataKey="drill"
              stroke="none"
              fill="#22c55e"
              fillOpacity={0.1}
            />
            <Area
              type="monotone"
              dataKey="ranked"
              stroke="none"
              fill="#1a1a2e"
              fillOpacity={1}
            />

            {/* Drill performance — dashed green */}
            <Line
              type="monotone"
              dataKey="drill"
              name="Drill"
              stroke="#22c55e"
              strokeDasharray="5 5"
              strokeWidth={2}
              dot={false}
            />

            {/* Ranked performance — solid green */}
            <Line
              type="monotone"
              dataKey="ranked"
              name="Ranked"
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
            />

            {/* Tournament performance — solid amber */}
            <Line
              type="monotone"
              dataKey="tournament"
              name="Tournament"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Transfer gap callout */}
      <p className="mt-4 text-sm text-amber-400">
        Your largest transfer gap: Pre-Snap Reads (-37%) — this skill is not
        competition-ready
      </p>

      {/* Legend */}
      <div className="mt-3 flex items-center gap-6 text-xs text-dark-400">
        <div className="flex items-center gap-2">
          <span className="inline-block w-6 border-t-2 border-dashed border-green-500" />
          <span>Drill</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-6 border-t-2 border-green-500" />
          <span>Ranked</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-6 border-t-2 border-amber-500" />
          <span>Tournament</span>
        </div>
      </div>
    </div>
  );
}
