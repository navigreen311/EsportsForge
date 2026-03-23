'use client';

import { useProfile } from '@/hooks/useProfile';
import PerformanceRadar from '@/components/profile/PerformanceRadar';
import IdentityCard from '@/components/profile/IdentityCard';
import ExecutionCeiling from '@/components/profile/ExecutionCeiling';
import BenchmarkComparison from '@/components/profile/BenchmarkComparison';
import {
  User,
  Shield,
  Calendar,
  Gamepad2,
  Star,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Wifi,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react';
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

const severityColors: Record<string, string> = {
  low: 'text-green-400 bg-green-500/10 border-green-800/30',
  medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-800/30',
  high: 'text-red-400 bg-red-500/10 border-red-800/30',
};

const trendIcons = {
  up: <ArrowUpRight className="w-4 h-4 text-forge-400" />,
  down: <ArrowDownRight className="w-4 h-4 text-red-400" />,
  stable: <Minus className="w-4 h-4 text-dark-400" />,
};

function SparklineTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded px-2 py-1 shadow-xl">
      <p className="text-xs font-mono text-forge-400">{payload[0].value}</p>
    </div>
  );
}

export default function ProfilePage() {
  const { profile, tierColor } = useProfile();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-dark-50 flex items-center gap-3">
          <User className="w-8 h-8 text-forge-400" />
          Player Profile
        </h1>
        <p className="text-dark-400 mt-1">Your PlayerTwin overview</p>
      </div>

      {/* PlayerTwin Summary Card */}
      <div className="rounded-xl border border-dark-700 bg-gradient-to-r from-dark-900/80 to-dark-900/50 p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            {/* Avatar placeholder */}
            <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-forge-600 to-forge-800 flex items-center justify-center text-2xl font-bold text-dark-950">
              {profile.name.charAt(0)}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-dark-50">
                {profile.name}
              </h2>
              <p className="text-sm text-dark-400">{profile.title}</p>
              <div className="flex items-center gap-3 mt-1">
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold rounded border ${tierColor}`}
                >
                  <Shield className="w-3 h-3" />
                  {profile.tier}
                </span>
                <span className="flex items-center gap-1 text-xs text-dark-500">
                  <Calendar className="w-3 h-3" />
                  Since {profile.memberSince}
                </span>
              </div>
            </div>
          </div>

          {/* Quick stats */}
          <div className="flex items-center gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold font-mono text-forge-400">
                {profile.overallRating}
              </p>
              <p className="text-[10px] text-dark-500 uppercase tracking-wider">
                Overall
              </p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold font-mono text-dark-100">
                {profile.gamesPlayed}
              </p>
              <p className="text-[10px] text-dark-500 uppercase tracking-wider">
                Games
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Radar + Identity — 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceRadar data={profile.radar} />
        <IdentityCard traits={profile.identity} />
      </div>

      {/* Execution Ceiling + Benchmark — 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ExecutionCeiling skills={profile.executionCeiling} />
        <BenchmarkComparison benchmarks={profile.benchmarks} />
      </div>

      {/* Transfer Rate + Input Profile — 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transfer Rate Card */}
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
          <h2 className="text-lg font-bold text-dark-100 mb-1 flex items-center gap-2">
            <ArrowUpRight className="w-5 h-5 text-forge-400" />
            Transfer Rate
          </h2>
          <p className="text-xs text-dark-500 mb-4">
            Skill transfer across contexts
          </p>

          <div className="space-y-3">
            {profile.transferRates.map((tr) => (
              <div
                key={tr.context}
                className="flex items-center justify-between p-3 rounded-lg bg-dark-800/40 border border-dark-700/50"
              >
                <div className="flex items-center gap-3">
                  {trendIcons[tr.trend]}
                  <div>
                    <p className="text-sm font-medium text-dark-200">
                      {tr.context}
                    </p>
                    <p className="text-[10px] text-dark-500">
                      {tr.trend === 'up'
                        ? 'Improving'
                        : tr.trend === 'down'
                        ? 'Declining'
                        : 'Stable'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p
                    className={`text-xl font-bold font-mono ${
                      tr.rate >= 70
                        ? 'text-forge-400'
                        : tr.rate >= 50
                        ? 'text-yellow-400'
                        : 'text-red-400'
                    }`}
                  >
                    {tr.rate}%
                  </p>
                  <p className="text-[10px] text-dark-500">success rate</p>
                </div>
              </div>
            ))}
          </div>

          {/* Visual flow indicator */}
          <div className="flex items-center justify-center gap-2 mt-4 pt-3 border-t border-dark-700/50">
            {profile.transferRates.map((tr, i) => (
              <div key={tr.context} className="flex items-center gap-2">
                <div className="text-center">
                  <p className="text-xs font-mono text-dark-300">{tr.rate}%</p>
                  <p className="text-[9px] text-dark-500">{tr.context}</p>
                </div>
                {i < profile.transferRates.length - 1 && (
                  <ArrowUpRight className="w-3 h-3 text-dark-600 rotate-90" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Input Profile Card */}
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
          <h2 className="text-lg font-bold text-dark-100 mb-1 flex items-center gap-2">
            <Gamepad2 className="w-5 h-5 text-blue-400" />
            Input Profile
          </h2>
          <p className="text-xs text-dark-500 mb-4">
            Controller and mechanical analysis
          </p>

          {/* Controller Info */}
          <div className="p-3 rounded-lg bg-dark-800/40 border border-dark-700/50 mb-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-dark-200">
                  {profile.inputProfile.controllerType}
                </p>
                <p className="text-[10px] text-dark-500">Active Controller</p>
              </div>
              <div className="flex items-center gap-1.5">
                <Wifi className="w-4 h-4 text-dark-400" />
                <span className="text-sm font-mono text-dark-300">
                  {profile.inputProfile.inputDelay}ms
                </span>
              </div>
            </div>
          </div>

          {/* Mechanical Leakage */}
          <h3 className="text-sm font-medium text-dark-300 mb-3 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
            Mechanical Leakage
          </h3>
          <div className="space-y-2">
            {profile.inputProfile.mechanicalLeakage.map((leak) => (
              <div
                key={leak.name}
                className="flex items-center justify-between p-2.5 rounded-lg bg-dark-800/40 border border-dark-700/50"
              >
                <span className="text-sm text-dark-200">{leak.name}</span>
                <span
                  className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded border ${severityColors[leak.severity]}`}
                >
                  {leak.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Improvement Velocity — Full width */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-1 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-forge-400" />
          Improvement Velocity
        </h2>
        <p className="text-xs text-dark-500 mb-4">
          8-week trend sparklines for key metrics
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {profile.improvementVelocity.map((metric) => {
            const firstVal = metric.data[0].value;
            const lastVal = metric.data[metric.data.length - 1].value;
            const change = lastVal - firstVal;

            return (
              <div
                key={metric.name}
                className="p-4 rounded-lg bg-dark-800/40 border border-dark-700/50"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-dark-200">
                    {metric.name}
                  </span>
                  <span
                    className={`text-xs font-mono font-bold ${
                      change > 0 ? 'text-forge-400' : 'text-red-400'
                    }`}
                  >
                    {change > 0 ? '+' : ''}
                    {change}
                  </span>
                </div>

                {/* Current value */}
                <p className="text-2xl font-bold font-mono text-dark-50 mb-2">
                  {lastVal}
                </p>

                {/* Sparkline */}
                <div className="h-12">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={metric.data}>
                      <Tooltip content={<SparklineTooltip />} />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#22c55e"
                        strokeWidth={1.5}
                        dot={false}
                        activeDot={{
                          r: 3,
                          fill: '#22c55e',
                          stroke: '#020617',
                          strokeWidth: 1,
                        }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="flex justify-between mt-1 text-[9px] text-dark-600">
                  <span>W1</span>
                  <span>W8</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
