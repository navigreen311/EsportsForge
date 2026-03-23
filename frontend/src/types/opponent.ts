export type Archetype =
  | 'Aggressive Rusher'
  | 'Pocket Passer'
  | 'Scrambler'
  | 'Zone Specialist'
  | 'Blitz Heavy'
  | 'Run First'
  | 'Balanced'
  | 'West Coast'
  | 'Air Raid'
  | 'Defensive Mastermind';

export type OpponentFilter = 'all' | 'rivals' | 'recent' | 'scouted';

export type OpponentSort = 'lastSeen' | 'encounters' | 'winRate';

export interface TendencyBreakdown {
  label: string;
  percentage: number;
  category: 'offense' | 'defense';
}

export interface PlayFrequency {
  playName: string;
  count: number;
  successRate: number;
}

export interface BehavioralSignal {
  type: 'timeout' | 'pace-change' | 'audible' | 'hot-route' | 'formation-shift';
  description: string;
  frequency: 'rare' | 'occasional' | 'frequent';
  situation: string;
}

export interface WeaknessEntry {
  area: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  exploitPlay?: string;
}

export interface KillSheetPlay {
  id: string;
  playName: string;
  formation: string;
  confidenceScore: number;
  successRate: number;
  description: string;
}

export interface Encounter {
  id: string;
  date: string;
  result: 'win' | 'loss';
  score: string;
  notes: string;
  mode: 'ranked' | 'tournament' | 'training';
}

export interface ArchetypeDetail {
  description: string;
  strengths: string[];
  weaknesses: string[];
}

export type DossierTab = 'overview' | 'tendencies' | 'plays' | 'killsheet' | 'history';

export interface Opponent {
  id: string;
  gamertag: string;
  archetype: Archetype;
  encounterCount: number;
  lastSeen: string;
  winRate: number;
  isRival: boolean;
  tendencies: TendencyBreakdown[];
  playFrequencies: PlayFrequency[];
  weaknesses: WeaknessEntry[];
  behavioralSignals: BehavioralSignal[];
  killSheet: KillSheetPlay[];
  encounters: Encounter[];
  archetypeDetail: ArchetypeDetail;
  record: { wins: number; losses: number };
  blitzFrequency: number;
  formationFrequencies: { formation: string; percentage: number }[];
  scoutedAt?: string;
  avatarUrl?: string;
}
