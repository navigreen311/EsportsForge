/**
 * Empty state component with icon, message, and optional action button.
 */

"use client";

import { clsx } from 'clsx';
import { Inbox } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center py-16 text-center',
        className
      )}
    >
      <div className="mb-4 rounded-xl bg-dark-800/50 p-4">
        <Icon className="h-10 w-10 text-dark-500" strokeWidth={1.5} />
      </div>
      <h3 className="mb-1 text-lg font-semibold text-dark-200">{title}</h3>
      {description && (
        <p className="mb-6 max-w-sm text-sm text-dark-400">{description}</p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="rounded-lg bg-forge-500 px-4 py-2 text-sm font-medium text-dark-950 transition-colors hover:bg-forge-400"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
