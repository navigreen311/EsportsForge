// ---------------------------------------------------------------------------
// Title-specific mock data for all 11 titles
// Every dashboard component pulls from this via getDashboardDataForTitle()
// ---------------------------------------------------------------------------

import type {
  TitleDashboardData,
  PriorityItem,
  RecommendationItem,
  WeeklyNarrativeData,
  DashboardStats,
  ExecutionGap,
  LoopAIDebrief,
  BenchmarkMetric,
  ProgressionPackage,
} from '@/types/dashboard';

// ---- Helper: empty / no-data shell ----------------------------------------

function emptyData(overrides: {
  gamesLabel: string;
  streakLabel: string;
}): TitleDashboardData {
  return {
    priorities: [],
    stats: { winRate: 0, totalGames: 0, currentStreak: 0, readiness: 0 },
    statLabels: { games: overrides.gamesLabel, streak: overrides.streakLabel },
    progression: {
      current: { name: 'Awaiting first session', percentComplete: 0 },
      next: { name: 'Will generate after session 1', percentComplete: 0 },
    },
    executionGap: { skill: 'N/A', drillRate: 0, rankedRate: 0 },
    recommendations: [],
    narrative: {
      weekLabel: 'No sessions yet',
      narrative:
        'Play your first session to unlock AI-powered coaching insights. Your dashboard will populate with priorities, recommendations, and progression tracking after your initial games.',
      milestones: [],
    },
    benchmarks: [],
    debrief: null,
    hasData: false,
  };
}

// ===========================================================================
// MADDEN 26
// ===========================================================================

const madden26: TitleDashboardData = {
  priorities: [
    {
      id: 'mad-pri-1',
      weakness: 'Coverage Read Speed',
      category: 'mental',
      winRateDamage: 8.3,
      expectedLift: 5.7,
      timeToMaster: '2-3 weeks',
      confidence: 87,
      impactRank: 9.4,
    },
    {
      id: 'mad-pri-2',
      weakness: 'Red Zone Efficiency',
      category: 'situational',
      winRateDamage: 5.1,
      expectedLift: 3.9,
      timeToMaster: '1-2 weeks',
      confidence: 82,
      impactRank: 7.8,
    },
    {
      id: 'mad-pri-3',
      weakness: 'Blitz Recognition',
      category: 'defense',
      winRateDamage: 4.2,
      expectedLift: 3.1,
      timeToMaster: '3-4 weeks',
      confidence: 76,
      impactRank: 6.5,
    },
  ],
  stats: { winRate: 67, totalGames: 142, currentStreak: 8, readiness: 84 },
  statLabels: { games: 'Games Played', streak: 'Win Streak' },
  progression: {
    current: { name: 'Base Pass Concepts', percentComplete: 67 },
    next: { name: 'Pressure Package', percentComplete: 0 },
  },
  executionGap: { skill: 'Coverage Reads', drillRate: 91, rankedRate: 54 },
  recommendations: [
    {
      id: 'mad-rec-1',
      agentSource: 'GameplanAgent',
      text: 'Switch to Cover 3 Sky against spread formations — your Cover 2 has been exploited in 4 of last 6 games.',
      confidence: 91,
      outcome: 'followed',
      timestamp: '2h ago',
      proof: {
        reason: 'Cover 2 exploited 4/6 games vs spread — opponents averaging 8.2 YPA',
        dataSource: 'Last 6 games vs spread formation opponents',
        riskIfIgnored: 'Exposed on wheel route if opponent motions the back out of backfield',
      },
    },
    {
      id: 'mad-rec-2',
      agentSource: 'DrillCoach',
      text: 'Add pre-snap read drills to your warm-up. Your read speed is 23% below your target.',
      confidence: 85,
      outcome: 'followed',
      timestamp: '5h ago',
      proof: {
        reason: 'Read speed avg 1.8s vs 1.4s target — costing 2.1 win-rate points',
        dataSource: 'PlayerTwin read-speed telemetry, 30-day trend',
        riskIfIgnored: 'Read speed regression likely if not drilled within 48h',
      },
    },
    {
      id: 'mad-rec-3',
      agentSource: 'OpponentScout',
      text: 'xXDragonSlayerXx favors HB Dive on 3rd & short — stack the box.',
      confidence: 78,
      outcome: 'pending',
      timestamp: '1d ago',
      proof: {
        reason: 'HB Dive called 72% of 3rd-and-short by this opponent (18/25 plays)',
        dataSource: 'OpponentScout encounter history, 8 games tracked',
        riskIfIgnored: 'Opponent converts 3rd down at 68% if box isn\'t stacked',
      },
    },
    {
      id: 'mad-rec-4',
      agentSource: 'SituationAnalyzer',
      text: 'Your red zone efficiency drops 18% in the 4th quarter — practice clutch scoring scenarios.',
      confidence: 82,
      outcome: 'ignored',
      timestamp: '1d ago',
      proof: {
        reason: '4th quarter RZ efficiency 41% vs 59% in quarters 1-3',
        dataSource: 'Session analytics, last 20 games with RZ attempts',
        riskIfIgnored: 'Estimated 1.4 points per game left on the table in close matches',
      },
    },
    {
      id: 'mad-rec-5',
      agentSource: 'GameplanAgent',
      text: 'PA Crossers has a 74% success rate vs man coverage — make it your go-to on 2nd & medium.',
      confidence: 88,
      outcome: 'followed',
      timestamp: '2d ago',
      proof: {
        reason: 'PA Crossers success rate 74% vs man (23/31 plays) — 12.4 avg yards',
        dataSource: 'Play-level analytics, current season',
        riskIfIgnored: '2nd & medium conversion rate stays at 48% instead of projected 61%',
      },
    },
  ],
  narrative: {
    weekLabel: 'Week of Mar 16 – 22',
    narrative:
      'This week you hit a new stride. Your win rate climbed to 67% — up 5 points from last week — driven by sharper pre-snap reads and better clutch execution. The 8-game streak is your longest this season. Your biggest remaining gap is coverage read speed, but the DrillCoach sees strong momentum if you stay consistent with your daily reps.',
    milestones: [
      { label: '8-Game Win Streak', achieved: true },
      { label: '67% Win Rate', achieved: true },
      { label: 'Pre-Snap Reads +12%', achieved: true },
    ],
  },
  benchmarks: [
    { label: 'Read Speed', percentile: 72 },
    { label: 'Clutch Conversion', percentile: 34 },
    { label: 'User Defense', percentile: 58 },
    { label: 'Execution Under Pressure', percentile: 81 },
  ],
  debrief: {
    gameTimestamp: '2h ago',
    recommendation: 'Switch to Cover 3 Sky against spread formations',
    wasFollowed: true,
    outcome: 'won',
    loopUpdate: 'Boosted Cover 3 Sky confidence to 91% for spread matchups',
  },
  hasData: true,
};

