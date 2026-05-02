/**
 * Single source of truth for per-title Arsenal metadata — categories,
 * trigger keys, situation pills, quick-search suggestions. Kept in one
 * place so the page, filters, AI prompts and Discover tab stay in sync.
 */

import type { GameTitle } from '@/lib/store';

/**
 * Canonical Arsenal title IDs (matches backend `TITLE_IDS`).
 * The frontend's UIStore uses different keys (madden26, cfb26, ...),
 * so we expose a mapping in both directions.
 */
export type ArsenalTitleId =
  | 'madden-26'
  | 'cfb-26'
  | 'nba-2k26'
  | 'eafc-26'
  | 'mlb-26'
  | 'warzone'
  | 'fortnite'
  | 'ufc-5'
  | 'pga-2k25'
  | 'undisputed'
  | 'video-poker';

export const TITLE_TO_ARSENAL_ID: Record<GameTitle, ArsenalTitleId> = {
  madden26: 'madden-26',
  cfb26: 'cfb-26',
  nba2k26: 'nba-2k26',
  fc26: 'eafc-26',
  mlbtheshow26: 'mlb-26',
  warzone: 'warzone',
  fortnite: 'fortnite',
  ufc5: 'ufc-5',
  pga2k25: 'pga-2k25',
  undisputed: 'undisputed',
  videopoker: 'video-poker',
};

export const ARSENAL_ID_TO_TITLE: Record<ArsenalTitleId, GameTitle> = Object
  .entries(TITLE_TO_ARSENAL_ID)
  .reduce((acc, [k, v]) => ({ ...acc, [v]: k as GameTitle }), {} as Record<ArsenalTitleId, GameTitle>);

export const TITLE_DISPLAY_NAME: Record<ArsenalTitleId, string> = {
  'madden-26': 'Madden 26',
  'cfb-26': 'CFB 26',
  'nba-2k26': 'NBA 2K26',
  'eafc-26': 'EA FC 26',
  'mlb-26': 'MLB The Show 26',
  warzone: 'Warzone',
  fortnite: 'Fortnite',
  'ufc-5': 'UFC 5',
  'pga-2k25': 'PGA TOUR 2K25',
  undisputed: 'Undisputed',
  'video-poker': 'Video Poker',
};

// ---------------------------------------------------------------------------
// Weapon categories per title
// ---------------------------------------------------------------------------

export const TITLE_WEAPON_CATEGORIES: Record<ArsenalTitleId, string[]> = {
  'madden-26': ['Trick Play', 'Unstoppable Concept', 'Situational', 'Cheese', 'Blitz Package'],
  'cfb-26': ['Trick Play', 'Unstoppable Concept', 'Situational', 'Cheese', 'Blitz Package'],
  'nba-2k26': ['Unstoppable Scorer', 'Cheese Dribble', 'Glitch Move', 'Set Play', 'End-of-Clock'],
  'eafc-26': ['Skill Move Combo', 'Dead Ball Trick', 'Counter Attack', 'Set Piece', 'Cheese Formation'],
  'mlb-26': ['Pitch Sequence', 'Batter Exploit', 'Shift Buster', 'Situational AB', 'Cheese Count'],
  warzone: ['Movement Tech', 'Loadout Exploit', 'Zone Edge', 'Drop Spot', 'Cheese Mechanic'],
  fortnite: ['Edit Speed', 'Build Reset', 'Zone Launch', 'Cheese Build', 'Mechanical Exploit'],
  'ufc-5': ['Submission Setup', 'Strike Exploit', 'Clinch Trick', 'Stamina Drain', 'Cheese Combo'],
  'pga-2k25': ['Wind Exploit', 'Shot Shape', 'Club Trick', 'Putt Line', 'Situational Club'],
  undisputed: ['Punch Exploit', 'Guard Break', 'Combo Ender', 'Stamina Trick', 'Footwork'],
  'video-poker': ['Optimal Hold', 'Variance Play', 'Bonus Trigger', 'Session Strategy'],
};

// ---------------------------------------------------------------------------
// Trigger condition keys per title (used by WeaponDetail rendering)
// ---------------------------------------------------------------------------

