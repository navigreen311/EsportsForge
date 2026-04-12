// ---------------------------------------------------------------------------
// Title-specific data — priorities, drills, plays, and first-install info
// for all 11 supported titles in EsportsForge.
// ---------------------------------------------------------------------------

export interface Priority {
  name: string;
  score: number;
  category: string;
}

export interface Drill {
  name: string;
  type: string;
  irScore: number;
  estimatedMinutes: number;
}

export interface Play {
  name: string;
  formation: string;
  type: string;
  confidence: number;
}

export interface TitleData {
  id: string;
  name: string;
  icon: string;
  priorities: Priority[];
  drills: Drill[];
  plays: Play[];
  firstInstall: string;
}

export const TITLES: Record<string, TitleData> = {
  // ═══════════════════════════════════════════════════════════════════════════
  // Football
  // ═══════════════════════════════════════════════════════════════════════════

  madden26: {
    id: "madden26",
    name: "Madden 26",
    icon: "\u{1F3C8}",
    priorities: [
      { name: "Pre-Snap Coverage ID", score: 9.4, category: "reads" },
      { name: "Red Zone Efficiency", score: 8.7, category: "situational" },
      { name: "4th Down Decisions", score: 8.1, category: "situational" },
    ],
    drills: [
      { name: "Coverage Shell Recognition", type: "reads", irScore: 9.2, estimatedMinutes: 8 },
      { name: "Hot Route Audible Speed", type: "execution", irScore: 8.5, estimatedMinutes: 6 },
      { name: "Red Zone Fade Timing", type: "situational", irScore: 8.0, estimatedMinutes: 10 },
    ],
    plays: [
      { name: "Gun Spread Y-Flex — Mesh Post", formation: "Gun Spread", type: "pass", confidence: 0.91 },
      { name: "Singleback Ace — HB Dive", formation: "Singleback Ace", type: "run", confidence: 0.87 },
      { name: "Shotgun Trips TE — Corner Strike", formation: "Shotgun Trips TE", type: "pass", confidence: 0.84 },
      { name: "I-Form Close — Power O", formation: "I-Form Close", type: "run", confidence: 0.82 },
      { name: "Gun Bunch — Drive Concept", formation: "Gun Bunch", type: "pass", confidence: 0.79 },
    ],
    firstInstall: "Base Spread Offense",
  },

  cfb26: {
    id: "cfb26",
    name: "College Football 26",
    icon: "\u{1F3DF}\u{FE0F}",
    priorities: [
      { name: "RPO Read Timing", score: 9.1, category: "reads" },
      { name: "Tempo Management", score: 8.5, category: "situational" },
      { name: "Option Mesh Point Discipline", score: 8.0, category: "execution" },
    ],
    drills: [
      { name: "RPO Give/Pull Decision", type: "reads", irScore: 9.0, estimatedMinutes: 7 },
      { name: "No-Huddle Tempo Drill", type: "execution", irScore: 8.3, estimatedMinutes: 5 },
      { name: "Zone Read Mesh Timing", type: "execution", irScore: 8.1, estimatedMinutes: 8 },
    ],
    plays: [
      { name: "Spread RPO — Bubble Screen", formation: "Spread", type: "rpo", confidence: 0.90 },
      { name: "Pistol — Zone Read", formation: "Pistol", type: "run", confidence: 0.88 },
      { name: "Empty 5-Wide — Slant Flat", formation: "Empty", type: "pass", confidence: 0.85 },
      { name: "Trips Right — RPO Power Read", formation: "Trips", type: "rpo", confidence: 0.83 },
      { name: "Shotgun Split — QB Draw", formation: "Shotgun Split", type: "run", confidence: 0.80 },
    ],
    firstInstall: "Base Spread RPO",
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Sports
  // ═══════════════════════════════════════════════════════════════════════════

  nba2k26: {
    id: "nba2k26",
    name: "NBA 2K26",
    icon: "\u{1F3C0}",
    priorities: [
      { name: "Shot Timing Consistency", score: 9.3, category: "execution" },
      { name: "Pick & Roll Defense", score: 8.8, category: "defense" },
      { name: "Dribble Package Mastery", score: 8.4, category: "offense" },
    ],
    drills: [
      { name: "Green Window Timing Lab", type: "execution", irScore: 9.1, estimatedMinutes: 10 },
      { name: "Hedge & Recover PnR Defense", type: "defense", irScore: 8.6, estimatedMinutes: 8 },
      { name: "Dribble Chain Combos", type: "offense", irScore: 8.2, estimatedMinutes: 7 },
    ],
    plays: [
      { name: "5-Out — PnR High", formation: "5-Out", type: "offense", confidence: 0.92 },
      { name: "Fist 15 Horns — Flare Screen", formation: "Horns", type: "offense", confidence: 0.88 },
      { name: "Quick Isolation — Post Fade", formation: "Isolation", type: "offense", confidence: 0.85 },
      { name: "2-3 Zone — Trap Wing", formation: "2-3 Zone", type: "defense", confidence: 0.83 },
      { name: "Motion 21 Delay — Kick Out 3", formation: "Motion", type: "offense", confidence: 0.81 },
    ],
    firstInstall: "5-Out Motion Offense",
  },

  eafc26: {
    id: "eafc26",
    name: "EA FC 26",
    icon: "\u26BD",
    priorities: [
      { name: "Manual Defending Discipline", score: 9.2, category: "defense" },
      { name: "Skill Move Efficiency", score: 8.6, category: "offense" },
      { name: "Tactical Switching Speed", score: 8.3, category: "defense" },
    ],
    drills: [
      { name: "Jockey Timing & Contain", type: "defense", irScore: 9.0, estimatedMinutes: 8 },
      { name: "Skill Move Cancel Chains", type: "offense", irScore: 8.4, estimatedMinutes: 7 },
      { name: "Right-Stick Switching Lab", type: "defense", irScore: 8.1, estimatedMinutes: 6 },
    ],
    plays: [
      { name: "4-2-3-1 Wide — Build-Up Play", formation: "4-2-3-1 Wide", type: "attacking", confidence: 0.91 },
      { name: "4-3-2-1 — Counter Attack", formation: "4-3-2-1", type: "attacking", confidence: 0.87 },
      { name: "4-1-2-1-2(2) — Possession", formation: "4-1-2-1-2(2)", type: "balanced", confidence: 0.84 },
      { name: "3-5-2 — Wing Overload", formation: "3-5-2", type: "attacking", confidence: 0.82 },
      { name: "4-4-2 Flat — Press High", formation: "4-4-2", type: "defensive", confidence: 0.79 },
    ],
    firstInstall: "Balanced 4-2-3-1 Build-Up",
  },

  mlb26: {
    id: "mlb26",
    name: "MLB 26",
    icon: "\u26BE",
    priorities: [
      { name: "Pitch Recognition Speed", score: 9.5, category: "reads" },
      { name: "Zone Discipline", score: 8.9, category: "patience" },
      { name: "Breaking Ball Timing", score: 8.2, category: "execution" },
    ],
    drills: [
      { name: "Fastball vs Offspeed ID", type: "reads", irScore: 9.3, estimatedMinutes: 10 },
      { name: "Zone Patience Trainer", type: "patience", irScore: 8.7, estimatedMinutes: 8 },
      { name: "Slider Recognition Lab", type: "execution", irScore: 8.0, estimatedMinutes: 9 },
    ],
    plays: [
      { name: "Sit Fastball — Adjust Down", formation: "Standard", type: "hitting", confidence: 0.93 },
      { name: "Two-Strike Approach — Shorten Up", formation: "Choke Up", type: "hitting", confidence: 0.89 },
      { name: "Bunt & Run — Runners On", formation: "Sacrifice", type: "baserunning", confidence: 0.84 },
      { name: "Pitch Sequence — 4-Seam Setup", formation: "Wind-Up", type: "pitching", confidence: 0.87 },
      { name: "Cut Fastball Tunnel — Backdoor", formation: "Stretch", type: "pitching", confidence: 0.82 },
    ],
    firstInstall: "Balanced Plate Approach",
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // FPS / Battle Royale
  // ═══════════════════════════════════════════════════════════════════════════

  warzone: {
    id: "warzone",
    name: "Warzone",
    icon: "\u{1F3AF}",
    priorities: [
      { name: "First Bullet Accuracy", score: 9.4, category: "gunplay" },
      { name: "Zone Rotation Timing", score: 8.8, category: "positioning" },
      { name: "Loadout Optimization", score: 8.3, category: "strategy" },
    ],
    drills: [
      { name: "Flick-Aim Reflex Drill", type: "gunplay", irScore: 9.2, estimatedMinutes: 6 },
      { name: "Circle Collapse Rotation Sim", type: "positioning", irScore: 8.5, estimatedMinutes: 10 },
      { name: "Recoil Pattern Mastery", type: "gunplay", irScore: 8.1, estimatedMinutes: 7 },
    ],
    plays: [
      { name: "Power Position Hold — High Ground", formation: "Trio", type: "positioning", confidence: 0.90 },
      { name: "Aggressive Push — Slide Cancel Entry", formation: "Duo", type: "aggression", confidence: 0.86 },
      { name: "Buy Station Priority Route", formation: "Squad", type: "economy", confidence: 0.83 },
      { name: "Gatekeep — Edge Rotation", formation: "Trio", type: "positioning", confidence: 0.81 },
      { name: "Bounty Hunt — UAV Chain", formation: "Duo", type: "aggression", confidence: 0.78 },
    ],
    firstInstall: "Zone Control Rotation",
  },

  fortnite: {
    id: "fortnite",
    name: "Fortnite",
    icon: "\u{1F3D7}\u{FE0F}",
    priorities: [
      { name: "Edit Speed Consistency", score: 9.3, category: "building" },
      { name: "Zone Rotation Discipline", score: 8.7, category: "positioning" },
      { name: "Box Fight Decision Speed", score: 8.4, category: "combat" },
    ],
    drills: [
      { name: "Triple-Edit Reset Lab", type: "building", irScore: 9.1, estimatedMinutes: 8 },
      { name: "Zone Tarping Practice", type: "positioning", irScore: 8.5, estimatedMinutes: 10 },
      { name: "Right-Hand Peek Drill", type: "combat", irScore: 8.2, estimatedMinutes: 6 },
    ],
    plays: [
      { name: "Piece Control — Double Edit Take", formation: "Solo", type: "building", confidence: 0.91 },
      { name: "Tarp Rotate — Layer Rush", formation: "Duo", type: "positioning", confidence: 0.87 },
      { name: "Box Fight — Edit Pump Reset", formation: "Solo", type: "combat", confidence: 0.85 },
      { name: "Height Retake — Crank 90s", formation: "Solo", type: "building", confidence: 0.83 },
      { name: "Surge Tag — Storm Edge Poke", formation: "Trio", type: "positioning", confidence: 0.80 },
    ],
    firstInstall: "Piece Control Fundamentals",
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Combat
  // ═══════════════════════════════════════════════════════════════════════════

  ufc5: {
    id: "ufc5",
    name: "UFC 5",
    icon: "\u{1F94A}",
    priorities: [
      { name: "Stamina Economy", score: 9.2, category: "resource" },
      { name: "Takedown Defense Timing", score: 8.8, category: "defense" },
      { name: "Combo EV Discipline", score: 8.3, category: "offense" },
    ],
    drills: [
      { name: "Stamina Burn Rate Analysis", type: "resource", irScore: 9.0, estimatedMinutes: 7 },
      { name: "Sprawl Timing Reaction Lab", type: "defense", irScore: 8.6, estimatedMinutes: 8 },
      { name: "3-Hit Combo EV Calculator", type: "offense", irScore: 8.1, estimatedMinutes: 6 },
    ],
    plays: [
      { name: "Jab-Cross-Hook — Distance Reset", formation: "Orthodox", type: "striking", confidence: 0.90 },
      { name: "Check Low Kick — Counter Overhand", formation: "Southpaw", type: "counter", confidence: 0.87 },
      { name: "Level Change Feint — Uppercut", formation: "Orthodox", type: "striking", confidence: 0.84 },
      { name: "Clinch Knee — Dirty Boxing", formation: "Clinch", type: "grappling", confidence: 0.81 },
      { name: "Sprawl to Guillotine", formation: "Defensive", type: "submission", confidence: 0.78 },
    ],
    firstInstall: "Fundamentals Striking Package",
  },

  undisputed: {
    id: "undisputed",
    name: "Undisputed",
    icon: "\u{1F94B}",
    priorities: [
      { name: "Punch Economy Discipline", score: 9.1, category: "resource" },
      { name: "Footwork Efficiency", score: 8.7, category: "movement" },
      { name: "Guard Break Timing", score: 8.2, category: "offense" },
    ],
    drills: [
      { name: "Punch Output vs Accuracy Balancer", type: "resource", irScore: 8.9, estimatedMinutes: 7 },
      { name: "Ring Cut Footwork Drill", type: "movement", irScore: 8.5, estimatedMinutes: 8 },
      { name: "Guard Break Setup Combos", type: "offense", irScore: 8.0, estimatedMinutes: 6 },
    ],
    plays: [
      { name: "Jab-Jab-Cross — Angle Out", formation: "Orthodox", type: "combination", confidence: 0.91 },
      { name: "Body Work — Hook Upstairs", formation: "Orthodox", type: "combination", confidence: 0.87 },
      { name: "Philly Shell Counter", formation: "Philly Shell", type: "counter", confidence: 0.84 },
      { name: "Clinch Break — Short Uppercut", formation: "Clinch", type: "infighting", confidence: 0.81 },
      { name: "Feint Low — Overhand Right", formation: "Southpaw", type: "power", confidence: 0.79 },
    ],
    firstInstall: "Orthodox Fundamentals",
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Precision
  // ═══════════════════════════════════════════════════════════════════════════

  pga2k25: {
    id: "pga2k25",
    name: "PGA 2K25",
    icon: "\u26F3",
    priorities: [
      { name: "Swing Tempo Consistency", score: 9.3, category: "execution" },
      { name: "Putting Read Accuracy", score: 8.9, category: "reads" },
      { name: "Wind Adjustment", score: 8.4, category: "strategy" },
    ],
    drills: [
      { name: "Tempo Meter Consistency Lab", type: "execution", irScore: 9.1, estimatedMinutes: 10 },
      { name: "Green Reading Practice", type: "reads", irScore: 8.7, estimatedMinutes: 8 },
      { name: "Crosswind Compensation Drill", type: "strategy", irScore: 8.2, estimatedMinutes: 7 },
    ],
    plays: [
      { name: "Draw Off Tee — Fairway Finder", formation: "Tee Box", type: "driving", confidence: 0.92 },
      { name: "Approach — Pin-High Landing", formation: "Fairway", type: "approach", confidence: 0.88 },
      { name: "Flop Shot — Short-Sided Pin", formation: "Greenside", type: "short_game", confidence: 0.84 },
      { name: "Lag Putt — 30ft+ Distance Control", formation: "Green", type: "putting", confidence: 0.86 },
      { name: "Punch Out — Recovery Shot", formation: "Trouble", type: "recovery", confidence: 0.80 },
    ],
    firstInstall: "Course Management Basics",
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Card
  // ═══════════════════════════════════════════════════════════════════════════

  videoPoker: {
    id: "videoPoker",
    name: "Video Poker",
    icon: "\u{1F0CF}",
    priorities: [
      { name: "Strategy Deviation Rate", score: 9.5, category: "discipline" },
      { name: "Session Discipline", score: 8.8, category: "bankroll" },
      { name: "Pay Table Selection", score: 8.3, category: "strategy" },
    ],
    drills: [
      { name: "Optimal Hold Trainer", type: "discipline", irScore: 9.3, estimatedMinutes: 12 },
      { name: "Session Stop-Loss Drill", type: "bankroll", irScore: 8.6, estimatedMinutes: 5 },
      { name: "Pay Table Comparison Lab", type: "strategy", irScore: 8.1, estimatedMinutes: 8 },
    ],
    plays: [
      { name: "Jacks or Better — Full Pay 9/6", formation: "Standard", type: "game_selection", confidence: 0.94 },
      { name: "Deuces Wild — Optimal Hold", formation: "Standard", type: "strategy", confidence: 0.90 },
      { name: "Double Bonus — High Pair Priority", formation: "Standard", type: "strategy", confidence: 0.86 },
      { name: "Session Budget — 200x Bet Bankroll", formation: "Bankroll", type: "money_management", confidence: 0.88 },
      { name: "Variance Check — Royal Flush Chase", formation: "Advanced", type: "risk_assessment", confidence: 0.82 },
    ],
    firstInstall: "Jacks or Better Optimal Strategy",
  },
};

/** Get title data by id. Returns undefined if not found. */
export function getTitleData(titleId: string): TitleData | undefined {
  return TITLES[titleId];
}

/** Get all title IDs. */
export function getAllTitleIds(): string[] {
  return Object.keys(TITLES);
}