// ===========================================================================
// CFB 26
// ===========================================================================

const cfb26: TitleDashboardData = {
  priorities: [
    {
      id: 'cfb-pri-1',
      weakness: 'Option Read Timing',
      category: 'mental',
      winRateDamage: 7.9,
      expectedLift: 5.3,
      timeToMaster: '2-3 weeks',
      confidence: 84,
      impactRank: 9.1,
    },
    {
      id: 'cfb-pri-2',
      weakness: 'Red Zone Play Selection',
      category: 'situational',
      winRateDamage: 5.4,
      expectedLift: 4.1,
      timeToMaster: '1-2 weeks',
      confidence: 79,
      impactRank: 7.5,
    },
    {
      id: 'cfb-pri-3',
      weakness: 'Blitz Pickup Assignments',
      category: 'defense',
      winRateDamage: 4.6,
      expectedLift: 3.3,
      timeToMaster: '3-4 weeks',
      confidence: 73,
      impactRank: 6.8,
    },
  ],
  stats: { winRate: 63, totalGames: 118, currentStreak: 5, readiness: 79 },
  statLabels: { games: 'Games Played', streak: 'Win Streak' },
  progression: {
    current: { name: 'RPO Fundamentals', percentComplete: 58 },
    next: { name: 'Zone Read Package', percentComplete: 0 },
  },
  executionGap: { skill: 'Option Reads', drillRate: 87, rankedRate: 49 },
  recommendations: [
    {
      id: 'cfb-rec-1',
      agentSource: 'GameplanAgent',
      text: 'Use RPO Bubble Screen when the linebacker walks up — your read-and-react is 31% faster on bubble vs mesh.',
      confidence: 89,
      outcome: 'followed',
      timestamp: '3h ago',
      proof: {
        reason: 'Bubble screen success 78% vs walked-up LB, mesh only 47%',
        dataSource: 'RPO play breakdown, last 15 games',
        riskIfIgnored: 'Sack rate jumps 22% if you default to mesh against walked-up LB',
      },
    },
    {
      id: 'cfb-rec-2',
      agentSource: 'DrillCoach',
      text: 'Focus on pitch-read timing in the triple option — your give/keep decision is 0.4s too slow.',
      confidence: 83,
      outcome: 'pending',
      timestamp: '6h ago',
      proof: {
        reason: 'Give/keep decision avg 1.6s vs 1.2s target — fumble risk up 15%',
        dataSource: 'Option-play telemetry, 30-day window',
        riskIfIgnored: 'Fumble rate on option plays stays at 8% vs 3% target',
      },
    },
    {
      id: 'cfb-rec-3',
      agentSource: 'OpponentScout',
      text: 'Alabama_GOAT_23 blitzes the edge 64% of the time on 3rd down — run screen passes to exploit.',
      confidence: 76,
      outcome: 'pending',
      timestamp: '1d ago',
      proof: {
        reason: 'Edge blitz 64% on 3rd down (16/25 plays) — screen pass success 71% vs edge blitz',
        dataSource: 'OpponentScout encounter history, 6 games tracked',
        riskIfIgnored: 'Sack rate on 3rd down stays at 24% vs this opponent',
      },
    },
    {
      id: 'cfb-rec-4',
      agentSource: 'SituationAnalyzer',
      text: 'Your two-minute drill efficiency is 38% — practice hurry-up scoring drives.',
      confidence: 80,
      outcome: 'ignored',
      timestamp: '1d ago',
      proof: {
        reason: 'Two-minute drill TD rate 38% vs 55% league average for your tier',
        dataSource: 'Situational analytics, last 25 games',
        riskIfIgnored: 'Estimated 2.1 points per game lost in close half/game-ending scenarios',
      },
    },
    {
      id: 'cfb-rec-5',
      agentSource: 'GameplanAgent',
      text: 'Inside Zone has an 81% success rate from Pistol formation — make it your base run play.',
      confidence: 86,
      outcome: 'followed',
      timestamp: '2d ago',
      proof: {
        reason: 'Inside Zone from Pistol: 81% success (29/36 plays), 5.8 avg YPC',
        dataSource: 'Play-level analytics, current season',
        riskIfIgnored: 'Run game efficiency drops to 52% if defaulting to Shotgun runs',
      },
    },
  ],
  narrative: {
    weekLabel: 'Week of Mar 16 – 22',
    narrative:
      'Solid week on the virtual gridiron. Your RPO execution has improved noticeably, with option-read accuracy up 9% from last week. The 5-game win streak shows your gameplay is clicking, but two-minute drill efficiency remains a weak spot. Stick with the DrillCoach reps on pitch-read timing and you should see that translate to ranked play within a week.',
    milestones: [
      { label: '5-Game Win Streak', achieved: true },
      { label: 'RPO Accuracy +9%', achieved: true },
      { label: 'Two-Minute Drill 50%', achieved: false },
    ],
  },
  benchmarks: [
    { label: 'Option Read Speed', percentile: 68 },
    { label: 'Clutch Conversion', percentile: 41 },
    { label: 'User Defense', percentile: 53 },
    { label: 'Execution Under Pressure', percentile: 76 },
  ],
  debrief: {
    gameTimestamp: '3h ago',
    recommendation: 'Use RPO Bubble Screen when the linebacker walks up',
    wasFollowed: true,
    outcome: 'won',
    loopUpdate: 'Bubble Screen confidence boosted to 89% vs walked-up LB formations',
  },
  hasData: true,
};

