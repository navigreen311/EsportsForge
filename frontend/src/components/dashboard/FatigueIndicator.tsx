/**
 * Predictive Fatigue Indicator — session health bar with peak window.
 */

'use client';

import { Clock, Battery, BatteryCharging, BatteryLow } from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';
import type { FatigueIndicator as FatigueData } from '@/types/dashboard';

const statusConfig = {
  fresh: { label: 'Fresh', color: 'text-forge-400', bar: 'bg-forge-500', icon: BatteryCharging },
  peak: { label: 'Peak', color: 'text-forge-400', bar: 'bg-forge-500', icon: Battery },
  fading: { label: 'Fading', color: 'text-amber-400', bar: 'bg-amber-500', icon: Battery },
  fatigued: { label: 'Fatigued', color: 'text-red-400', bar: 'bg-red-500', icon: BatteryLow },
} as const;

interface FatigueIndicatorProps {
  data: FatigueData;
}

export default function FatigueIndicatorCard({ data }: FatigueIndicatorProps) {
  const config = statusConfig[data.status];
  const StatusIcon = config.icon;
  const hasSession = data.currentSessionMinutes !== null;
  const progress = hasSession
    ? Math.min(100, (data.currentSessionMinutes! / data.peakWindowMinutes) * 100)
    : 0;

  return (
    <Card padding="sm">
      <div className="flex items-center gap-4">
        <div className={clsx('flex h-9 w-9 items-center justify-center rounded-lg bg-dark-800')}>
          <StatusIcon className={clsx('h-5 w-5', config.color)} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-xs font-medium text-dark-300">Session Health</span>
            <span className={clsx('text-xs font-bold', config.color)}>
              {config.label}
            </span>
          </div>

          <div className="h-1.5 w-full overflow-hidden rounded-full bg-dark-800">
            <div
              className={clsx('h-full rounded-full transition-all duration-500', config.bar)}
              style={{ width: hasSession ? `${progress}%` : '0%' }}
            />
          </div>

          <div className="mt-1 flex items-center justify-between text-[10px] text-dark-500">
            {hasSession ? (
              <>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {data.currentSessionMinutes} min elapsed
                </span>
                <span>Peak window: {data.peakWindowMinutes} min</span>
              </>
            ) : (
              <span>Start a session to track fatigue &bull; Peak window: {data.peakWindowMinutes} min</span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
