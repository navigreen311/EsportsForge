export type SituationTag =
  | 'red-zone'
  | 'goal-line'
  | '3rd-down'
  | '2-minute'
  | 'opening-drive'
  | 'anti-blitz'
  | 'prevent'
  | 'hurry-up';

export type Formation =
  | 'Gun Spread'
  | 'Gun Trips TE'
  | 'Singleback Ace'
  | 'Shotgun Trips'
  | 'Shotgun Bunch'
  | 'I-Form Close'
  | 'Gun Empty'
  | 'Pistol Strong'
  | 'Singleback Deuce Close'
  | 'Gun Trey Open'
  | 'Nickel Double A Gap'
  | '3-4 Odd'
  | '4-3 Under'
  | 'Dime Normal';

export type ConceptTag =
  | 'man-beater'
  | 'zone-beater'
  | 'screen'
  | 'rpo'
  | 'play-action'
  | 'quick-pass'
  | 'deep-shot'
  | 'run'
  | 'draw'
  | 'misdirection';

/**
 * A point in the play-diagram coordinate space: 0–100 × 0–100, line of
 * scrimmage at y=60, offense below (y>60), routes run UP the field (decreasing
 * y). x grows left→right. Shared with `lib/arsenal/playDiagram` (`Pt`).
 */
export type DiagramPoint = [number, number];

/**
 * An explicit per-receiver route path in diagram space. Phase 2's gameplan
 * generation will emit these (LLM-produced, server-validated); until then they
 * can be authored directly on a Play to drive the animated diagram. When
 * absent, the diagram falls back to a concept template derived from the play's
 * name + tags (see `lib/gameplan/playDiagram`).
 */
export interface DiagramRoute {
  /** Receiver this route belongs to, e.g. "X", "Z", "TE", "SL", "HB". */
  receiver: string;
  /** Polyline; points[0] is the pre-snap alignment (at/near the LOS). */
  points: DiagramPoint[];
}

export interface Play {
  id: string;
  name: string;
  formation: Formation;
  conceptTags: ConceptTag[];
  situationTags: SituationTag[];
  confidenceScore: number; // 0-100
  isKillSheetPlay: boolean;
  description: string;
  beats?: string; // e.g., "Cover 3", "Man Blitz"
  audibleOptions?: AudibleNode[];
  /**
   * Explicit route geometry for the animated play diagram. Optional — when
   * present and valid it renders faithfully; when absent/invalid the diagram
   * degrades to a concept template, then a formation-only view, then text.
   */
  routes?: DiagramRoute[];
  // --- Depth fields (AI-generated at Generate time; when absent the UI falls
  // back to the static maps). Plain language, no jargon. ---
  /** One-line "base call" read for Layer 1 of the Call Structure. */
  baseRead?: string;
  /** Actionable "when to call" prose — replaces the vague tag labels. */
  whenToCall?: string;
  /** WHY / DATA / RISK / COMPARABLE, written for a normal player. */
  evidence?: PlayEvidence;
}

export interface AudibleNode {
  id: string;
  label: string;
  trigger: string; // e.g., "Cover 3 detected", "Blitz look"
  targetPlay: string;
  children?: AudibleNode[];
  // Plain-language teaching depth. Layer 2 ("if the pre-snap look is wrong"):
  lookFor?: string; // what to look for pre-snap
  recognize?: string; // how to recognize it / define the term in plain words
  do?: string; // exactly what to do
  // Layer 3 ("if they adjust to your adjustment"):
  counterLookFor?: string; // how to spot their counter-adjustment
  counterDo?: string; // what to do about it
}

/** Deep, plain-language evidence for a play (WHY / DATA / RISK / COMPARABLE). */
export interface PlayEvidence {
  why: string;
  data: string;
  risk: string;
  comparable: string;
}

export type MetaRating = 'Exploit' | 'Strong' | 'Neutral' | 'Countered';

export interface MetaStatus {
  rating: MetaRating;
  patchVersion: string;
  lastUpdated: string;
}

export interface Gameplan {
  id: string;
  name: string;
  opponentId: string;
  opponentName: string;
  plays: Play[];
  killSheet: Play[];
  redZonePackage: Play[];
  antiBlitzPackage: Play[];
  twoMinDrillPackage: Play[];
  metaStatus: MetaStatus;
  createdAt: string;
  updatedAt: string;
}

export type PackageTab = 'all' | 'kill-sheet' | 'red-zone' | 'anti-blitz' | '2-min-drill';
