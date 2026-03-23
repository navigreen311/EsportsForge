/**
 * Glass-morphism card component with dark background and subtle border.
 */

"use client";

import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  onClick?: () => void;
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

export function Card({
  children,
  className,
  padding = 'md',
  hover = false,
  onClick,
}: CardProps) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'rounded-xl border border-dark-700/50 bg-dark-900/80 backdrop-blur-sm',
        paddingStyles[padding],
        hover && 'cursor-pointer transition-all duration-200 hover:border-forge-500/30 hover:bg-dark-800/80',
        onClick && 'cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  );
}
