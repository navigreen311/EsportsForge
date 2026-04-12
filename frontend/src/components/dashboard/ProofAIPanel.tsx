/**
 * ProofAI Panel — Evidence cards with sample size, confidence, and verification status.
 * Shows data-backed proof for AI recommendations.
 */

'use client';

import { ShieldCheck, Database, CheckCircle2 } from 'lucide-react';
import { Card } from '@/components/shared/Card';

interface EvidenceCard {
  id: string;
  statement: string;
  confidence: number;
  verified: string;
  icon: 'database' | 'check';
}

const mockEvidence: EvidenceCard[] = [
  {
    id: 'ev-1',
    statement: 'Based on 14 games vs zone',
    confidence: 87,
    verified: 'Verified 2 games ago',
    icon: 'database',
  },
  {
    id: 'ev-2',
    statement: 'Pressure timing drops 23% after 60min',
    confidence: 79,
    verified: 'Verified last session',
    icon: 'database',
  },
  {
    id: 'ev-3',
    statement: 'Red zone efficiency peaks with PA concepts',
    confidence: 91,
    verified: 'Verified 1 game ago',
    icon: 'check',
  },
];

function getConfidenceColor(confidence: number) {
  if (confidence >= 85) return 'text-forge-400 bg-forge-500/10 border-forge-500/30';
  if (confidence >= 70) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
  return 'text-dark-400 bg-dark-700 border-dark-600';
}

export default function ProofAIPanel() {
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
            return (
              <div
                key={ev.id}
                className="flex items-center gap-3 rounded-lg border border-dark-700/50 bg-dark-800/40 px-3 py-2.5"
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
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
