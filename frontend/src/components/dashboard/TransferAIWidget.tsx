/**
 * TransferAI Widget — Lab vs Live performance comparison with gap indicator bar.
 * Shows the gap between practice/lab performance and live match execution.
 */

'use client';

import { FlaskConical, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Card } from '@/components/shared/Card';

interface TransferAIWidgetProps {
  labScore?: number;
  liveScore?: number;
  focusArea?: string;
}

export default function TransferAIWidget({
  labScore = 82,
  liveScore = 61,
  focusArea = 'pressure',
}: TransferAIWidgetProps) {
  const gap = labScore - liveScore;
  const gapPercentage = (gap / labScore) * 100;

  return (
    <Card padding="md">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10">
              <FlaskConical className="h-4 w-4 text-cyan-400" />
            </div>
            <span className="text-sm font-bold text-dark-100">TransferAI</span>
          </div>
          <Link
            href="/drills?filter=pressure&focus=transfer-gap"
            className="inline-flex items-center gap-1 text-[11px] font-medium text-forge-400 hover:text-forge-300 transition-colors"
          >
            Close Gap
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Scores comparison */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className="text-[10px] font-medium uppercase tracking-wider text-dark-500">Lab</p>
              <p className="text-2xl font-black tabular-nums text-forge-400">{labScore}%</p>
            </div>
            <span className="text-dark-600 text-lg">vs</span>
            <div className="text-center">
              <p className="text-[10px] font-medium uppercase tracking-wider text-dark-500">Live</p>
              <p className="text-2xl font-black tabular-nums text-amber-400">{liveScore}%</p>
            </div>
          </div>
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-center">
            <p className="text-[10px] font-medium text-red-300">Gap</p>
            <p className="text-lg font-black tabular-nums text-red-400">{gap}pts</p>
          </div>
        </div>

        {/* Gap indicator bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] text-dark-500">
            <span>Transfer Efficiency</span>
            <span>{Math.round((liveScore / labScore) * 100)}%</span>
          </div>
          <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-dark-700">
            {/* Lab level (full bar background) */}
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-forge-500/30"
              style={{ width: `${labScore}%` }}
            />
            {/* Live level (solid portion) */}
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-forge-500 transition-all duration-500"
              style={{ width: `${liveScore}%` }}
            />
            {/* Gap zone indicator */}
            <div
              className="absolute inset-y-0 rounded-full bg-red-500/40 border-l-2 border-red-400/60"
              style={{ left: `${liveScore}%`, width: `${gap}%` }}
            />
          </div>
        </div>

        {/* Focus recommendation */}
        <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-3 py-2">
          <p className="text-[11px] text-cyan-300">
            <span className="font-bold">Gap: {gap}pts</span> — focus on {focusArea}
          </p>
        </div>
      </div>
    </Card>
  );
}
