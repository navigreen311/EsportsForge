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
