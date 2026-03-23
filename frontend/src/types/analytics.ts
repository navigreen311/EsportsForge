export interface SessionRecord {
  id: string;
  date: string;
  mode: 'ranked' | 'tournament' | 'training';
  wins: number;
  losses: number;
  winRate: number;
  opponentGamertag: string;
  score: string; // e.g., "28-14"
  keyPlays: string[];
  duration: number; // minutes
}

export interface WinRateDataPoint {
  date: string;
  winRate: number;
  sessions: number;
}

export interface ModePerformance {
  mode: 'ranked' | 'tournament' | 'training';
  totalGames: number;
  wins: number;
  losses: number;
  winRate: number;
  avgScore: number;
}

export interface WeaknessHeatmapEntry {
  skill: string;
  impactRank: number; // 1-10, higher = more impactful
  currentLevel: number; // 0-100
  targetLevel: number; // 0-100
  category: 'offense' | 'defense' | 'situational' | 'mental';
}

export interface AgentAccuracyEntry {
  agentName: string;
  predictionsTotal: number;
  predictionsCorrect: number;
  accuracy: number;
  trend: 'up' | 'down' | 'stable';
  lastUpdated: string;
}

export interface LoopAITrend {
  date: string;
  learningScore: number;
  adaptationRate: number;
  predictionConfidence: number;
}

export interface DrillRecord {
  id: string;
  name: string;
  instructions: string;
  reps: number;
  completedReps: number;
  successRate: number;
  impactRank: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'elite';
  skillTargets: SkillTarget[];
  isDynamicCalibration: boolean;
}

export interface SkillTarget {
  name: string;
  current: number;
  target: number;
}