export const TITLE_TRIGGER_KEYS: Record<ArsenalTitleId, string[]> = {
  'madden-26': ['down', 'distance', 'fieldPosition', 'quarter', 'scoreMargin', 'opponentTendency', 'consecutiveRuns'],
  'cfb-26': ['down', 'distance', 'fieldPosition', 'quarter', 'scoreMargin', 'opponentTendency', 'consecutiveRuns'],
  'nba-2k26': ['shotClock', 'quarter', 'pointMargin', 'defenderPosition', 'stamina', 'gameMode'],
  'eafc-26': ['possession', 'half', 'scoreline', 'opponentShape', 'pressingIntensity', 'fieldZone'],
  'mlb-26': ['count', 'inning', 'runners', 'outs', 'batterTendency', 'pitcherStamina'],
  warzone: ['circlePhase', 'squadCount', 'height', 'loadout', 'endgamePosition'],
  fortnite: ['storm', 'materials', 'height', 'playerCount', 'buildPhase'],
  'ufc-5': ['round', 'stamina', 'position', 'healthBar', 'distance', 'style'],
  'pga-2k25': ['wind', 'lie', 'distance', 'elevation', 'green', 'pressure'],
  undisputed: ['round', 'stamina', 'guardHealth', 'distance', 'stance', 'momentum'],
  'video-poker': ['hand', 'paytable', 'credits', 'sessionLength'],
};

// ---------------------------------------------------------------------------
// Situation pills per title
// ---------------------------------------------------------------------------

export const TITLE_SITUATIONS: Record<ArsenalTitleId, string[]> = {
  'madden-26': ['Red Zone', '4th Down', '2-Min', 'Comeback'],
  'cfb-26': ['Red Zone', '4th Down', '2-Min', 'Comeback'],
  'nba-2k26': ['End of Clock', 'Tied', 'Crunch Time'],
  'eafc-26': ['Final Third', 'Set Piece', 'Counter', 'Defending Lead'],
  'mlb-26': ['RISP', 'Full Count', '2 Outs', 'Tie Game'],
  warzone: ['Final Circle', '1v1', 'Low Loot', 'Hot Drop'],
  fortnite: ['Box Fight', 'Endgame', 'Build Battle', 'Storm Push'],
  'ufc-5': ['Final Round', 'Low Health', 'Clinch'],
  'pga-2k25': ['Pressure Putt', 'Long Drive', 'Wind Challenge'],
  undisputed: ['Final Round', 'Low Stamina', 'Inside'],
  'video-poker': ['Bonus Hand', 'High Credit', 'Session Start'],
};

// ---------------------------------------------------------------------------
// Quick-search pill suggestions (Discover tab)
// ---------------------------------------------------------------------------

export const TITLE_QUICK_SEARCHES: Record<ArsenalTitleId, string[]> = {
  'madden-26': [
    'Madden 26 unstoppable plays',
    'Best trick plays patch X',
    'Red zone cheese',
    '4th down fake plays',
    'Unblockable blitz',
  ],
  'cfb-26': [
    'CFB 26 unstoppable plays',
    'Best trick plays CFB 26',
    'Option offense exploits',
    'Triple option fake pitch',
  ],
  'nba-2k26': [
    '2K26 cheese dribbles',
    'Unstoppable moves 2K26',
    'Best post moves 2K26',
    'Unguardable shots',
    'Cheese plays 2K',
  ],
  'eafc-26': [
    'FC 26 skill moves',
    'Best dead ball tricks FC26',
    'Unstoppable set pieces',
    'Cheese formations FC26',
  ],
  'mlb-26': [
    'The Show 26 pitch sequences',
    'Best hitting cheese',
    'Strikeout pitches Show 26',
    'PCI cheese Show 26',
  ],
  warzone: [
    'Warzone movement tech',
    'Best loadout Warzone Season X',
    'Warzone cheese spots',
    'Unstoppable Warzone strats',
  ],
  fortnite: [
    'Fortnite edit courses',
    'Best build resets',
    'Unstoppable box fights',
    'Zone launch tricks',
  ],
  'ufc-5': [
    'UFC 5 cheese submissions',
    'Unstoppable combos UFC 5',
    'Best striking combos UFC 5',
    'Exploit UFC 5',
  ],
  'pga-2k25': [
    'PGA 2K25 wind exploit',
    'Best shot shapes 2K25',
    'Putting trick 2K25',
    'Scoring trick PGA 2K',
  ],
  undisputed: [
    'Undisputed cheese combos',
    'Best jabs Undisputed',
    'Undisputed exploit',
    'Unstoppable punch sequences',
  ],
  'video-poker': [
    'Video poker strategy Jacks or Better',
    'Best video poker holds',
    'Optimal video poker strategy',
  ],
};

export const ALL_ARSENAL_TITLES: ArsenalTitleId[] = Object.keys(
  TITLE_DISPLAY_NAME
) as ArsenalTitleId[];
