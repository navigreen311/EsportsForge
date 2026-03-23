export interface PriorityItem {
  id: string;
  weakness: string;
  category: 'offense' | 'defense' | 'situational' | 'mental';
  winRateDamage: number; // percentage points lost
  expectedLift: number; // percentage points gained if fixed
  timeToMaster: string; // e.g., "2-3 weeks"
  confidence: number; // 0-100
  impactRank: number; // 1-10
}

export interface RecommendationItem {
  id: string;
  agentSource: string;
  text: string;
  confidence: number; // 0-100
  outcome: 'followed' | 'ignored' | 'pending';
  timestamp: string;
}

export interface WeeklyNarrativeData {
  narrative: string;
  milestones: { label: string; achieved: boolean }[];
  weekLabel: string;
}

export interface QuickAction {
  id: string;
  label: string;
  description: string;
  href: string;
  icon: string; // lucide icon name reference
}

export interface SessionStatus {
  isActive: boolean;
  type?: 'ranked' | 'tournament' | 'training';
  startedAt?: string;
  opponent?: string;
  score?: string;
}

export interface TournamentInfo {
  id: string;
  name: string;
  date: string;
  format: string;
  registeredPlayers: number;
  status: 'upcoming' | 'live' | 'completed';
}

export interface DashboardStats {
  winRate: number;
  totalGames: number;
  currentStreak: number;
  readiness: number;
}

export interface DashboardData {
  username: string;
  stats: DashboardStats;
  priority: PriorityItem;
  recentRecommendations: RecommendationItem[];
  weeklyNarrative: WeeklyNarrativeData;
  quickActions: QuickAction[];
  activeSession: SessionStatus | null;
  upcomingTournament: TournamentInfo | null;
}
