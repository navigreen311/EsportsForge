/**
 * ProgressionOS Install Roadmap — compact horizontal strip showing
 * current package progress and next package preview.
 */

'use client';

import { Package, Lock, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Card } from '@/components/shared/Card';
import type { ProgressionPackage } from '@/types/dashboard';

interface ProgressionStripProps {
  current: ProgressionPackage;
  next: ProgressionPackage;
}

export default function ProgressionStrip({ current, next }: ProgressionStripProps) {
  return (
    <Link href="/drills">
      <Card padding="sm" hover className="group">
        <div className="flex items-center gap-4">
          {/* Current package */}
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-forge-400" />
            <span className="text-[10px] font-medium uppercase tracking-wider text-dark-500">
              Installing
            </span>
          </div>

          <div className="min-w-0 flex-1">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-bold text-dark-100">
                {current.name}
              </span>
              <span className="text-xs font-bold tabular-nums text-forge-400">
                {current.percentComplete}%
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-dark-800">
              <div
                className="h-full rounded-full bg-forge-500 transition-all duration-500"
                style={{ width: `${current.percentComplete}%` }}
              />
            </div>
          </div>

          <ArrowRight className="h-4 w-4 text-dark-600" />

          {/* Next package (locked) */}
          <div className="flex items-center gap-2 opacity-50">
            <Lock className="h-3.5 w-3.5 text-dark-500" />
            <div>
              <span className="text-[10px] font-medium uppercase tracking-wider text-dark-600">
                Next
              </span>
              <p className="text-xs font-medium text-dark-400">{next.name}</p>
            </div>
          </div>
        </div>
      </Card>
    </Link>
  );
}
