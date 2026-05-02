/**
 * Voice script builders for the Arsenal — turn a Weapon into the right
 * coaching lines for read-instructions, pre-execution brief, and debrief.
 */

import type { Weapon } from '@/hooks/useArsenal';
import type { ArsenalTitleId } from './titleMeta';

// ---------------------------------------------------------------------------
// Title family helpers
// ---------------------------------------------------------------------------

export type TitleFamily =
  | 'football'
  | 'basketball'
  | 'soccer'
  | 'fps'
  | 'fighting'
  | 'baseball'
  | 'golf'
  | 'poker';

export function titleFamily(titleId: ArsenalTitleId): TitleFamily {
  if (titleId === 'madden-26' || titleId === 'cfb-26') return 'football';
  if (titleId === 'nba-2k26') return 'basketball';
  if (titleId === 'eafc-26') return 'soccer';
  if (titleId === 'warzone' || titleId === 'fortnite') return 'fps';
  if (titleId === 'ufc-5' || titleId === 'undisputed') return 'fighting';
  if (titleId === 'mlb-26') return 'baseball';
  if (titleId === 'pga-2k25') return 'golf';
  return 'poker';
}

const FAMILY_CONFIDENCE_LINE: Record<TitleFamily, string> = {
  football: 'Your assignment is clear. Execute with confidence.',
  basketball: 'Read the defender, then go. Trust the move.',
  soccer: 'Touch, touch, then release. Calm hands.',
  fps: 'Eyes up. Move now.',
  fighting: 'Wait for the opening. Then commit.',
  baseball: 'Trust the sequence.',
  golf: 'Commit to the line.',
  poker: 'The math is clear.',
};

// ---------------------------------------------------------------------------
// Full read (Fix 1)
// ---------------------------------------------------------------------------

/**
 * Returns a list of "segments" — each segment maps to one step (or one
 * narrative line). The caller speaks them sequentially so it can highlight
 * the matching step in the UI as each utterance fires.
 */
export interface VoiceSegment {
  text: string;
  /** Section the segment belongs to so the UI can scroll/highlight. */
  section: 'intro' | 'when' | 'setup' | 'execution' | 'why' | 'counter' | 'outro';
  /** When section is "setup" or "execution", this is the 0-based step index. */
  stepIndex?: number;
}

function abbreviated(text: string, max = 220): string {
  if (text.length <= max) return text;
  const cut = text.slice(0, max);
  const lastDot = cut.lastIndexOf('.');
  return (lastDot > 100 ? cut.slice(0, lastDot + 1) : cut) + '…';
}

export function buildFullReadScript(weapon: Weapon): VoiceSegment[] {
  const fam = titleFamily(weapon.title_id);
  const segments: VoiceSegment[] = [];

  segments.push({
    text: `Secret weapon: ${weapon.name}. Category: ${weapon.category}.`,
    section: 'intro',
  });
  segments.push({ text: `When to use: ${weapon.when_to_use}`, section: 'when' });

  if (weapon.setup_steps?.length) {
    segments.push({
      text: `Setup. ${weapon.setup_steps.length} ${
        weapon.setup_steps.length === 1 ? 'step' : 'steps'
      }.`,
      section: 'setup',
    });
    weapon.setup_steps.forEach((s, i) =>
      segments.push({
        text: `Step ${i + 1}: ${s}`,
        section: 'setup',
        stepIndex: i,
      })
    );
  }

  if (weapon.instructions?.length) {
    segments.push({
      text: `Execution. ${weapon.instructions.length} ${
        weapon.instructions.length === 1 ? 'step' : 'steps'
      }.`,
      section: 'execution',
    });
    weapon.instructions.forEach((s, i) =>
      segments.push({
        text: `Step ${i + 1}: ${s}`,
        section: 'execution',
        stepIndex: i,
      })
    );
  }

  if (weapon.description) {
    segments.push({
      text: `What makes this unstoppable: ${abbreviated(weapon.description)}`,
      section: 'why',
    });
  }

  const counter = (weapon.trigger_conditions as Record<string, unknown>)?.counter;
  if (typeof counter === 'string' && counter.trim()) {
    segments.push({
      text: `Watch out for: ${counter.split('.')[0]}.`,
      section: 'counter',
    });
  }

  segments.push({
    text: `You have this. ${FAMILY_CONFIDENCE_LINE[fam]}`,
    section: 'outro',
  });

  return segments;
}

