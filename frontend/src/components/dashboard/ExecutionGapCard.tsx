/**
 * TransferAI Lab-to-Live execution gap widget.
 * Shows the top skill gap between drills and ranked play.
 */

'use client';

import { ArrowRight, TrendingDown } from 'lucide-react';
import Link from 'next/link';
import { Card } from '@/components/shared/Card';
import type { ExecutionGap } from '@/types/dashboard';

interface ExecutionGapCardProps {
  gap: ExecutionGap;
}

export default function ExecutionGapCard({ gap }: ExecutionGapCardProps) {
  const delta = gap.drillRate - gap.rankedRate;

  return (
    <Card padding="md">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-500/10">
            <TrendingDown className="h-5 w-5 text-orange-400" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-medium uppercase tracking-wider text-dark-500">
              Execution Gap
            </p>
            <p className="text-sm font-bold text-dark-100">
              {gap.skill}:{' '}
              <span className="text-forge-400">{gap.drillRate}%</span>
              <span className="text-dark-500"> drills </span>
              <span className="text-dark-500">&rarr;</span>
              <span className="text-red-400"> {gap.rankedRate}%</span>
              <span className="text-dark-500"> ranked</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="rounded-md bg-red-500/10 px-2 py-0.5 text-xs font-bold text-red-400">
            &minus;{delta}%
          </span>
          <Link
            href={`/drills${gap.drillId ? `?focus=${gap.drillId}` : ''}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-forge-500 px-3 py-1.5 text-xs font-bold text-dark-950 transition-colors hover:bg-forge-400"
          >
            Drill This
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </div>
    </Card>
  );
}
