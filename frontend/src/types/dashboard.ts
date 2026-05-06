export interface PriorityItem {
  id: string;
  weakness: string;
  category: 'offense' | 'defense' | 'situational' | 'mental';
  /** Which side of play this priority belongs to. A 'mental' or
   *  'situational' priority can be either offensive or defensive — this
   *  axis is independent of category. */
  side?: 'offense' | 'defense';
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
  proof?: RecommendationProof;
  /**
   * Tri-state follow status for the dashboard card:
   *  - `undefined` / `null`: no action yet → render Follow/Dismiss buttons
   *  - `true`: player tapped Follow (optimistic or persisted)
   *  - `false`: player tapped Dismiss (optimistic or persisted)
   * Independent of `outcome`, which encodes the final logged result.
   */
  followed?: boolean | null;
}

export interface RecommendationProof {
  reason: string;
  dataSource: string;
  riskIfIgnored: string;
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

export type TiltGuardMood = 'locked-in' | 'good' | 'tired' | 'frustrated' | 'tilted';

export interface FatigueIndicator {
  peakWindowMinutes: number;
  currentSessionMinutes: number | null;
  status: 'fresh' | 'peak' | 'fading' | 'fatigued';
}

export interface ExecutionGap {
  skill: string;
  drillRate: number;  // percentage
  rankedRate: number; // percentage
  drillId?: string;
}

export interface LoopAIDebrief {
  gameTimestamp: string;
  recommendation: string;
  wasFollowed: boolean | null;
  outcome: 'won' | 'lost';
  loopUpdate: string;
}

export interface BenchmarkMetric {
  label: string;
  percentile: number; // 0-100
}

export interface ProgressionPackage {
  name: string;
  percentComplete: number;
}

export interface TitleDashboardData {
  priorities: PriorityItem[];
  stats: DashboardStats;
  statLabels: { games: string; streak: string };
  progression: { current: ProgressionPackage; next: ProgressionPackage };
  executionGap: ExecutionGap;
  recommendations: RecommendationItem[];
  narrative: WeeklyNarrativeData;
  benchmarks: BenchmarkMetric[];
  debrief: LoopAIDebrief | null;
  hasData: boolean;
}

export interface DashboardData {
  username: string;
  stats: DashboardStats;
  priority: PriorityItem;
  priorities: PriorityItem[];
  recentRecommendations: RecommendationItem[];
  weeklyNarrative: WeeklyNarrativeData;
  quickActions: QuickAction[];
  activeSession: SessionStatus | null;
  upcomingTournament: TournamentInfo | null;
  fatigue: FatigueIndicator;
  executionGap: ExecutionGap;
  lastDebrief: LoopAIDebrief | null;
  benchmarks: BenchmarkMetric[];
  progression: { current: ProgressionPackage; next: ProgressionPackage };
}
