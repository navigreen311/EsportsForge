'use client';

import { AgentAccuracyEntry } from '@/types/analytics';
import { TrendingUp, TrendingDown, Minus, Bot } from 'lucide-react';

interface AgentAccuracyProps {
  agents: AgentAccuracyEntry[];
}

const trendIcons = {
  up: <TrendingUp className="w-4 h-4 text-forge-400" />,
  down: <TrendingDown className="w-4 h-4 text-red-400" />,
  stable: <Minus className="w-4 h-4 text-dark-400" />,
};

function getAccuracyColor(accuracy: number): string {
  if (accuracy >= 85) return 'bg-forge-500';
  if (accuracy >= 70) return 'bg-yellow-500';
  return 'bg-red-500';
}

export default function AgentAccuracy({ agents }: AgentAccuracyProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center gap-3 mb-5">
        <Bot className="w-5 h-5 text-forge-400" />
        <div>
          <h2 className="text-lg font-bold text-dark-100">Agent Accuracy</h2>
          <p className="text-sm text-dark-400">Truth Engine validation</p>
        </div>
      </div>

      <div className="space-y-4">
        {agents.map((agent) => (
          <div key={agent.agentName} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-dark-100">{agent.agentName}</span>
                {trendIcons[agent.trend]}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-dark-500">
                  {agent.predictionsCorrect}/{agent.predictionsTotal}
                </span>
                <span className="text-sm font-bold font-mono text-dark-100">
                  {agent.accuracy}%
                </span>
              </div>
            </div>
            <div className="w-full bg-dark-800 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full transition-all duration-500 ${getAccuracyColor(agent.accuracy)}`}
                style={{ width: `${agent.accuracy}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
