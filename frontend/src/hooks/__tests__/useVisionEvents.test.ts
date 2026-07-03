/** @jest-environment jsdom */
import { act, renderHook } from '@testing-library/react';

import { useVisionEvents, type EventEnvelope } from '../useVisionEvents';

// Real envelope shape captured from Day 1's integration test
// (FORMATION_LOCKED, formation 'Trips' / family 'shotgun_trips') — the hook is
// asserted against the actual wire shape, not an invented one.
const REAL_FORMATION_EVENT: EventEnvelope = {
  event_id: 'evt-formation-1',
  session_id: 'sess-1',
  title: 'madden26',
  event_type: 'FORMATION_LOCKED',
  confidence: 0.9,
  timestamp: '2026-07-03T00:00:00Z',
  captured_at: '2026-07-03T00:00:00Z',
  payload: { offensive_formation: 'Trips', offensive_formation_family: 'shotgun_trips' },
};

const SNAPSHOT_EVENT: EventEnvelope = {
  ...REAL_FORMATION_EVENT,
  event_id: 'evt-snapshot-1',
  event_type: 'SNAPSHOT',
};

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

  // test-only drivers
  emitOpen() {
    this.readyState = 1;
    this.onopen?.({});
  }
  emitMessage(obj: unknown) {
    this.onmessage?.({ data: JSON.stringify(obj) });
  }
  emitServerClose() {
    this.readyState = 3;
    this.onclose?.({});
  }
}

beforeEach(() => {
  FakeWebSocket.instances = [];
  (global as unknown as { WebSocket: unknown }).WebSocket = FakeWebSocket;
  process.env.NEXT_PUBLIC_VAF_WS_URL = 'ws://test-core:8100';
});

const OPTS = { sessionId: 'sess-1', token: 'browser-tok' };

test('connects when enabled with sessionId + token; URL carries ?token=', () => {
  renderHook(() => useVisionEvents(OPTS));
  expect(FakeWebSocket.instances).toHaveLength(1);
  expect(FakeWebSocket.instances[0].url).toBe(
    'ws://test-core:8100/ws/events/sess-1?token=browser-tok',
  );
});

test('does not connect when disabled or missing sessionId/token', () => {
  renderHook(() => useVisionEvents({ ...OPTS, enabled: false }));
  renderHook(() => useVisionEvents({ sessionId: null, token: 'x' }));
  renderHook(() => useVisionEvents({ sessionId: 'sess-1', token: null }));
  expect(FakeWebSocket.instances).toHaveLength(0);
});

test('filters: SNAPSHOT ignored, FORMATION_LOCKED surfaced (real shape)', () => {
  const { result } = renderHook(() => useVisionEvents(OPTS));
  const ws = FakeWebSocket.instances[0];
  act(() => ws.emitOpen());

  act(() => ws.emitMessage(SNAPSHOT_EVENT));
  expect(result.current.lastEvent).toBeNull();

  act(() => ws.emitMessage(REAL_FORMATION_EVENT));
  expect(result.current.lastEvent).not.toBeNull();
  expect(result.current.lastEvent!.event_type).toBe('FORMATION_LOCKED');
  expect(result.current.lastEvent!.payload.offensive_formation).toBe('Trips');
  expect(result.current.lastEvent!.payload.offensive_formation_family).toBe('shotgun_trips');
});

test('lastEvent tracks the latest matching event', () => {
  const { result } = renderHook(() => useVisionEvents(OPTS));
  const ws = FakeWebSocket.instances[0];
  act(() => ws.emitOpen());
  act(() =>
    ws.emitMessage({
      ...REAL_FORMATION_EVENT,
      payload: { offensive_formation: 'Bunch', offensive_formation_family: 'shotgun_bunch' },
    }),
  );
  act(() => ws.emitMessage(REAL_FORMATION_EVENT));
  expect(result.current.lastEvent!.payload.offensive_formation).toBe('Trips');
});

test('connected toggles on open/close', () => {
  jest.useFakeTimers();
  try {
    const { result } = renderHook(() => useVisionEvents(OPTS));
    const ws = FakeWebSocket.instances[0];
    act(() => ws.emitOpen());
    expect(result.current.connected).toBe(true);
    act(() => ws.emitServerClose());
    expect(result.current.connected).toBe(false);
  } finally {
    jest.useRealTimers();
  }
});

test('reconnects with backoff on unexpected close', () => {
  jest.useFakeTimers();
  try {
    renderHook(() => useVisionEvents(OPTS));
    const ws = FakeWebSocket.instances[0];
    act(() => ws.emitOpen());
    act(() => ws.emitServerClose());
    expect(FakeWebSocket.instances).toHaveLength(1);
    act(() => {
      jest.advanceTimersByTime(600); // > RECONNECT_BASE_MS (500)
    });
    expect(FakeWebSocket.instances).toHaveLength(2);
  } finally {
    jest.useRealTimers();
  }
});

test('cleanup on unmount closes socket and does not reconnect', () => {
  jest.useFakeTimers();
  try {
    const { unmount } = renderHook(() => useVisionEvents(OPTS));
    const ws = FakeWebSocket.instances[0];
    act(() => ws.emitOpen());
    unmount();
    expect(ws.close).toHaveBeenCalled();
    act(() => {
      jest.advanceTimersByTime(20000);
    });
    expect(FakeWebSocket.instances).toHaveLength(1); // no reconnect after unmount
  } finally {
    jest.useRealTimers();
  }
});
