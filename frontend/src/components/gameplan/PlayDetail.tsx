'use client';

import { Target, Lightbulb, Zap } from 'lucide-react';
import { Badge } from '@/components/shared/Badge';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
import { Card } from '@/components/shared/Card';
import { ImpactScore } from '@/components/gameplan/ImpactScore';
import SimLabButton from '@/components/gameplan/SimLabButton';
import EvidencePanel from '@/components/gameplan/EvidencePanel';
import ThreeLayerAudible from '@/components/gameplan/ThreeLayerAudible';
import type { Play } from '@/types/gameplan';

interface PlayDetailProps {
  play: Play | null;
  opponentName?: string;
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

export default function PlayDetail({ play, opponentName = 'Opponent' }: PlayDetailProps) {
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
      {/* Header + 3. SimLab Button */}
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-dark-500">
          {play.formation}
        </p>
        <div className="mt-1 flex items-center gap-3">
          <h2 className="text-2xl font-bold text-dark-50">{play.name}</h2>
          <SimLabButton
            playId={play.id}
            playName={play.name}
            opponentName={opponentName}
          />
        </div>
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

      {/* Expected Success Rate + 6. ImpactRank Score */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-dark-200">
          Expected Success Rate
        </h3>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <ConfidenceBar
              value={play.confidenceScore}
              label="Confidence"
              size="lg"
              showValue
            />
          </div>
          <ImpactScore playId={play.id} layout="detail" />
        </div>
      </div>

      {/* 2. ProofAI Evidence Panel */}
      <EvidencePanel playId={play.id} />

      {/* 5. Three-Layer Call Structure (replaces flat audible list) */}
      {play.audibleOptions && play.audibleOptions.length > 0 && (
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
            Call Structure
          </h3>
          <ThreeLayerAudible
            playName={play.name}
            audibles={play.audibleOptions}
          />
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
