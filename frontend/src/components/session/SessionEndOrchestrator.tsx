/**
 * Mounted once in the dashboard layout. Listens for cross-page "end
 * session requested" signals from useSessionUIStore and shows the
 * SessionSummaryModal so the End Session button on the global banner
 * works the same on every page.
 */

'use client';

import { useSessionUIStore } from '@/lib/sessionStore';
import { SessionSummaryModal } from './PostGameFlow';

export function SessionEndOrchestrator() {
  const endRequested = useSessionUIStore((s) => s.endRequested);
  const clearEnd = useSessionUIStore((s) => s.clearEnd);

  return <SessionSummaryModal open={endRequested} onClose={clearEnd} />;
}