// ===========================================================================
// NBA 2K26
// ===========================================================================

const nba2k26: TitleDashboardData = {
  priorities: [
    {
      id: 'nba-pri-1',
      weakness: 'Shot Timing Consistency',
      category: 'mental',
      winRateDamage: 7.1,
      expectedLift: 4.8,
      timeToMaster: '2-3 weeks',
      confidence: 85,
      impactRank: 8.9,
    },
    {
      id: 'nba-pri-2',
      weakness: 'Pick & Roll Defense',
      category: 'defense',
      winRateDamage: 6.2,
      expectedLift: 4.1,
      timeToMaster: '2-3 weeks',
      confidence: 80,
      impactRank: 7.5,
    },
    {
      id: 'nba-pri-3',
      weakness: 'Dribble Package Efficiency',
      category: 'offense',
      winRateDamage: 5.5,
      expectedLift: 3.6,
      timeToMaster: '1-2 weeks',
      confidence: 77,
      impactRank: 6.8,
    },
  ],
  stats: { winRate: 61, totalGames: 89, currentStreak: 5, readiness: 78 },
  statLabels: { games: 'Games Played', streak: 'Win Streak' },
  progression: {
    current: { name: 'Base Half-Court Offense', percentComplete: 54 },
    next: { name: 'Pick & Roll Package', percentComplete: 0 },
  },
  executionGap: { skill: 'Shot Timing', drillRate: 88, rankedRate: 52 },
  recommendations: [
    {
      id: 'nba-rec-1',
      agentSource: 'GameplanAgent',
      text: 'Run pick & roll with your center on the left side — opponents are hedging poorly on that side 68% of the time.',
      confidence: 87,
      outcome: 'followed',
      timestamp: '4h ago',
      proof: {
        reason: 'Left-side PnR scores 1.14 PPP vs 0.81 PPP on right side',
        dataSource: 'Play-by-play analytics, last 20 games',
        riskIfIgnored: 'Half-court offense efficiency stays at 0.92 PPP vs projected 1.08',
      },
    },
    {
      id: 'nba-rec-2',
      agentSource: 'DrillCoach',
      text: 'Spacing drill: practice kicking out to the corner on drive-and-kick plays — your relocation timing is 0.3s slow.',
      confidence: 82,
      outcome: 'pending',
      timestamp: '8h ago',
      proof: {
        reason: 'Corner kick-out arrives 0.3s late, closing the shooting window by 40%',
        dataSource: 'Drive-and-kick telemetry, 30-day trend',
        riskIfIgnored: 'Open 3PT rate on kick-outs stays at 31% vs 52% with proper timing',
      },
    },
    {
      id: 'nba-rec-3',
      agentSource: 'SituationAnalyzer',
      text: 'Your fast break conversion drops to 41% when you have a 2-on-1 — practice the read to pass or finish.',
      confidence: 79,
      outcome: 'ignored',
      timestamp: '1d ago',
      proof: {
        reason: '2-on-1 fast break conversion 41% vs 72% league average at your tier',
        dataSource: 'Transition analytics, last 30 games',
        riskIfIgnored: 'Estimated 3.2 points per game left on the table in transition',
      },
    },
  ],
  narrative: {
    weekLabel: 'Week of Mar 16 – 22',
    narrative:
      'Your court game is heating up. Win rate at 61% with a 5-game streak — your best run this month. Shot timing is the big unlock: you hit 88% in drills but only 52% translates to ranked play. The gap is narrowing though, down from 41% last week. Keep grinding the DrillCoach reps and focus on replicating drill tempo in-game.',
    milestones: [
      { label: '5-Game Win Streak', achieved: true },
      { label: '60%+ Win Rate', achieved: true },
      { label: 'Shot Timing Gap < 30%', achieved: false },
    ],
  },
  benchmarks: [
    { label: 'Shot Timing', percentile: 65 },
    { label: 'Court Vision', percentile: 48 },
    { label: 'Defensive IQ', percentile: 71 },
    { label: 'Clutch Shooting', percentile: 39 },
  ],
  debrief: {
    gameTimestamp: '4h ago',
    recommendation: 'Run pick & roll with center on the left side',
    wasFollowed: true,
    outcome: 'won',
    loopUpdate: 'Left-side PnR confidence boosted to 87% — added to preferred play set',
  },
  hasData: true,
};

