/** @jest-environment jsdom */
import { renderHook } from '@testing-library/react';

import { useCoverageGameState } from '../useCoverageGameState';
import type { EventEnvelope } from '../useVisionEvents';

function coverageEvent(overrides: Partial<EventEnvelope> = {}): EventEnvelope {
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
      defensive_coverage: 'Cover 3',
      down: 3,
      distance: 8,
    },
    ...overrides,
  };
}

test('a COVERAGE_LOCKED → state + onCoverage once (with down/distance)', () => {
  const onCoverage = jest.fn();
  const { result } = renderHook(
    ({ lastEvent }) => useCoverageGameState({ lastEvent, onCoverage }),
    { initialProps: { lastEvent: coverageEvent() as EventEnvelope | null } },
  );
  expect(result.current).toEqual({
    coverage: 'Cover 3', down: 3, distance: 8, eventId: 'evt-cov-1',
  });
  expect(onCoverage).toHaveBeenCalledTimes(1);
  expect(onCoverage.mock.calls[0][0].coverage).toBe('Cover 3');
});

test('dedupe: a re-surfaced event_id does not re-fire onCoverage', () => {
  const onCoverage = jest.fn();
  const ev = coverageEvent();
  const { rerender } = renderHook(
    ({ lastEvent }) => useCoverageGameState({ lastEvent, onCoverage }),
    { initialProps: { lastEvent: ev as EventEnvelope | null } },
  );
  rerender({ lastEvent: { ...ev } }); // same event_id, new object
  rerender({ lastEvent: { ...ev } });
  expect(onCoverage).toHaveBeenCalledTimes(1);
});

test('two distinct event_ids → onCoverage twice; state tracks the latest', () => {
  const onCoverage = jest.fn();
  const { result, rerender } = renderHook(
    ({ lastEvent }) => useCoverageGameState({ lastEvent, onCoverage }),
    { initialProps: { lastEvent: coverageEvent() as EventEnvelope | null } },
  );
  rerender({
    lastEvent: coverageEvent({
      event_id: 'evt-cov-2',
      payload: {
        offensive_formation: null,
        offensive_formation_family: null,
        defensive_coverage: 'Cover 2-Man',
        down: 1,
        distance: 10,
      },
    }),
  });
  expect(onCoverage).toHaveBeenCalledTimes(2);
  expect(result.current.coverage).toBe('Cover 2-Man');
  expect(result.current.distance).toBe(10);
});

test('null lastEvent → empty state, no onCoverage', () => {
  const onCoverage = jest.fn();
  const { result } = renderHook(
    ({ lastEvent }) => useCoverageGameState({ lastEvent, onCoverage }),
    { initialProps: { lastEvent: null as EventEnvelope | null } },
  );
  expect(result.current.coverage).toBeNull();
  expect(onCoverage).not.toHaveBeenCalled();
});

test('a non-coverage event or a null-coverage payload is ignored', () => {
  const onCoverage = jest.fn();
  const { result, rerender } = renderHook(
    ({ lastEvent }) => useCoverageGameState({ lastEvent, onCoverage }),
    {
      initialProps: {
        lastEvent: coverageEvent({ event_type: 'FORMATION_LOCKED' }) as EventEnvelope | null,
      },
    },
  );
  expect(onCoverage).not.toHaveBeenCalled();
  rerender({
    lastEvent: coverageEvent({
      event_id: 'evt-x',
      payload: {
        offensive_formation: null,
        offensive_formation_family: null,
        defensive_coverage: null,
      },
    }),
  });
  expect(onCoverage).not.toHaveBeenCalled();
  expect(result.current.coverage).toBeNull();
});
