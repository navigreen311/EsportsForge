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
}

export interface AudibleNode {
  id: string;
  label: string;
  trigger: string; // e.g., "Cover 3 detected", "Blitz look"
  targetPlay: string;
  children?: AudibleNode[];
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
