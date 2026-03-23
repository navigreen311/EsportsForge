/**
 * Horizontal confidence bar 0-100% with color gradient (red -> yellow -> green).
 */

"use client";

import { clsx } from 'clsx';

interface ConfidenceBarProps {
  value: number; // 0-100
  label?: string;
  showValue?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

function getBarColor(value: number): string {
  if (value >= 75) return 'bg-forge-500';
  if (value >= 50) return 'bg-amber-500';
  if (value >= 25) return 'bg-orange-500';
  return 'bg-red-500';
}

function getTextColor(value: number): string {
  if (value >= 75) return 'text-forge-400';
  if (value >= 50) return 'text-amber-400';
  if (value >= 25) return 'text-orange-400';
  return 'text-red-400';
}

const heightStyles = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-3.5',
};

export function ConfidenceBar({
  value,
  label,
  showValue = true,
  size = 'md',
  className,
}: ConfidenceBarProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className={clsx('w-full', className)}>
      {(label || showValue) && (
        <div className="mb-1.5 flex items-center justify-between">
          {label && (
            <span className="text-xs font-medium text-dark-400">{label}</span>
          )}
          {showValue && (
            <span className={clsx('text-xs font-bold', getTextColor(clamped))}>
              {Math.round(clamped)}%
            </span>
          )}
        </div>
      )}
      <div
        className={clsx(
          'w-full overflow-hidden rounded-full bg-dark-800',
          heightStyles[size]
        )}
      >
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-500 ease-out',
            getBarColor(clamped)
          )}
          style={{ width: `${clamped}%` }}
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label}
        />
      </div>
    </div>
  );
}
