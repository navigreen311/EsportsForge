/** @jest-environment jsdom */
import { render, screen } from '@testing-library/react';

import DrillLabVisionStatus from '../DrillLabVisionStatus';

// Standard Jest matchers only (no jest-dom setup in this repo's config):
// getByText throws if absent; queryBy* returns null if absent.
const KEY = 'NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED';
const original = process.env[KEY];
afterEach(() => {
  if (original === undefined) delete process.env[KEY];
  else process.env[KEY] = original;
});

test('renders On when the flag env is "true"', () => {
  process.env[KEY] = 'true';
  render(<DrillLabVisionStatus />);
  expect(screen.queryByText('On')).not.toBeNull();
  expect(screen.queryByText('Off')).toBeNull();
});

test('renders Off when the flag env is unset', () => {
  delete process.env[KEY];
  render(<DrillLabVisionStatus />);
  expect(screen.queryByText('Off')).not.toBeNull();
  expect(screen.queryByText('On')).toBeNull();
});

test('shows the engineer-controlled label', () => {
  process.env[KEY] = 'true';
  render(<DrillLabVisionStatus />);
  expect(screen.queryByText(/engineer-controlled/i)).not.toBeNull();
});

test('has NO interactive control (read-only exposure, ADR 0001)', () => {
  process.env[KEY] = 'true';
  render(<DrillLabVisionStatus />);
  expect(screen.queryByRole('button')).toBeNull();
  expect(screen.queryByRole('switch')).toBeNull();
  expect(screen.queryByRole('checkbox')).toBeNull();
});