// ===========================================================================
// EA FC 26
// ===========================================================================

const fc26: TitleDashboardData = {
  priorities: [
    {
      id: 'fc-pri-1',
      weakness: 'Manual Defending Discipline',
      category: 'defense',
      winRateDamage: 6.8,
      expectedLift: 4.5,
      timeToMaster: '2-3 weeks',
      confidence: 83,
      impactRank: 8.2,
    },
    {
      id: 'fc-pri-2',
      weakness: 'Skill Move Efficiency',
      category: 'offense',
      winRateDamage: 5.9,
      expectedLift: 3.8,
      timeToMaster: '1-2 weeks',
      confidence: 78,
      impactRank: 7.1,
    },
    {
      id: 'fc-pri-3',
      weakness: 'Tactical Switching Speed',
      category: 'mental',
      winRateDamage: 4.7,
      expectedLift: 3.2,
      timeToMaster: '2-4 weeks',
      confidence: 74,
      impactRank: 6.4,
    },
  ],
  stats: { winRate: 58, totalGames: 76, currentStreak: 3, readiness: 72 },
  statLabels: { games: 'Matches', streak: 'Win Streak' },
  progression: {
    current: { name: 'Base Formation 4-3-3', percentComplete: 71 },
    next: { name: 'High Press Package', percentComplete: 0 },
  },
  executionGap: { skill: 'Manual Defending', drillRate: 85, rankedRate: 48 },
  recommendations: [
    {
      id: 'fc-rec-1',
      agentSource: 'GameplanAgent',
      text: 'Switch to manual jockeying instead of AI contain — your opponents are dribbling past AI defenders 62% of the time.',
      confidence: 86,
      outcome: 'followed',
      timestamp: '3h ago',
      proof: {
        reason: 'AI contain beaten 62% vs skilled dribblers — manual jockey cuts to 34%',
        dataSource: 'Defensive action analysis, last 15 matches',
        riskIfIgnored: 'Goals conceded per match stays at 2.4 vs projected 1.6 with manual defending',
      },
    },
    {
      id: 'fc-rec-2',
      agentSource: 'DrillCoach',
      text: 'Practice ball roll + fake shot combo — you attempt it 8 times per match but only succeed 3 times.',
      confidence: 81,
      outcome: 'pending',
      timestamp: '6h ago',
      proof: {
        reason: 'Ball roll + fake shot success rate 37% (3/8 per match) vs 65% target',
        dataSource: 'Skill move telemetry, 20-match window',
        riskIfIgnored: 'Turnovers from failed skill moves cost 0.8 goals per match on counter-attacks',
      },
    },
    {
      id: 'fc-rec-3',
      agentSource: 'SituationAnalyzer',
      text: 'Your set piece conversion is 31% — practice corner kick routines with near-post runs.',
      confidence: 77,
      outcome: 'ignored',
      timestamp: '1d ago',
      proof: {
        reason: 'Set piece conversion 31% vs 48% average at your division',
        dataSource: 'Set piece analytics, current season',
        riskIfIgnored: 'Missing 0.6 goals per match from set pieces',
      },
    },
  ],
  narrative: {
    weekLabel: 'Week of Mar 16 – 22',
    narrative:
      'Steady progress on the pitch this week. Your win rate is holding at 58% with a modest 3-match streak. Manual defending is the key area to unlock — you execute well in drills at 85% but ranked play drops to 48%. The good news: your 4-3-3 base is nearly mastered at 71% completion. Focus on closing the defending gap and set pieces for the biggest immediate impact.',
    milestones: [
      { label: '4-3-3 Formation 70%+', achieved: true },
      { label: '60% Win Rate', achieved: false },
      { label: 'Manual Defending Gap < 30%', achieved: false },
    ],
  },
  benchmarks: [
    { label: 'Manual Defending', percentile: 52 },
    { label: 'Skill Moves', percentile: 61 },
    { label: 'Positioning', percentile: 44 },
    { label: 'Set Pieces', percentile: 73 },
  ],
  debrief: {
    gameTimestamp: '3h ago',
    recommendation: 'Switch to manual jockeying instead of AI contain',
    wasFollowed: true,
    outcome: 'won',
    loopUpdate: 'Manual jockey confidence boosted to 86% — goals conceded dropped to 1 this match',
  },
  hasData: true,
};

