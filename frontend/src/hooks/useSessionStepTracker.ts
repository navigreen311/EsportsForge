/**
 * Auto-marks session steps as the player navigates between routes during
 * an active session. Used by the dashboard layout so the step flow stays
 * in sync without each page having to opt in.
 */

'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useSessionStore } from '@/lib/sessionStore';

const ROUTE_TO_STEP: Array<[RegExp, 'warRoom' | 'gameplan']> = [
  [/^\/war-room(\/|$)/, 'warRoom'],
  [/^\/gameplan(\/|$)/, 'gameplan'],
];

export function useSessionStepTracker() {
  const pathname = usePathname();
  const session = useSessionStore((s) => s.session);
  const markStep = useSessionStore((s) => s.markStep);

  useEffect(() => {
    if (!session || !pathname) return;
    for (const [pattern, step] of ROUTE_TO_STEP) {
      if (pattern.test(pathname) && !session.steps[step]) {
        markStep(step, true);
        return;
      }
    }
  }, [pathname, session, markStep]);
}
