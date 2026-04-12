import type { ReactNode } from 'react';
import Link from 'next/link';

export default function EmptyState({ icon, title, description, actionLabel, actionHref }: {
  icon: ReactNode; title: string; description: string; actionLabel?: string; actionHref?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] px-4 text-center">
      <div className="mb-4 text-dark-500">{icon}</div>
      <h3 className="text-lg font-bold text-dark-100 mb-2">{title}</h3>
      <p className="text-dark-400 text-sm max-w-md mb-6">{description}</p>
      {actionLabel && actionHref && (
        <Link href={actionHref} className="rounded-lg bg-forge-600 px-4 py-2 text-sm font-medium text-white hover:bg-forge-500 transition-colors">
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
