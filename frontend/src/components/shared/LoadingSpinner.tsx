/**
 * Branded loading spinner with forge-green accent.
 */

"use client";

import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

const sizeStyles = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
};

export function LoadingSpinner({
  size = 'md',
  label,
  className,
}: LoadingSpinnerProps) {
  return (
    <div className={clsx('flex flex-col items-center gap-3', className)}>
      <div
        className={clsx(
          'animate-spin rounded-full border-forge-500 border-t-transparent',
          sizeStyles[size]
        )}
        role="status"
        aria-label={label ?? 'Loading'}
      />
      {label && (
        <p className="text-sm text-dark-400">{label}</p>
      )}
    </div>
  );
}
