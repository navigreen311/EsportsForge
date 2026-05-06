/**
 * ProofAI Panel — Evidence cards with sample size, confidence, and verification status.
 * Shows data-backed proof for AI recommendations.
 *
 * Each card is clickable and expands to show WHY/DATA/RISK rationale,
 * mirroring the "Why?" toggle pattern from RecentRecommendations.
 *
 * TODO: Wire WHY/DATA/RISK to real ConfidenceAI output instead of static mock fields.
 */

'use client';

import { useState } from 'react';
import {
  ShieldCheck,
  Database,
  CheckCircle2,
  ChevronDown,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';

interface EvidenceCard {
  id: string;
  statement: string;
  confidence: number;
  verified: string;
  icon: 'database' | 'check';
  why: string;
  data: string;
  risk: string;
}

const mockEvidence: EvidenceCard[] = [
  {
    id: 'ev-1',
    statement: 'Based on 14 games vs zone',
    confidence: 87,
    verified: 'Verified 2 games ago',
    icon: 'database',
    why: 'Pattern is consistent across recent games vs zone defenses.',
    data: '14 games sampled, last 21 days. 87% confidence interval.',
    risk: 'Low — high sample size, recent and stable trend.',
  },
  {
    id: 'ev-2',
    statement: 'Pressure timing drops 23% after 60min',
    confidence: 79,
    verified: 'Verified last session',
    icon: 'database',
    why: 'Decision latency increases measurably late in long sessions.',
    data: 'Compared first 30min vs final 30min across 11 multi-hour sessions.',
    risk: 'Medium — true effect, but some variance from opponent strength.',
  },
  {
    id: 'ev-3',
    statement: 'Red zone efficiency peaks with PA concepts',
    confidence: 91,
    verified: 'Verified 1 game ago',
    icon: 'check',
    why: 'Play-action concepts consistently outperform straight drop-back inside the 20.',
    data: '23 red zone snaps with PA vs 31 without; +18% TD rate.',
    risk: 'Low — recent, repeatable, and effect size is large.',
  },
];

function getConfidenceColor(confidence: number) {
  if (confidence >= 85) return 'text-forge-400 bg-forge-500/10 border-forge-500/30';
  if (confidence >= 70) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
  return 'text-dark-400 bg-dark-700 border-dark-600';
}

export default function ProofAIPanel() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <Card padding="md">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>
          <div>
            <span className="text-sm font-bold text-dark-100">ProofAI Evidence</span>
            <p className="text-[10px] text-dark-500">Data-verified insights</p>
          </div>
        </div>

        {/* Evidence cards */}
        <div className="space-y-2">
          {mockEvidence.map((ev) => {
            const confColor = getConfidenceColor(ev.confidence);
            const isExpanded = expandedId === ev.id;
            return (
              <div key={ev.id}>
                <button
                  type="button"
                  onClick={() => setExpandedId(isExpanded ? null : ev.id)}
                  aria-expanded={isExpanded}
                  aria-controls={`proof-${ev.id}`}
                  className="flex w-full items-center gap-3 rounded-lg border border-dark-700/50 bg-dark-800/40 px-3 py-2.5 text-left transition-colors hover:border-dark-600 hover:bg-dark-800/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-500/40"
                >
                  <div className="flex h-7 w-7 items-center justify-center rounded-md bg-dark-700/50">
                    {ev.icon === 'database' ? (
                      <Database className="h-3.5 w-3.5 text-dark-400" />
                    ) : (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-dark-200">{ev.statement}</p>
                    <p className="text-[10px] text-dark-500">{ev.verified}</p>
                  </div>
                  <span
                    className={`rounded-md border px-2 py-0.5 text-[11px] font-bold tabular-nums ${confColor}`}
                  >
                    {ev.confidence}%
                  </span>
                  <ChevronDown
                    className={clsx(
                      'h-3.5 w-3.5 flex-shrink-0 text-dark-500 transition-transform',
                      isExpanded && 'rotate-180'
                    )}
                  />
                </button>

                {isExpanded && (
                  <div
                    id={`proof-${ev.id}`}
                    className="mt-2 space-y-1.5 rounded-lg border border-dark-700/50 bg-dark-800/50 px-3 py-2"
                  >
                    <div className="flex items-start gap-1.5">
                      <FileText className="mt-0.5 h-3 w-3 flex-shrink-0 text-dark-500" />
                      <p className="text-[11px] text-dark-300">
                        <span className="font-medium text-dark-200">WHY:</span>{' '}
                        {ev.why}
                      </p>
                    </div>
                    <div className="flex items-start gap-1.5">
                      <Database className="mt-0.5 h-3 w-3 flex-shrink-0 text-dark-500" />
                      <p className="text-[11px] text-dark-300">
                        <span className="font-medium text-dark-200">DATA:</span>{' '}
                        {ev.data}
                      </p>
                    </div>
                    <div className="flex items-start gap-1.5">
                      <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0 text-amber-500" />
                      <p className="text-[11px] text-dark-300">
                        <span className="font-medium text-amber-400">RISK:</span>{' '}
                        {ev.risk}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