// ===========================================================================
// MLB THE SHOW 26
// ===========================================================================

const mlbtheshow26: TitleDashboardData = {
  priorities: [
    {
      id: 'mlb-pri-1',
      weakness: 'Pitch Recognition Speed',
      category: 'mental',
      winRateDamage: 7.5,
      expectedLift: 5.1,
      timeToMaster: '3-4 weeks',
      confidence: 84,
      impactRank: 8.6,
    },
    {
      id: 'mlb-pri-2',
      weakness: 'Zone Discipline',
      category: 'mental',
      winRateDamage: 5.8,
      expectedLift: 3.9,
      timeToMaster: '2-3 weeks',
      confidence: 79,
      impactRank: 7.2,
    },
    {
      id: 'mlb-pri-3',
      weakness: 'Breaking Ball Timing',
      category: 'mental',
      winRateDamage: 4.9,
      expectedLift: 3.4,
      timeToMaster: '2-3 weeks',
      confidence: 75,
      impactRank: 6.1,
    },
  ],
  stats: { winRate: 55, totalGames: 64, currentStreak: 2, readiness: 68 },
  statLabels: { games: 'Games', streak: 'Streak' },
  progression: {
    current: { name: 'Base Pitch Sequencing', percentComplete: 42 },
    next: { name: 'Off-Speed Package', percentComplete: 0 },
  },
  executionGap: { skill: 'Pitch Recognition', drillRate: 82, rankedRate: 41 },
  recommendations: [
    {
      id: 'mlb-rec-1',
      agentSource: 'GameplanAgent',
      text: 'Lay off sliders away from righties — you chase that pitch 58% of the time, leading to weak contact.',
      confidence: 88,
      outcome: 'followed',
      timestamp: '5h ago',
      proof: {
        reason: 'Chase rate on away sliders 58% vs 22% target — results in 0.89 OPS against',
        dataSource: 'Pitch-level analytics, last 30 games',
        riskIfIgnored: 'Batting average stays at .218 vs projected .267 with better discipline',
      },
    },
    {
      id: 'mlb-rec-2',
      agentSource: 'DrillCoach',
      text: 'Practice identifying curveball spin out of the hand — your recognition time is 0.2s behind target.',
      confidence: 83,
      outcome: 'pending',
      timestamp: '8h ago',
      proof: {
        reason: 'Curveball recognition avg 0.45s vs 0.25s target — swing decision too late',
        dataSource: 'Pitch recognition telemetry, 30-day window',
        riskIfIgnored: 'Curveball whiff rate stays at 44% vs 18% at your tier average',
      },
    },
    {
      id: 'mlb-rec-3',
      agentSource: 'SituationAnalyzer',
      text: 'Your RISP average drops to .181 — practice situational hitting with runners on base.',
      confidence: 79,
      outcome: 'ignored',
      timestamp: '1d ago',
      proof: {
        reason: 'RISP avg .181 vs .267 overall — pressing leads to chasing out of zone',
        dataSource: 'Situational hitting analytics, current season',
        riskIfIgnored: 'Estimated 1.8 runs per game stranded due to RISP struggles',
      },
    },
  ],
  narrative: {
    weekLabel: 'Week of Mar 16 – 22',
    narrative:
      'Your batting eye is developing but still has a ways to go. Win rate at 55% with pitch recognition being the clear bottleneck — 82% in drills but only 41% in ranked play. Zone discipline is improving: chase rate down 6% from last week. The 2-game streak is modest but the trajectory is positive. Stay locked in on breaking ball recognition drills.',
    milestones: [
      { label: '55% Win Rate', achieved: true },
      { label: 'Chase Rate < 40%', achieved: false },
      { label: 'Pitch Recognition Gap < 30%', achieved: false },
    ],
  },
  benchmarks: [
    { label: 'Pitch Recognition', percentile: 42 },
    { label: 'Zone Discipline', percentile: 38 },
    { label: 'Power Hitting', percentile: 56 },
    { label: 'Clutch Hitting', percentile: 29 },
  ],
  debrief: {
    gameTimestamp: '5h ago',
    recommendation: 'Lay off sliders away from righties',
    wasFollowed: true,
    outcome: 'won',
    loopUpdate: 'Slider discipline confidence boosted to 88% — chase rate dropped to 41% this game',
  },
  hasData: true,
};

