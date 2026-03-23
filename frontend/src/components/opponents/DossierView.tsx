'use client';

import { Opponent } from '@/types/opponent';
import {
  Swords,
  AlertTriangle,
  BarChart3,
  Brain,
  Shield,
  Zap,
  Target,
  Clock,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface DossierViewProps {
  opponent: Opponent;
}

const severityColors: Record<string, string> = {
  low: 'bg-dark-700 text-dark-300',
  medium: 'bg-yellow-900/40 text-yellow-400',
  high: 'bg-orange-900/40 text-orange-400',
  critical: 'bg-red-900/40 text-red-400',
};

const frequencyDots: Record<string, number> = {
  rare: 1,
  occasional: 2,
  frequent: 3,
};

const signalIcons: Record<string, React.ReactNode> = {
  timeout: <Clock className="w-4 h-4" />,
  'pace-change': <Zap className="w-4 h-4" />,
  audible: <Brain className="w-4 h-4" />,
  'hot-route': <Target className="w-4 h-4" />,
  'formation-shift': <Shield className="w-4 h-4" />,
};

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-xs text-dark-400 mb-1">{label}</p>
      <p className="text-sm font-bold text-forge-400">Used {payload[0].value}x</p>
      {payload[1] && (
        <p className="text-xs text-dark-300">{payload[1].value}% success rate</p>
      )}
    </div>
  );
}

export default function DossierView({ opponent }: DossierViewProps) {
  const offenseTendencies = opponent.tendencies.filter((t) => t.category === 'offense');
  const defenseTendencies = opponent.tendencies.filter((t) => t.category === 'defense');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 p-6 rounded-xl border border-dark-700 bg-dark-900/50">
        <div className="w-16 h-16 rounded-full bg-dark-800 border-2 border-dark-600 flex items-center justify-center text-2xl font-bold text-dark-200">
          {opponent.gamertag.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-dark-50">{opponent.gamertag}</h1>
            {opponent.isRival && (
              <span className="flex items-center gap-1 px-2 py-1 text-xs font-bold bg-red-500/20 text-red-400 border border-red-800/50 rounded">
                <Swords className="w-3.5 h-3.5" />
                RIVAL
              </span>
            )}
          </div>
          <p className="text-dark-400 mt-1">
            {opponent.archetype} &middot; {opponent.encounterCount} encounters &middot; Last seen {opponent.lastSeen}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold font-mono text-forge-400">{opponent.winRate}%</p>
          <p className="text-xs text-dark-500">Win Rate vs</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tendency Breakdown */}
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
          <h2 className="text-lg font-bold text-dark-100 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-forge-400" />
            Tendency Breakdown
          </h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-blue-400 mb-2">Offense</h3>
              {offenseTendencies.map((t) => (
                <div key={t.label} className="flex items-center gap-3 mb-2">
                  <span className="text-sm text-dark-300 w-32 truncate">{t.label}</span>
                  <div className="flex-1 bg-dark-800 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-blue-500 transition-all"
                      style={{ width: `${t.percentage}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-dark-400 w-10 text-right">
                    {t.percentage}%
                  </span>
                </div>
              ))}
            </div>
            <div>
              <h3 className="text-sm font-medium text-red-400 mb-2">Defense</h3>
              {defenseTendencies.map((t) => (
                <div key={t.label} className="flex items-center gap-3 mb-2">
                  <span className="text-sm text-dark-300 w-32 truncate">{t.label}</span>
                  <div className="flex-1 bg-dark-800 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-red-500 transition-all"
                      style={{ width: `${t.percentage}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-dark-400 w-10 text-right">
                    {t.percentage}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Play Frequency Chart */}
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
          <h2 className="text-lg font-bold text-dark-100 mb-4">Play Frequency</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={opponent.playFrequencies} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis
                  dataKey="playName"
                  type="category"
                  stroke="#64748b"
                  fontSize={11}
                  width={100}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" fill="#22c55e" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weakness Map */}
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
          <h2 className="text-lg font-bold text-dark-100 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            Weakness Map
          </h2>
          <div className="space-y-2">
            {opponent.weaknesses.map((w, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-lg bg-dark-800/50 border border-dark-700"
              >
                <span
                  className={`flex-shrink-0 px-2 py-0.5 text-[10px] font-bold uppercase rounded ${severityColors[w.severity]}`}
                >
                  {w.severity}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-dark-100">{w.area}</p>
                  <p className="text-xs text-dark-400 mt-0.5">{w.description}</p>
                  {w.exploitPlay && (
                    <p className="text-xs text-forge-400 mt-1">
                      Exploit: {w.exploitPlay}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Behavioral Signals */}
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
          <h2 className="text-lg font-bold text-dark-100 mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            Behavioral Signals
          </h2>
          <div className="space-y-3">
            {opponent.behavioralSignals.map((signal, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-lg bg-dark-800/50 border border-dark-700"
              >
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-800/30 flex items-center justify-center text-purple-400">
                  {signalIcons[signal.type]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-dark-100 capitalize">
                      {signal.type.replace('-', ' ')}
                    </span>
                    <div className="flex gap-0.5">
                      {Array.from({ length: 3 }).map((_, j) => (
                        <span
                          key={j}
                          className={`w-1.5 h-1.5 rounded-full ${
                            j < frequencyDots[signal.frequency]
                              ? 'bg-purple-400'
                              : 'bg-dark-700'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-dark-400 mt-0.5">{signal.description}</p>
                  <p className="text-[10px] text-dark-500 mt-1">
                    Situation: {signal.situation}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
