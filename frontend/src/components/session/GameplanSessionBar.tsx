/**
 * Compact session context bar shown on the Gameplan page when a session
 * is live. Smaller than the global ActiveSessionBanner — just enough to
 * orient the player to "this is your active gameplan."
 */

'use client';

import { useRouter } from 'next/navigation';
import { ArrowLeft, Target } from 'lucide-react';
import { useSessionStore, useElapsed } from '@/lib/sessionStore';

interface GameplanSessionBarProps {
  onOpenKillSheet: () => void;
}

export function GameplanSessionBar({ onOpenKillSheet }: GameplanSessionBarProps) {
  const session = useSessionStore((s) => s.session);
  const elapsed = useElapsed(session?.startTime ?? null);
  const router = useRouter();

  if (!session) return null;

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-forge-500/30 bg-forge-500/5 px-4 py-2.5">
      <span className="flex items-center gap-2 text-xs font-bold text-forge-300">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-forge-500" />
        </span>
        Session Active — {session.mode.toUpperCase()}
      </span>
      <span className="font-mono text-xs text-dark-200">{elapsed}</span>
      <span className="text-[11px] text-dark-400">
        This is your active gameplan{session.opponent ? ` vs ${session.opponent}` : ''}.
      </span>
      <div className="ml-auto flex items-center gap-2">
        <button
          type="button"
          onClick={() => router.push('/dashboard')}
          className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800/60 px-2.5 py-1 text-[11px] font-medium text-dark-300 transition-colors hover:bg-dark-700"
        >
          <ArrowLeft className="h-3 w-3" />
          Back to Dashboard
        </button>
        <button
          type="button"
          onClick={onOpenKillSheet}
          className="inline-flex items-center gap-1 rounded-md border border-forge-500/40 bg-forge-500/10 px-2.5 py-1 text-[11px] font-bold text-forge-300 transition-colors hover:bg-forge-500/20"
        >
          <Target className="h-3 w-3" />
          Open Kill Sheet
        </button>
      </div>
    </div>
  );
}
