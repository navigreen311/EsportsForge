'use client';

import { Activity, Target, Lightbulb, Volume2, Zap } from 'lucide-react';
import { Badge } from '@/components/shared/Badge';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
import { Card } from '@/components/shared/Card';
import { ImpactScore } from '@/components/gameplan/ImpactScore';
import EvidencePanel from '@/components/gameplan/EvidencePanel';
import ThreeLayerAudible from '@/components/gameplan/ThreeLayerAudible';
import PlayerTwinBadge, { PLAY_EXECUTION_PCT } from '@/components/gameplan/PlayerTwinBadge';
import ProofAIEvidence from '@/components/gameplan/ProofAIEvidence';
import MetaExpiryWarning from '@/components/gameplan/MetaExpiryWarning';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import type { Play } from '@/types/gameplan';

interface PlayDetailProps {
  play: Play | null;
  opponentName?: string;
  onSimulate?: (play: Play) => void;
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

function speakPlay(play: Play) {
  const layer1 = play.callStructure?.layer1;
  const audible = play.callStructure?.layer2?.[0];
  const parts = [
    `${play.name} from ${play.formation}.`,
    play.whenToCall ? `Call when ${play.whenToCall}.` : '',
    layer1 ? `Layer 1: ${layer1.name}.` : '',
    audible ? `If bagged: ${audible.audible} when ${audible.trigger}.` : '',
    play.confidenceScore !== undefined ? `Confidence ${play.confidenceScore} percent.` : '',
    play.impactScore !== undefined ? `Win impact ${play.impactScore} out of 10.` : '',
  ].filter(Boolean).join(' ');
  VoiceForgeService.speak(parts, { interruptCurrent: true });
}

export default function PlayDetail({ play, opponentName = 'Opponent', onSimulate }: PlayDetailProps) {
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
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <h2 className="text-2xl font-bold text-dark-50">{play.name}</h2>
          {onSimulate && (
            <button
              type="button"
              onClick={() => onSimulate(play)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-dark-600 bg-dark-800/50 px-3 py-1.5 text-xs font-medium text-dark-200 transition-colors hover:border-forge-500/50 hover:bg-dark-800 hover:text-forge-400"
              title={`Ask AdaptAI what to do vs ${opponentName}'s tendency`}
            >
              <Activity className="h-3.5 w-3.5" /> Simulate
            </button>
          )}
          <a
            href={`/drills/simlab?play=${encodeURIComponent(play.id)}&opponent=${encodeURIComponent(opponentName)}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-forge-500/30 bg-forge-500/10 px-3 py-1.5 text-xs font-medium text-forge-400 transition-colors hover:bg-forge-500/20 hover:border-forge-500/50"
          >
            Test in SimLab
          </a>
          <button
            type="button"
            onClick={() => speakPlay(play)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-dark-600 bg-dark-800/50 px-3 py-1.5 text-xs font-medium text-dark-200 transition-colors hover:border-forge-500/50 hover:bg-dark-800 hover:text-forge-400"
            title="Read play details aloud via VoiceForge"
          >
            <Volume2 className="h-3.5 w-3.5" /> Read Play
          </button>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {play.isKillSheetPlay && (
            <Badge variant="success" size="sm" dot>
              Kill Sheet Play
            </Badge>
          )}
          {/* PlayerTwin Execution Badge */}
          {PLAY_EXECUTION_PCT[play.id] !== undefined && (
            <PlayerTwinBadge executionPct={PLAY_EXECUTION_PCT[play.id]} />
          )}
          {/* Meta Expiry Warning */}
          <MetaExpiryWarning playId={play.id} />
        </div>
      </div>

      {/* Concept Breakdown */}
      <div>
        <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
          <Zap className="h-4 w-4 text-forge-400" />
          Concept Breakdown
        </h3>
        <p className="text-sm leading-relaxed text-dark-300">
          {play.conceptBreakdown ?? play.description}
        </p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {(play.tags ?? play.conceptTags).map((tag) => (
            <Badge key={tag} variant="neutral" size="sm">
              {tag}
            </Badge>
          ))}
        </div>
      </div>

      {/* When to Call */}
      {(play.whenToCall || play.situationTags.length > 0) && (
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
            <Target className="h-4 w-4 text-amber-400" />
            When to Call
          </h3>
          {play.whenToCall ? (
            <p className="text-sm leading-relaxed text-dark-300">{play.whenToCall}</p>
          ) : (
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
          )}
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
      <EvidencePanel playId={play.id} evidence={play.evidence} />

      {/* ProofAI Statistical Evidence */}
      <ProofAIEvidence playId={play.id} liveConfidence={play.proofAIConfidence} />

      {/* 5. Three-Layer Call Structure */}
      {(play.callStructure || (play.audibleOptions && play.audibleOptions.length > 0)) && (
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
            Call Structure
          </h3>
          <ThreeLayerAudible
            playName={play.name}
            audibles={play.audibleOptions ?? []}
            callStructure={play.callStructure}
          />
        </div>
      )}

      {/* Meta status footer */}
      {(play.metaStatus || play.patchVersion) && (
        <div className="flex items-center justify-between rounded-lg border border-dark-700/50 bg-dark-800/40 px-3 py-2 text-xs">
          <span className="text-dark-400">
            Meta: <span className="font-semibold text-dark-200">{play.metaStatus ?? 'Unknown'}</span>
          </span>
          {play.patchVersion && (
            <span className="text-dark-500">Patch {play.patchVersion}</span>
          )}
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
