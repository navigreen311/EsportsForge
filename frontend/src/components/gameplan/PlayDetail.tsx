'use client';

import { Target, Lightbulb, GitBranch, Zap } from 'lucide-react';
import { Badge } from '@/components/shared/Badge';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
import { Card } from '@/components/shared/Card';
import type { Play } from '@/types/gameplan';

interface PlayDetailProps {
  play: Play | null;
}

const situationLabels: Record<string, string> = {
  'red-zone': 'Inside the 20',
  'goal-line': 'Goal line (1-3 yards)',
  '3rd-down': '3rd down conversions',
  '2-minute': '2-minute drill / hurry-up',
  'opening-drive': 'Opening drive / script',
  'anti-blitz': 'When opponent sends pressure',
  prevent: 'Prevent / clock kill',
  'hurry-up': 'No-huddle tempo',
};

export default function PlayDetail({ play }: PlayDetailProps) {
  if (!play) {
    return (
      <Card className="flex h-full items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Target className="mx-auto mb-3 h-10 w-10 text-dark-600" />
          <p className="text-dark-400 font-medium">Select a play</p>
          <p className="mt-1 text-sm text-dark-600">
            Click a play from the list to view its details
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card padding="lg" className="space-y-5">
      {/* Header */}
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-dark-500">
          {play.formation}
        </p>
        <h2 className="mt-1 text-2xl font-bold text-dark-50">{play.name}</h2>
        {play.isKillSheetPlay && (
          <Badge variant="success" size="sm" dot className="mt-2">
            Kill Sheet Play
          </Badge>
        )}
      </div>

      {/* Concept Breakdown */}
      <div>
        <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
          <Zap className="h-4 w-4 text-forge-400" />
          Concept Breakdown
        </h3>
        <p className="text-sm leading-relaxed text-dark-300">{play.description}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {play.conceptTags.map((tag) => (
            <Badge key={tag} variant="neutral" size="sm">
              {tag}
            </Badge>
          ))}
        </div>
      </div>

      {/* When to Call */}
      {play.situationTags.length > 0 && (
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
            <Target className="h-4 w-4 text-amber-400" />
            When to Call
          </h3>
          <ul className="space-y-1.5">
            {play.situationTags.map((tag) => (
              <li
                key={tag}
                className="flex items-center gap-2 text-sm text-dark-300"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-dark-500" />
                {situationLabels[tag] ?? tag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Expected Success Rate */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-dark-200">
          Expected Success Rate
        </h3>
        <ConfidenceBar
          value={play.confidenceScore}
          label="Confidence"
          size="lg"
          showValue
        />
      </div>

      {/* Audible Options */}
      {play.audibleOptions && play.audibleOptions.length > 0 && (
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
            <GitBranch className="h-4 w-4 text-sky-400" />
            Audible Options
          </h3>
          <div className="space-y-2">
            {play.audibleOptions.map((aud) => (
              <div
                key={aud.id}
                className="rounded-lg border border-dark-700/50 bg-dark-800/50 p-3"
              >
                <p className="text-sm font-medium text-dark-200">
                  {aud.label}
                </p>
                <p className="mt-0.5 text-xs text-amber-400/80">
                  Trigger: {aud.trigger}
                </p>
                <p className="mt-0.5 text-xs text-dark-400">
                  Audible to:{' '}
                  <span className="font-medium text-forge-400">
                    {aud.targetPlay}
                  </span>
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insight */}
      {play.beats && (
        <div className="rounded-lg border border-forge-800/30 bg-forge-950/20 p-3">
          <div className="flex items-start gap-2">
            <Lightbulb className="mt-0.5 h-4 w-4 flex-shrink-0 text-forge-400" />
            <p className="text-sm text-forge-300">
              This play beats{' '}
              <span className="font-semibold text-forge-400">{play.beats}</span>
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
