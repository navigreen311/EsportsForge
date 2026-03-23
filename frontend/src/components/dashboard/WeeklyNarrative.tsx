/**
 * Weekly growth narrative card with milestone badges and full-report link.
 */

'use client';

import { BookOpen, CheckCircle2, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Card } from '@/components/shared/Card';
import type { WeeklyNarrativeData } from '@/types/dashboard';

interface WeeklyNarrativeProps {
  narrative: WeeklyNarrativeData;
}

export default function WeeklyNarrative({ narrative }: WeeklyNarrativeProps) {
  return (
    <Card padding="lg">
      <div className="mb-4 flex items-center gap-2">
        <BookOpen className="h-5 w-5 text-forge-400" />
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-dark-300">
            Weekly Narrative
          </h3>
          <p className="text-[10px] text-dark-500">{narrative.weekLabel}</p>
        </div>
      </div>

      {/* Narrative body */}
      <p className="mb-5 text-sm leading-relaxed text-dark-300">
        {narrative.narrative}
      </p>

      {/* Milestones */}
      <div className="mb-5 flex flex-wrap gap-2">
        {narrative.milestones.map((ms) => (
          <span
            key={ms.label}
            className="inline-flex items-center gap-1.5 rounded-full border border-forge-500/30 bg-forge-500/10 px-2.5 py-1 text-xs font-medium text-forge-400"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            {ms.label}
          </span>
        ))}
      </div>

      {/* Link */}
      <Link
        href="/analytics"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-forge-400 transition-colors hover:text-forge-300"
      >
        View Full Report
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </Card>
  );
}
