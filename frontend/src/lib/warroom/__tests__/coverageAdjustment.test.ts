import { coverageAdjustment } from '../coverageAdjustment';

test('known coverages map to a specific hint', () => {
  expect(coverageAdjustment('Cover 3')).toMatch(/seams/i);
  expect(coverageAdjustment('Cover 2')).toMatch(/deep middle/i);
  expect(coverageAdjustment('Cover 0')).toMatch(/blitz/i);
  expect(coverageAdjustment('Cover 4 (Quarters)')).toMatch(/underneath/i);
});

test('an unmapped coverage falls back to a safe generic hint (no throw)', () => {
  expect(coverageAdjustment('Cover 42')).toContain('Cover 42');
  expect(coverageAdjustment('')).toBeTruthy();
});
