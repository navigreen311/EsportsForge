import {
  arsenalVisionEnabled,
  drillLabVisionEnabled,
  warRoomVisionEnabled,
} from '../vafFlags';

// Every VAF flag reader has the same env-only contract (ADR 0001): on iff the
// env var is exactly "true"; off for "false" / any other value / unset.
describe.each([
  ['drillLabVisionEnabled', 'NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED', drillLabVisionEnabled],
  ['arsenalVisionEnabled', 'NEXT_PUBLIC_VAF_ARSENAL_ENABLED', arsenalVisionEnabled],
  ['warRoomVisionEnabled', 'NEXT_PUBLIC_VAF_WAR_ROOM_ENABLED', warRoomVisionEnabled],
] as const)('%s (env-only reader, ADR 0001)', (_name, KEY, read) => {
  const original = process.env[KEY];
  afterEach(() => {
    if (original === undefined) delete process.env[KEY];
    else process.env[KEY] = original;
  });

  test("'true' → on", () => {
    process.env[KEY] = 'true';
    expect(read()).toBe(true);
  });

  test("'false' → off", () => {
    process.env[KEY] = 'false';
    expect(read()).toBe(false);
  });

  test('other value → off (only exact "true")', () => {
    process.env[KEY] = '1';
    expect(read()).toBe(false);
  });

  test('unset → off (default)', () => {
    delete process.env[KEY];
    expect(read()).toBe(false);
  });
});