// ===========================================================================
// WARZONE
// ===========================================================================

const warzone: TitleDashboardData = {
  priorities: [
    {
      id: 'wz-pri-1',
      weakness: 'First Bullet Accuracy',
      category: 'mental',
      winRateDamage: 8.1,
      expectedLift: 5.5,
      timeToMaster: '2-3 weeks',
      confidence: 86,
      impactRank: 9.1,
    },
    {
      id: 'wz-pri-2',
      weakness: 'Zone Rotation Timing',
      category: 'situational',
      winRateDamage: 6.4,
      expectedLift: 4.2,
      timeToMaster: '2-4 weeks',
      confidence: 78,
      impactRank: 7.8,
    },
    {
      id: 'wz-pri-3',
      weakness: 'Loadout Optimization',
      category: 'offense',
      winRateDamage: 3.8,
      expectedLift: 2.6,
      timeToMaster: '1 week',
      confidence: 91,
      impactRank: 5.5,
    },
  ],
  stats: { winRate: 12, totalGames: 203, currentStreak: 1, readiness: 71 },
  statLabels: { games: 'Matches', streak: 'Win Streak' },
  progression: {
    current: { name: 'Base Loadout Package', percentComplete: 58 },
    next: { name: 'Final Circle Package', percentComplete: 0 },
  },
  executionGap: { skill: 'First Bullet Accuracy', drillRate: 84, rankedRate: 47 },
  recommendations: [
    {
      id: 'wz-rec-1',
      agentSource: 'GameplanAgent',
      text: 'Pre-aim common angles when rotating — your first-bullet accuracy is 47% in ranked vs 84% in drills.',
      confidence: 88,
      outcome: 'followed',
      timestamp: '1h ago',
      proof: {
        reason: 'First-bullet hit rate 47% in BR vs 84% in aim trainer — pre-aim cuts reaction time by 0.3s',
        dataSource: 'Gunfight telemetry, last 50 engagements',
        riskIfIgnored: 'Lose 62% of opening gunfights vs players who pre-aim',
      },
    },
    {
      id: 'wz-rec-2',
      agentSource: 'SituationAnalyzer',
      text: 'You die to zone damage in 18% of matches — start rotating 30s earlier when circle is far.',
      confidence: 84,
      outcome: 'pending',
      timestamp: '4h ago',
      proof: {
        reason: 'Zone death rate 18% (37/203 matches) — early rotation reduces to 4% historically',
        dataSource: 'Match death analysis, current season',
        riskIfIgnored: 'Nearly 1 in 5 matches ends to zone instead of gunfight',
      },
    },
    {
      id: 'wz-rec-3',
      agentSource: 'DrillCoach',
      text: 'Run recoil control drills with your primary AR — your spray pattern drifts 22% left after 15 rounds.',
      confidence: 81,
      outcome: 'ignored',
      timestamp: '1d ago',
      proof: {
        reason: 'Spray pattern left-drift 22% after 15 rounds — misses 3-4 bullets per mag in extended fights',
        dataSource: 'Recoil telemetry, aim trainer data',
        riskIfIgnored: 'TTK increases by 0.4s in mid-range engagements, losing advantage',
      },
    },
  ],
  narrative: {
    weekLabel: 'Week of Mar 16 – 22',
    narrative:
      'Battle royale is a grind, and your 12% win rate reflects the high variance nature of the mode. That said, your gunfight win rate is trending up — first-bullet accuracy improved 8% this week. Zone rotations are your biggest non-mechanical weakness, accounting for nearly 1 in 5 deaths. Tighten up rotations and keep drilling aim for the biggest uplift.',
    milestones: [
      { label: 'First Bullet Accuracy +8%', achieved: true },
      { label: '15% Win Rate', achieved: false },
      { label: 'Zone Deaths < 10%', achieved: false },
    ],
  },
  benchmarks: [
    { label: 'Aim Accuracy', percentile: 58 },
    { label: 'Positioning', percentile: 43 },
    { label: 'Zone Awareness', percentile: 36 },
    { label: 'Clutch Factor', percentile: 67 },
  ],
  debrief: {
    gameTimestamp: '1h ago',
    recommendation: 'Pre-aim common angles when rotating',
    wasFollowed: true,
    outcome: 'won',
    loopUpdate: 'Pre-aim confidence boosted to 88% — first-bullet hit rate up to 61% this match',
  },
  hasData: true,
};

