/** @jest-environment jsdom */
import { act, renderHook } from '@testing-library/react';

import { deriveCoverageHighlight } from '../coverageHighlight';
import { useVisionEvents, type EventEnvelope } from '@/hooks/useVisionEvents';

// Synthetic COVERAGE_LOCKED envelope — INJECTED, because the Madden adapter
// emits no coverage in v0.1 (soft-launch, ADR 0010 §45). There is no live clip
// that produces this; the synthetic event + graceful-empty ARE the proof.
// Live verification is deferred to v0.3.
function coverageEvent(overrides: Partial<EventEnvelope> = {}): EventEnvelope {
  return {
    event_id: 'evt-cov-1',
    session_id: 'sess-1',
    title: 'madden26',
    event_type: 'COVERAGE_LOCKED',
    confidence: 0.9,
    timestamp: '2026-07-03T00:00:00Z',
    captured_at: '2026-07-03T00:00:00Z',
    // defensive_formation is the only defensive field today, null-until-v0.3;
    // supplied here purely to exercise the seam with a realistic shape.
    payload: {
      offensive_formation: null,
      offensive_formation_family: null,
      defensive_formation: 'Cover 3',
    },
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// The v0.3 seam — pure. v0.1 always returns null (silence by design).
// ---------------------------------------------------------------------------

test('graceful-empty: null lastEvent → null (no highlight)', () => {
  expect(deriveCoverageHighlight(null)).toBeNull();
});

test('v0.1 soft-launch: a synthetic COVERAGE_LOCKED is inert → null (seam invoked)', () => {
  expect(deriveCoverageHighlight(coverageEvent())).toBeNull();
});

// ---------------------------------------------------------------------------
// Subscription surfaces COVERAGE_LOCKED → seam invoked. Reuses the FakeWebSocket
// pattern from useVisionEvents.test.ts to drive the real hook.
// ---------------------------------------------------------------------------

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  url: string;
  readyState = 0;
  onopen: ((e?: unknown) => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onerror: ((e?: unknown) => void) | null = null;
  onclose: ((e?: unknown) => void) | null = null;
  close = jest.fn(() => {
    this.readyState = 3;
    this.onclose?.({});
  });

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  emitOpen() {
    this.readyState = 1;
    this.onopen?.({});
  }
  emitMessage(obj: unknown) {
    this.onmessage?.({ data: JSON.stringify(obj) });
  }
}

beforeEach(() => {
  FakeWebSocket.instances = [];
  (global as unknown as { WebSocket: unknown }).WebSocket = FakeWebSocket;
  process.env.NEXT_PUBLIC_VAF_WS_URL = 'ws://test-core:8100';
});

const OPTS = { sessionId: 'sess-1', token: 'browser-tok', eventType: 'COVERAGE_LOCKED' };

test('subscription surfaces a COVERAGE_LOCKED and the seam stays inert (v0.1)', () => {
  const { result } = renderHook(() => {
    const { lastEvent } = useVisionEvents(OPTS);
    return { lastEvent, highlight: deriveCoverageHighlight(lastEvent) };
  });
  const ws = FakeWebSocket.instances[0]!;
  act(() => ws.emitOpen());

  // Nothing surfaced yet → graceful empty.
  expect(result.current.lastEvent).toBeNull();
  expect(result.current.highlight).toBeNull();

  // Inject a COVERAGE_LOCKED — the subscription surfaces it (filter matches)...
  act(() => ws.emitMessage(coverageEvent()));
  expect(result.current.lastEvent).not.toBeNull();
  expect(result.current.lastEvent!.event_type).toBe('COVERAGE_LOCKED');
  // ...and the seam is invoked but inert in v0.1 (no highlight until v0.3).
  expect(result.current.highlight).toBeNull();
});

test('non-coverage events are filtered out (FORMATION_LOCKED ignored)', () => {
  const { result } = renderHook(() => {
    const { lastEvent } = useVisionEvents(OPTS);
    return { lastEvent, highlight: deriveCoverageHighlight(lastEvent) };
  });
  const ws = FakeWebSocket.instances[0]!;
  act(() => ws.emitOpen());
  act(() =>
    ws.emitMessage({
      ...coverageEvent(),
      event_id: 'evt-form-1',
      event_type: 'FORMATION_LOCKED',
    }),
  );
  // Filtered by the COVERAGE_LOCKED subscription → still empty.
  expect(result.current.lastEvent).toBeNull();
  expect(result.current.highlight).toBeNull();
});
