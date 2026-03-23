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
  | 'Singleback Ace'
  | 'Shotgun Trips'
  | 'I-Form Close'
  | 'Gun Empty'
  | 'Pistol Strong'
  | 'Nickel Double A Gap'
  | '3-4 Odd'
  | '4-3 Under'
  | 'Dime Normal';

export interface Play {
  id: string;
  name: string;
  formation: Formation;
  situationTags: SituationTag[];
  confidenceScore: number; // 0-100
  isKillSheetPlay: boolean;
  description: string;
  audibleOptions?: AudibleNode[];
}

export interface AudibleNode {
  id: string;
  label: string;
  trigger: string; // e.g., "Cover 3 detected", "Blitz look"
  targetPlay: string;
  children?: AudibleNode[];
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
  createdAt: string;
  updatedAt: string;
}

export type PackageTab = 'all' | 'kill-sheet' | 'red-zone' | 'anti-blitz';
