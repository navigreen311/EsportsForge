/**
 * useVisionEvents — Phase 1a Day 2.
 *
 * Frontend consumer of the VAF core WS event surface (Day 1,
 * `services/visionaudioforge/app/api/events.py`, `/ws/events/{session_id}`).
 * Opens a WebSocket, receives the `EventEnvelope` stream, and surfaces the
 * latest event matching a predicate (default `FORMATION_LOCKED`) for Drill
 * Lab to display.
 *
 * Event-display-only: envelopes are surfaced as-is; no coaching analysis
 * (the coaching engine is Phase 1b). Counting-agnostic: rep-counting is
 * Day-3 page logic. Written for the ADR 0015 sampled cadence — formation
 * fires once per play-call screen; there are NO per-frame assumptions here.
 *
 * Auth: the Day-1 surface accepts a `?token=` query param for browsers
 * (which cannot set WS headers). `token` + `sessionId` are caller-provided
 * (Day-3 page wires their source). Base URL from NEXT_PUBLIC_VAF_WS_URL.
 */
import { useEffect, useRef, useState } from 'react';

// Minimal mirror of the VAF core EventEnvelope
// (services/visionaudioforge/app/schemas/events.py). No shared frontend type
// existed; kept minimal + event-display-only. `payload` carries more fields
// on the wire; Drill Lab display only needs the formation.
export interface FootballPayload {
  offensive_formation: string | null;
  offensive_formation_family: string | null;
  // v0.3 COVERAGE_LOCKED — the committed defensive coverage, canonical name
  // (e.g. "Cover 3", "Cover 2-Man"). Null on non-coverage events; optional so
  // existing partial payload literals (tests) don't need updating — the matcher
  // treats absent as no-coverage.
  defensive_coverage?: string | null;
  // Situational fields carried on the payload (best-effort — the fixed-bbox HUD is
  // matchup-calibrated, so these can be null off the calibrated matchup, PR #135).
  // Optional so existing partial payload literals don't need updating.
  down?: number | null;
  distance?: number | null;
  [key: string]: unknown;
}

export interface EventEnvelope {
  event_id: string;
  session_id: string;
  title: string;
  event_type: string; // "FORMATION_LOCKED" | "SNAPSHOT" | ...
  confidence: number;
  timestamp: string;
  captured_at: string;
  payload: FootballPayload;
}

export interface UseVisionEventsOptions {
  sessionId: string | null | undefined;
  token: string | null | undefined;
  /**
   * WS base URL (e.g. `ws://127.0.0.1:8100`). The broker (`/sessions/start`)
   * returns this as `ws_url`; the Day-3 page threads it through so the socket
   * self-configures. Falls back to NEXT_PUBLIC_VAF_WS_URL when not supplied.
   */
  wsUrl?: string | null;
  /** Event type to surface. Day 1 streams all events; the client filters. */
  eventType?: string;
  enabled?: boolean;
}

export interface UseVisionEventsResult {
  lastEvent: EventEnvelope | null;
  connected: boolean;
  error: Error | null;
}

const RECONNECT_BASE_MS = 500;
const RECONNECT_MAX_MS = 10_000;

export function useVisionEvents({
  sessionId,
  token,
  wsUrl,
  eventType = 'FORMATION_LOCKED',
  enabled = true,
}: UseVisionEventsOptions): UseVisionEventsResult {
  const [lastEvent, setLastEvent] = useState<EventEnvelope | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    if (!enabled || !sessionId || !token) {
      return;
    }

    const base = wsUrl ?? process.env.NEXT_PUBLIC_VAF_WS_URL ?? '';
    const url =
      `${base}/ws/events/${encodeURIComponent(sessionId)}` +
      `?token=${encodeURIComponent(token)}`;
    let closedByCleanup = false;

    const scheduleReconnect = () => {
      if (!mountedRef.current || closedByCleanup) return;
      const delay = Math.min(RECONNECT_BASE_MS * 2 ** attemptRef.current, RECONNECT_MAX_MS);
      attemptRef.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    function connect() {
      if (!mountedRef.current || closedByCleanup) return;
      let ws: WebSocket;
      try {
        ws = new WebSocket(url);
      } catch (e) {
        if (mountedRef.current) setError(e as Error);
        scheduleReconnect();
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        attemptRef.current = 0;
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (evt: MessageEvent) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(evt.data as string) as EventEnvelope;
          if (data && data.event_type === eventType) {
            setLastEvent(data);
          }
        } catch {
          // Ignore malformed frames — event display is best-effort.
        }
      };

      ws.onerror = () => {
        if (!mountedRef.current) return;
        setError(new Error('WebSocket error'));
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setConnected(false);
        if (!closedByCleanup) scheduleReconnect();
      };
    }

    connect();

    return () => {
      mountedRef.current = false;
      closedByCleanup = true;
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      const ws = wsRef.current;
      if (ws) {
        ws.onopen = null;
        ws.onmessage = null;
        ws.onerror = null;
        ws.onclose = null;
        try {
          ws.close();
        } catch {
          /* noop */
        }
      }
      wsRef.current = null;
    };
  }, [sessionId, token, wsUrl, eventType, enabled]);

  return { lastEvent, connected, error };
}