// ===========================================================================
// FORTNITE
// ===========================================================================

const fortnite: TitleDashboardData = {
  priorities: [
    {
      id: 'fn-pri-1',
      weakness: 'Edit Speed Consistency',
      category: 'mental',
      winRateDamage: 7.8,
      expectedLift: 5.2,
      timeToMaster: '2-3 weeks',
      confidence: 84,
      impactRank: 8.8,
    },
    {
      id: 'fn-pri-2',
      weakness: 'Box Fight Decision Speed',
      category: 'mental',
      winRateDamage: 6.1,
      expectedLift: 4.0,
      timeToMaster: '2-4 weeks',
      confidence: 79,
      impactRank: 7.3,
    },
    {
      id: 'fn-pri-3',
      weakness: 'Material Management',
      category: 'situational',
      winRateDamage: 4.5,
      expectedLift: 3.1,
      timeToMaster: '1-2 weeks',
      confidence: 76,
      impactRank: 6.0,
    },
  ],
  stats: { winRate: 18, totalGames: 156, currentStreak: 2, readiness: 75 },
  statLabels: { games: 'Matches', streak: 'Win Streak' },
  progression: {
    current: { name: 'Base Building Package', percentComplete: 63 },
    next: { name: 'Advanced Edit Plays', percentComplete: 0 },
  },
  executionGap: { skill: 'Edit Speed', drillRate: 86, rankedRate: 49 },
  recommendations: [
    {
      id: 'fn-rec-1',
      agentSource: 'GameplanAgent',
      text: 'Use right-hand peek edits in box fights — you win 71% of fights with right peek vs 43% with left peek.',
      confidence: 87,
      outcome: 'followed',
      timestamp: '2h ago',
      proof: {
        reason: 'Right-hand peek win rate 71% vs 43% left peek — camera angle advantage',
        dataSource: 'Box fight analytics, last 40 engagements',
        riskIfIgnored: 'Box fight win rate stays at 52% instead of projected 64%',
      },
    },
    {
      id: 'fn-rec-2',
      agentSource: 'DrillCoach',
      text: 'Practice triple-edit sequences — your 3rd edit in a chain is 0.4s slower than your 1st.',
      confidence: 83,
      outcome: 'pending',
      timestamp: '5h ago',
      proof: {
        reason: '3rd edit avg 0.62s vs 0.22s for 1st edit — opponents react in the gap',
        dataSource: 'Edit speed telemetry, creative mode + ranked',
        riskIfIgnored: 'Multi-edit plays fail 58% of the time due to 3rd edit delay',
      },
    },
    {
      id: 'fn-rec-3',
      agentSource: 'SituationAnalyzer',
      text: 'You run out of materials in 24% of endgame fights — farm to 999 before moving into final zone.',
      confidence: 80,
      outcome: 'ignored',
      timestamp: '1d ago',
      proof: {
        reason: 'Material depletion in endgame 24% of matches — avg 312 mats entering final zone vs 750+ target',
        dataSource: 'Endgame resource analytics, last 50 matches',
        riskIfIgnored: 'Endgame win rate capped at 28% vs 45% with full materials',
      },
    },
  ],
  narrative: {
    weekLabel: 'Week of Mar 16 – 22',
    narrative:
      'Building and editing is where the game is won in Fortnite, and your edit speed is steadily improving. Win rate at 18% is solid for BR, and your 2-match streak shows momentum. The big gap: edit speed drops from 86% accuracy in creative to 49% in ranked. Box fight awareness is improving — right-hand peeks are becoming second nature. Keep farming materials heading into endgame.',
    milestones: [
      { label: 'Edit Speed Drills 85%+', achieved: true },
      { label: '20% Win Rate', achieved: false },
      { label: 'Material Management Endgame', achieved: false },
    ],
  },
  benchmarks: [
    { label: 'Edit Speed', percentile: 62 },
    { label: 'Building IQ', percentile: 55 },
    { label: 'Aim Accuracy', percentile: 49 },
    { label: 'Game Sense', percentile: 71 },
  ],
  debrief: {
    gameTimestamp: '2h ago',
    recommendation: 'Use right-hand peek edits in box fights',
    wasFollowed: true,
    outcome: 'won',
    loopUpdate: 'Right-hand peek confidence boosted to 87% — box fight win rate up to 68% this session',
  },
  hasData: true,
};

