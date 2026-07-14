/** @jest-environment jsdom */
import { act, renderHook } from '@testing-library/react';

import {
  deriveCoverageHighlight,
  playBeatsCoverage,
  type HighlightablePlay,
} from '../coverageHighlight';
import { useVisionEvents, type EventEnvelope } from '@/hooks/useVisionEvents';

// A COVERAGE_LOCKED envelope carrying the v0.3 `defensive_coverage` field (the
// canonical coverage the classifier emits, e.g. "Cover 3" / "Cover 2-Man").
function coverageEvent(coverage: string | null = 'Cover 3'): EventEnvelope {
  return {
    event_id: 'evt-cov-1',
    session_id: 'sess-1',
    title: 'madden26',
    event_type: 'COVERAGE_LOCKED',
    confidence: 0.9,
    timestamp: '2026-07-14T00:00:00Z',
    captured_at: '2026-07-14T00:00:00Z',
    payload: {
      offensive_formation: null,
      offensive_formation_family: null,
      defensive_coverage: coverage,
    },
  };
}

// Mirrors the real kill-sheet `beats` vocabulary (useGameplan mockPlays).
const PLAYS: HighlightablePlay[] = [
  { id: 'play-1', beats: 'Cover 3' },
  { id: 'play-2', beats: 'Nickel/Dime Packages' },
  { id: 'play-3', beats: 'Man Coverage' },
  { id: 'play-4', beats: 'Cover 2' },
  { id: 'play-6', beats: 'Cover 3' },
  { id: 'play-7', beats: 'Man Blitz' },
  { id: 'play-8', beats: 'Cover 3 / Cover 4' },
  { id: 'play-10', beats: 'Cover 2 Zone' },
  { id: 'play-x', beats: undefined }, // no beats — never matches
];

function ids(cov: string | null): string[] | null {
  return deriveCoverageHighlight(coverageEvent(cov), PLAYS)?.playIds ?? null;
}

// ---------------------------------------------------------------------------
// The pure matcher.
// ---------------------------------------------------------------------------

test('null lastEvent → null (no highlight)', () => {
  expect(deriveCoverageHighlight(null, PLAYS)).toBeNull();
});

test('empty / missing defensive_coverage → null', () => {
  expect(deriveCoverageHighlight(coverageEvent(null), PLAYS)).toBeNull();
  expect(deriveCoverageHighlight(coverageEvent(''), PLAYS)).toBeNull();
});

test('Cover 3 → the three plays whose beats name Cover 3', () => {
  const h = deriveCoverageHighlight(coverageEvent('Cover 3'), PLAYS);
  expect(h).toEqual({ coverage: 'Cover 3', playIds: ['play-1', 'play-6', 'play-8'] });
});

test('Cover 2 → shell match on "Cover 2" and "Cover 2 Zone"', () => {
  expect(ids('Cover 2')).toEqual(['play-4', 'play-10']);
});

test('Cover 4 → the combined "Cover 3 / Cover 4" play', () => {
  expect(ids('Cover 4')).toEqual(['play-8']);
});

test('Cover 2-Man → the Cover-2 shell AND the generic Man beaters', () => {
  // shell 2 (play-4, play-10) + man rule (play-3, play-7), in list order.
  expect(ids('Cover 2-Man')).toEqual(['play-3', 'play-4', 'play-7', 'play-10']);
});

test('Cover 0 (man-based) → only the Man beaters', () => {
  expect(ids('Cover 0')).toEqual(['play-3', 'play-7']);
});

test('Cover 6 (no counter-play in the sheet) → null, not an empty highlight', () => {
  expect(deriveCoverageHighlight(coverageEvent('Cover 6'), PLAYS)).toBeNull();
});

test('playBeatsCoverage: word-bounded shell match ("Cover 2" ≠ "Cover 20")', () => {
  expect(playBeatsCoverage('Cover 2 Zone', 'Cover 2')).toBe(true);
  expect(playBeatsCoverage('Cover 20 Prevent', 'Cover 2')).toBe(false);
  expect(playBeatsCoverage('Man Coverage', 'Cover 1')).toBe(true); // Cover 1 is man-based
  expect(playBeatsCoverage('Cover 3', 'Cover 2')).toBe(false);
});

// ---------------------------------------------------------------------------
// Subscription → seam. A live COVERAGE_LOCKED now yields a real highlight.
// Reuses the FakeWebSocket pattern from useVisionEvents.test.ts.
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

test('a surfaced COVERAGE_LOCKED yields a real highlight', () => {
  const { result } = renderHook(() => {
    const { lastEvent } = useVisionEvents(OPTS);
    return { lastEvent, highlight: deriveCoverageHighlight(lastEvent, PLAYS) };
  });
  const ws = FakeWebSocket.instances[0]!;
  act(() => ws.emitOpen());

  expect(result.current.lastEvent).toBeNull();
  expect(result.current.highlight).toBeNull();

  act(() => ws.emitMessage(coverageEvent('Cover 3')));
  expect(result.current.lastEvent!.event_type).toBe('COVERAGE_LOCKED');
  expect(result.current.highlight).toEqual({
    coverage: 'Cover 3',
    playIds: ['play-1', 'play-6', 'play-8'],
  });
});

test('non-coverage events are filtered out (FORMATION_LOCKED ignored)', () => {
  const { result } = renderHook(() => {
    const { lastEvent } = useVisionEvents(OPTS);
    return { lastEvent, highlight: deriveCoverageHighlight(lastEvent, PLAYS) };
  });
  const ws = FakeWebSocket.instances[0]!;
  act(() => ws.emitOpen());
  act(() =>
    ws.emitMessage({
      ...coverageEvent('Cover 3'),
      event_id: 'evt-form-1',
      event_type: 'FORMATION_LOCKED',
    }),
  );
  expect(result.current.lastEvent).toBeNull();
  expect(result.current.highlight).toBeNull();
});
