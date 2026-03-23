/**
 * Status/tier badge component with multiple visual variants.
 */

"use client";

import { clsx } from 'clsx';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'tier' | 'neutral';
export type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-forge-500/20 text-forge-400 border-forge-500/30',
  warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  danger: 'bg-red-500/20 text-red-400 border-red-500/30',
  info: 'bg-sky-500/20 text-sky-400 border-sky-500/30',
  tier: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  neutral: 'bg-dark-700/50 text-dark-300 border-dark-600/50',
};

const dotColors: Record<BadgeVariant, string> = {
  success: 'bg-forge-400',
  warning: 'bg-amber-400',
  danger: 'bg-red-400',
  info: 'bg-sky-400',
  tier: 'bg-purple-400',
  neutral: 'bg-dark-400',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'text-xs px-1.5 py-0.5',
  md: 'text-xs px-2 py-1',
  lg: 'text-sm px-2.5 py-1',
};

export function Badge({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {dot && (
        <span
          className={clsx('h-1.5 w-1.5 rounded-full', dotColors[variant])}
        />
      )}
      {children}
    </span>
  );
}
