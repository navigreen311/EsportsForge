/**
 * Metric card with large value, label, trend indicator, and sparkline.
 */

"use client";

import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card } from './Card';

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: {
    direction: 'up' | 'down' | 'flat';
    value: string;
  };
  sparklineData?: number[];
  icon?: React.ReactNode;
  className?: string;
}

function MiniSparkline({ data }: { data: number[] }) {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const height = 24;
  const width = 64;
  const step = width / (data.length - 1);

  const points = data
    .map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * height;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-6 w-16"
      preserveAspectRatio="none"
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-forge-500"
      />
    </svg>
  );
}

export function StatCard({
  label,
  value,
  trend,
  sparklineData,
  icon,
  className,
}: StatCardProps) {
  const TrendIcon =
    trend?.direction === 'up'
      ? TrendingUp
      : trend?.direction === 'down'
        ? TrendingDown
        : Minus;

  const trendColor =
    trend?.direction === 'up'
      ? 'text-forge-400'
      : trend?.direction === 'down'
        ? 'text-red-400'
        : 'text-dark-400';

  return (
    <Card className={clsx('flex flex-col gap-2', className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-dark-400">
          {label}
        </span>
        {icon && (
          <div className="text-dark-500">{icon}</div>
        )}
      </div>

      <div className="flex items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-2xl font-bold text-dark-50">{value}</span>
          {trend && (
            <div className={clsx('flex items-center gap-1', trendColor)}>
              <TrendIcon className="h-3.5 w-3.5" />
              <span className="text-xs font-medium">{trend.value}</span>
            </div>
          )}
        </div>

        {sparklineData && sparklineData.length > 1 && (
          <MiniSparkline data={sparklineData} />
        )}
      </div>
    </Card>
  );
}
