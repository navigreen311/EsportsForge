'use client';

import { Brain, Clock, Zap, Target, Shield, type LucideIcon } from 'lucide-react';
import type { BehavioralSignal } from '@/types/opponent';

interface BehavioralSignalFeedProps {
  signals: BehavioralSignal[];
}

const typeIcons: Record<BehavioralSignal['type'], LucideIcon> = {
  timeout: Clock,
  'pace-change': Zap,
  audible: Brain,
  'hot-route': Target,
  'formation-shift': Shield,
};

const frequencyDots: Record<BehavioralSignal['frequency'], number> = {
  rare: 1,
  occasional: 2,
  frequent: 3,
};

const frequencyToReliability: Record<BehavioralSignal['frequency'], number> = {
  rare: 45,
  occasional: 68,
  frequent: 89,
};

function formatTypeLabel(type: string): string {
  return type
    .replace(/-/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function reliabilityColor(score: number): string {
  if (score >= 80) return 'text-forge-400';
  if (score >= 60) return 'text-amber-400';
  return 'text-dark-400';
}

export default function BehavioralSignalFeed({ signals }: BehavioralSignalFeedProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-1">
          <Brain className="h-5 w-5 text-purple-400" />
          <h2 className="text-lg font-semibold text-white">Behavioral Signal Agent</h2>
        </div>
        <p className="text-sm text-dark-400">Non-gameplay pattern observations</p>
      </div>

      <div className="space-y-3">
        {signals.map((signal, idx) => {
          const Icon = typeIcons[signal.type];
          const filled = frequencyDots[signal.frequency];
          const reliability = frequencyToReliability[signal.frequency];

          return (
            <div
              key={`${signal.type}-${idx}`}
              className="p-3 rounded-lg bg-dark-800/50 border border-dark-700"
            >
              <div className="flex items-start gap-3">
                <Icon className="h-4 w-4 text-purple-400 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-sm font-medium text-white">
                      {formatTypeLabel(signal.type)}
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        {[1, 2, 3].map((dot) => (
                          <span
                            key={dot}
                            className={`h-1.5 w-1.5 rounded-full ${
                              dot <= filled ? 'bg-purple-400' : 'bg-dark-600'
                            }`}
                          />
                        ))}
                      </div>
                      <span className={`text-xs font-mono ${reliabilityColor(reliability)}`}>
                        {reliability}% reliability
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-dark-300 mb-1">{signal.description}</p>
                  <p className="text-xs text-dark-400">{signal.situation}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
