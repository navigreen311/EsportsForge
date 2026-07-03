import { drillLabVisionEnabled } from '../vafFlags';

describe('drillLabVisionEnabled (env-only reader, ADR 0001)', () => {
  const KEY = 'NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED';
  const original = process.env[KEY];
  afterEach(() => {
    if (original === undefined) delete process.env[KEY];
    else process.env[KEY] = original;
  });

  test("'true' → on", () => {
    process.env[KEY] = 'true';
    expect(drillLabVisionEnabled()).toBe(true);
  });

  test("'false' → off", () => {
    process.env[KEY] = 'false';
    expect(drillLabVisionEnabled()).toBe(false);
  });

  test('other value → off (only exact "true")', () => {
    process.env[KEY] = '1';
    expect(drillLabVisionEnabled()).toBe(false);
  });

  test('unset → off (default)', () => {
    delete process.env[KEY];
    expect(drillLabVisionEnabled()).toBe(false);
  });
});
