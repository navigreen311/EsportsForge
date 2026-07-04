/** @jest-environment jsdom */
import { renderHook } from '@testing-library/react';

import { useSimLabAutoRep } from '../useSimLabAutoRep';
import type { EventEnvelope } from '../useVisionEvents';

// Real Day-1 envelope shape ('Trips' / 'shotgun_trips').
function formationEvent(overrides: Partial<EventEnvelope> = {}): EventEnvelope {
  return {
    event_id: 'evt-1',
    session_id: 'sess-1',
    title: 'madden26',
    event_type: 'FORMATION_LOCKED',
    confidence: 0.9,
    timestamp: '2026-07-03T00:00:00Z',
    captured_at: '2026-07-03T00:00:00Z',
    payload: { offensive_formation: 'Trips', offensive_formation_family: 'shotgun_trips' },
    ...overrides,
  };
}

test('one FORMATION_LOCKED → exactly one rep (real shape)', () => {
  const onRep = jest.fn();
  renderHook(({ lastEvent }) => useSimLabAutoRep({ lastEvent, onRep }), {
    initialProps: { lastEvent: formationEvent() as EventEnvelope | null },
  });
  expect(onRep).toHaveBeenCalledTimes(1);
  expect(onRep.mock.calls[0][0].payload.offensive_formation).toBe('Trips');
  expect(onRep.mock.calls[0][0].payload.offensive_formation_family).toBe('shotgun_trips');
});

test('does not double-count a re-surfaced event_id (dedupe, load-bearing)', () => {
  const onRep = jest.fn();
  const ev = formationEvent(); // event_id 'evt-1'
  const { rerender } = renderHook(({ lastEvent }) => useSimLabAutoRep({ lastEvent, onRep }), {
    initialProps: { lastEvent: ev as EventEnvelope | null },
  });
  // Same event_id re-delivered as a NEW object (React re-render / reconnect replay).
  rerender({ lastEvent: { ...ev } });
  rerender({ lastEvent: { ...ev } });
  expect(onRep).toHaveBeenCalledTimes(1); // exactly one rep for one event_id
});

test('two distinct event_ids → two reps', () => {
  const onRep = jest.fn();
  const { rerender } = renderHook(({ lastEvent }) => useSimLabAutoRep({ lastEvent, onRep }), {
    initialProps: { lastEvent: formationEvent({ event_id: 'evt-1' }) as EventEnvelope | null },
  });
  rerender({
    lastEvent: formationEvent({
      event_id: 'evt-2',
      payload: { offensive_formation: 'Bunch', offensive_formation_family: 'shotgun_bunch' },
    }),
  });
  expect(onRep).toHaveBeenCalledTimes(2);
});

test('null lastEvent → no auto-reps; then an event → one rep; unchanged → no more', () => {
  const onRep = jest.fn();
  const { rerender } = renderHook(({ lastEvent }) => useSimLabAutoRep({ lastEvent, onRep }), {
    initialProps: { lastEvent: null as EventEnvelope | null },
  });
  expect(onRep).not.toHaveBeenCalled();

  // A real event arrives → one rep.
  const ev = formationEvent();
  rerender({ lastEvent: ev });
  expect(onRep).toHaveBeenCalledTimes(1);

  // Unchanged (same object reference) → no additional rep.
  rerender({ lastEvent: ev });
  expect(onRep).toHaveBeenCalledTimes(1);
});

test('non-FORMATION_LOCKED is ignored (defensive)', () => {
  const onRep = jest.fn();
  renderHook(({ lastEvent }) => useSimLabAutoRep({ lastEvent, onRep }), {
    initialProps: {
      lastEvent: formationEvent({ event_type: 'SNAPSHOT', event_id: 'snap-1' }) as EventEnvelope | null,
    },
  });
  expect(onRep).not.toHaveBeenCalled();
});