// ===========================================================================
// NO-DATA TITLES
// ===========================================================================

const ufc5: TitleDashboardData = emptyData({ gamesLabel: 'Fights', streakLabel: 'Win Streak' });
const pga2k25: TitleDashboardData = emptyData({ gamesLabel: 'Rounds', streakLabel: 'Streak' });
const undisputed: TitleDashboardData = emptyData({ gamesLabel: 'Fights', streakLabel: 'Win Streak' });
const videopoker: TitleDashboardData = emptyData({ gamesLabel: 'Hands', streakLabel: 'Win Streak' });

// ===========================================================================
// Lookup map & exported accessor
// ===========================================================================

const titleDataMap: Record<string, TitleDashboardData> = {
  madden26: madden26,
  cfb26: cfb26,
  nba2k26: nba2k26,
  fc26: fc26,
  mlbtheshow26: mlbtheshow26,
  warzone: warzone,
  fortnite: fortnite,
  ufc5: ufc5,
  pga2k25: pga2k25,
  undisputed: undisputed,
  videopoker: videopoker,
};

/**
 * Returns title-specific dashboard data for the given title ID.
 * Falls back to a no-data shell if the title ID is unrecognized.
 */
export function getDashboardDataForTitle(titleId: string): TitleDashboardData {
  return (
    titleDataMap[titleId] ??
    emptyData({ gamesLabel: 'Games', streakLabel: 'Streak' })
  );
}