export function buildSetupOnlyScript(weapon: Weapon): VoiceSegment[] {
  return buildFullReadScript(weapon).filter((s) => s.section === 'setup');
}

export function buildExecutionOnlyScript(weapon: Weapon): VoiceSegment[] {
  return buildFullReadScript(weapon).filter((s) => s.section === 'execution');
}

// ---------------------------------------------------------------------------
// Guided practice intro / transitions (Fix 2)
// ---------------------------------------------------------------------------

export function guidedIntroLine(weapon: Weapon): string {
  return `${weapon.name}. I will walk you through this step by step. Say "next" when you are ready to advance, or tap the button. Let us begin.`;
}

export function guidedSetupToExecutionLine(): string {
  return 'Setup complete. Now the execution. When the snap happens, do exactly this:';
}

export function guidedCompletionLine(weapon: Weapon): string {
  const fam = titleFamily(weapon.title_id);
  return `That is the full play. You know what to do. When ArsenalAI gives you the signal, trust it. ${FAMILY_CONFIDENCE_LINE[fam]}`;
}

// ---------------------------------------------------------------------------
// Pre-execution brief (Fix 3) — under 30 seconds
// ---------------------------------------------------------------------------

export function buildPreExecBrief(weapon: Weapon, urgency?: string): string {
  const fam = titleFamily(weapon.title_id);
  const setup = (weapon.setup_steps ?? []).slice(0, 2);
  const exec = (weapon.instructions ?? []).slice(
    0,
    fam === 'fighting' ? 2 : fam === 'fps' ? 3 : fam === 'poker' ? 1 : 3
  );

  const parts: string[] = ['Quick brief.'];
  if (fam !== 'basketball' && setup.length) {
    parts.push('Setup: ' + setup.join('. '));
  }
  parts.push('Execute: ' + exec.join('. '));
  parts.push(
    urgency === 'now'
      ? 'Element of surprise is high. Trust the play.'
      : 'Trust the play.'
  );
  return parts.join(' ') + '.';
}

// ---------------------------------------------------------------------------
// Post-deployment debrief (Fix 4)
// ---------------------------------------------------------------------------

const WORKED_LINES: Record<TitleFamily, string> = {
  football:
    'That is what it looks like when the play works. Note what they showed pre-snap — you read it right. Confidence in that weapon: justified.',
  basketball:
    'Clean execution. Their defender over-committed. You recognized it and punished it.',
  soccer:
    'Clean touch into space. Their shape broke right where the model said it would.',
  fps:
    'Perfect timing on that rotation. That position wins that fight every time.',
  fighting:
    'The setup worked. They did not see the combo coming. File that pattern. Use it in the next round if needed.',
  baseball:
    'They chased. Your sequence set it up perfectly. LoopAI has noted this tendency for future at-bats.',
  golf:
    'Committed to the line and it held. Wind read was correct. Trust that read again.',
  poker:
    'Correct hold. The math played out. That is optimal strategy executed cleanly.',
};

const FAILED_LINES: Record<TitleFamily, string> = {
  football:
    'They read it. Happens. Note what they showed — did they shift coverage pre-snap? That is your tell for next time.',
  basketball:
    'Defender stayed disciplined. Check if they are scouting your dribble package. Variant move next time.',
  soccer:
    'Their block held. Rotate the angle on the next attempt — same idea, different lane.',
  fps:
    'They had the angle covered. Your positioning was right — they were just already there. Adjust the rotation timing.',
  fighting:
    'They slipped it. The setup telegraphed. Change the feint pattern on the next attempt.',
  baseball:
    'They laid off. They may be sitting on that pitch. Change the eye level — go down next time.',
  golf:
    'Misread the wind shift. Check the flag movement at address next time. The read was close — execution was right.',
  poker:
    'Variance. The hold was still mathematically correct. Stick to the strategy — do not deviate from optimal play.',
};

export function buildDebriefLine(weapon: Weapon, worked: boolean): string {
  const fam = titleFamily(weapon.title_id);
  return worked ? WORKED_LINES[fam] : FAILED_LINES[fam];
}
