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

export interface Opponent {
  id: string;
  gamertag: string;
  archetype: Archetype;
  encounterCount: number;
  lastSeen: string;
  winRate: number; // against this opponent
  isRival: boolean;
  tendencies: TendencyBreakdown[];
  playFrequencies: PlayFrequency[];
  weaknesses: WeaknessEntry[];
  behavioralSignals: BehavioralSignal[];
  killSheet: string[]; // play IDs
  avatarUrl?: string;
}
