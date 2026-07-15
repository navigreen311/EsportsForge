/**
 * War Room coverage → one-line adjustment hint (Phase 1c, 1c.2).
 *
 * A concise, standard beat-it concept for each canonical coverage the Madden adapter
 * emits (Cover 0/1/2/2-Man/3/4/6/9). Read-only: this drives the "Cover N detected"
 * banner text; the LLM DefensiveSchemePanel remains the deep-adjustment surface. Kept
 * as a plain lookup with a safe generic fallback for any unmapped value (e.g. a future
 * coverage or the 6/9-mirror residual).
 */
const HINTS: Record<string, string> = {
  'Cover 0': 'All-out man blitz, no help — hot routes and quick slants/picks beat the pressure.',
  'Cover 1': 'Man-free — crossers and mesh; iso your best matchup away from the robber.',
  'Cover 2': 'Two-deep zone — attack the deep middle (the hole) and the sideline honey-holes.',
  'Cover 2-Man': 'Man under two-deep — rub/pick concepts and verticals up the seam.',
  'Cover 3': 'Three-deep shell — flood the flats and hit the seams between the deep thirds.',
  'Cover 4 (Quarters)': 'Four-deep — underneath is soft; curls, comebacks, and the run.',
  'Cover 6': 'Quarter-quarter-half — attack the two-deep (half-field) side.',
  'Cover 9': 'Mirror of Cover 6 — attack the half-field side deep.',
};

export function coverageAdjustment(coverage: string): string {
  return HINTS[coverage] ?? `Read ${coverage} pre-snap and check to your best concept.`;
}
