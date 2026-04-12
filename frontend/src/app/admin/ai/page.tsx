/**
 * Admin AI Performance — Claude API usage, agent accuracy, cache hit rates.
 */

'use client';

import { Brain, Cpu, Zap, Database } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Mock data                                                          */
/* ------------------------------------------------------------------ */

const API_USAGE = {
  tokensToday:   '1.24M',
  tokensMonth:   '28.6M',
  costToday:     '$18.60',
  costMonth:     '$429.00',
  callsToday:    3_842,
  callsMonth:    87_210,
};

const CALLS_BY_AGENT = [
  { agent: 'ForgeCore',     calls: 12_400, tokens: '4.2M' },
  { agent: 'LoopAI',        calls: 9_800,  tokens: '3.8M' },
  { agent: 'TruthEngine',   calls: 8_100,  tokens: '5.1M' },
  { agent: 'ImpactRank',    calls: 6_700,  tokens: '2.9M' },
  { agent: 'TransferAI',    calls: 5_200,  tokens: '2.1M' },
  { agent: 'BenchmarkAI',   calls: 4_900,  tokens: '1.8M' },
  { agent: 'CalibrationAI', calls: 3_100,  tokens: '1.4M' },
];

interface AgentAccuracy {
  agent: string;
  accuracy: number;
  trend: 'up' | 'down' | 'stable';
}

const AGENT_ACCURACY: AgentAccuracy[] = [
  { agent: 'ForgeCore',     accuracy: 94.2, trend: 'up' },
  { agent: 'LoopAI',        accuracy: 91.8, trend: 'up' },
  { agent: 'TruthEngine',   accuracy: 96.1, trend: 'stable' },
  { agent: 'ImpactRank',    accuracy: 89.5, trend: 'down' },
  { agent: 'TransferAI',    accuracy: 87.3, trend: 'up' },
  { agent: 'BenchmarkAI',   accuracy: 92.0, trend: 'stable' },
  { agent: 'CalibrationAI', accuracy: 90.7, trend: 'up' },
];

const CACHE_HIT_RATE = 72.4;

const TREND_ICON: Record<string, { symbol: string; color: string }> = {
  up:     { symbol: '+', color: 'text-green-400' },
  down:   { symbol: '-', color: 'text-red-400' },
  stable: { symbol: '=', color: 'text-dark-400' },
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AdminAIPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Brain className="h-6 w-6 text-forge-400" />
        <h1 className="text-2xl font-bold text-dark-50">AI Performance</h1>
      </div>

      {/* API Usage Summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
          <div className="flex items-center gap-2 text-xs text-dark-400">
            <Zap className="h-4 w-4" />
            Tokens Today
          </div>
          <p className="mt-1 text-2xl font-bold text-dark-50">{API_USAGE.tokensToday}</p>
          <p className="mt-1 text-xs text-dark-400">Month total: {API_USAGE.tokensMonth}</p>
        </div>
        <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
          <div className="flex items-center gap-2 text-xs text-dark-400">
            <Cpu className="h-4 w-4" />
            Cost Today
          </div>
          <p className="mt-1 text-2xl font-bold text-dark-50">{API_USAGE.costToday}</p>
          <p className="mt-1 text-xs text-dark-400">Month total: {API_USAGE.costMonth}</p>
        </div>
        <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
          <div className="flex items-center gap-2 text-xs text-dark-400">
            <Database className="h-4 w-4" />
            Cache Hit Rate
          </div>
          <p className="mt-1 text-2xl font-bold text-dark-50">{CACHE_HIT_RATE}%</p>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-dark-700">
            <div
              className="h-full rounded-full bg-forge-400"
              style={{ width: `${CACHE_HIT_RATE}%` }}
            />
          </div>
        </div>
      </div>

      {/* Calls by Agent */}
      <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
        <h2 className="mb-4 text-sm font-semibold text-dark-100">Calls by Agent (this month)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
                <th className="px-4 py-3 font-medium">Agent</th>
                <th className="px-4 py-3 font-medium">Calls</th>
                <th className="px-4 py-3 font-medium">Tokens</th>
              </tr>
            </thead>
            <tbody>
              {CALLS_BY_AGENT.map((row) => (
                <tr
                  key={row.agent}
                  className="border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
                >
                  <td className="px-4 py-3 font-medium text-dark-100">{row.agent}</td>
                  <td className="px-4 py-3 text-dark-300">{row.calls.toLocaleString()}</td>
                  <td className="px-4 py-3 text-dark-300">{row.tokens}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Agent Accuracy */}
      <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
        <h2 className="mb-4 text-sm font-semibold text-dark-100">Agent Accuracy</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
                <th className="px-4 py-3 font-medium">Agent</th>
                <th className="px-4 py-3 font-medium">Accuracy</th>
                <th className="px-4 py-3 font-medium">Trend</th>
              </tr>
            </thead>
            <tbody>
              {AGENT_ACCURACY.map((row) => {
                const t = TREND_ICON[row.trend];
                return (
                  <tr
                    key={row.agent}
                    className="border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
                  >
                    <td className="px-4 py-3 font-medium text-dark-100">{row.agent}</td>
                    <td className="px-4 py-3 text-dark-100">{row.accuracy}%</td>
                    <td className={`px-4 py-3 font-medium ${t.color}`}>
                      {t.symbol} {row.trend}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
