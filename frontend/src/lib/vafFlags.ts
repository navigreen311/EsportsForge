/**
 * VisionAudioForge feature-flag readers.
 *
 * Single source of truth for the Drill Lab live-vision gate. ENV-ONLY by
 * design (ADR 0001: env-var flags, engineer-flipped via deployment config +
 * restart — no in-app flip). Both the Drill Lab page (which ENFORCES the gate)
 * and the Settings read-only exposure (which DISPLAYS it) call this same
 * function, so what Settings shows is guaranteed to match what the page does.
 *
 * Deliberately NO localStorage / runtime override — a UI toggle would diverge
 * from ADR 0001. See docs/runbooks/1a-drill-lab-flag.md.
 */
export function drillLabVisionEnabled(): boolean {
  return process.env.NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED === 'true';
}

/**
 * SimLab live-vision gate (Phase 1b — SimLab cutover). Same env-only shape as
 * the Drill Lab flag (ADR 0001: engineer-flipped via deployment config +
 * restart, no in-app toggle). SimLab keys on FORMATION_LOCKED (live in Madden
 * adapter v0.1); PLAY_STARTED/PLAY_ENDED are a documented v0.2/v0.3 deferral.
 */
export function simlabVisionEnabled(): boolean {
  return process.env.NEXT_PUBLIC_VAF_SIMLAB_ENABLED === 'true';
}

/**
 * Gameplan live-vision gate (Phase 1b — Gameplan cutover). Same env-only shape
 * as the Drill Lab / SimLab flags (ADR 0001). Gameplan subscribes to
 * COVERAGE_LOCKED, which the Madden adapter does NOT emit until v0.3 — so this
 * is a SOFT-LAUNCH (ADR 0010 §45): with the flag on the subscription is
 * genuinely wired and live, but stays silent until v0.3. Expected silence, not
 * a bug.
 */
export function gameplanVisionEnabled(): boolean {
  return process.env.NEXT_PUBLIC_VAF_GAMEPLAN_ENABLED === 'true';
}
