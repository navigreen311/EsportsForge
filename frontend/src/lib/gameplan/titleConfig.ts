/**
 * Per-title gameplan terminology + tab labels. The Gameplan page reads
 * the config for the active title so the UI uses native vocabulary
 * (sets vs plays, shape vs formation, finishers vs kill sheet, etc.).
 *
 * Title IDs mirror lib/titles.ts FULL_TITLE_LIST.
 */

export type GameplanTabKey =
  | 'all'
  | 'kill-sheet'
  | 'red-zone'
  | 'anti-blitz'
  | '2-min-drill'
  | 'script'
  | 'arsenal';

export interface TitleGameplanConfig {
  playLabel: string; // "plays" | "sets" | "tactics" | …
  formationLabel: string; // "Formation" | "Set" | "Shape" | …
  evidenceLabel: string;
  tabLabels: Partial<Record<GameplanTabKey, string>>;
}

const FOOTBALL_LABELS: Partial<Record<GameplanTabKey, string>> = {
  'all': 'All Plays',
  'kill-sheet': 'Kill Sheet',
  'red-zone': 'Red Zone',
  'anti-blitz': 'Anti-Blitz',
  '2-min-drill': '2-Min Drill',
  'script': 'Script View',
  'arsenal': '⚡ Arsenal',
};

const DEFAULT_CONFIG: TitleGameplanConfig = {
  playLabel: 'plays',
  formationLabel: 'Formation',
  evidenceLabel: 'Why this beats their look',
  tabLabels: FOOTBALL_LABELS,
};

const CONFIG: Record<string, TitleGameplanConfig> = {
  madden26: {
    playLabel: 'plays',
    formationLabel: 'Formation',
    evidenceLabel: 'Why this beats their scheme',
    tabLabels: FOOTBALL_LABELS,
  },
  cfb26: {
    playLabel: 'plays',
    formationLabel: 'Formation',
    evidenceLabel: 'Why this beats their scheme',
    tabLabels: FOOTBALL_LABELS,
  },
  nba2k26: {
    playLabel: 'sets',
    formationLabel: 'Set',
    evidenceLabel: 'Why this scores on their defense',
    tabLabels: {
      'all': 'All Sets',
      'kill-sheet': 'Closers',
      'red-zone': 'Clutch Plays',
      'anti-blitz': 'Zone Busters',
      '2-min-drill': 'End of Clock',
      'script': 'Opening Sets',
      'arsenal': '⚡ Arsenal',
    },
  },
  fc26: {
    playLabel: 'plays',
    formationLabel: 'Shape',
    evidenceLabel: 'Why this breaks their defensive shape',
    tabLabels: {
      'all': 'All Plays',
      'kill-sheet': 'Finishers',
      'red-zone': 'Final Third',
      'anti-blitz': 'Counter Plays',
      '2-min-drill': 'Game-State',
      'script': 'Opening Phase',
      'arsenal': '⚡ Arsenal',
    },
  },
  mlbtheshow26: {
    playLabel: 'pitches',
    formationLabel: 'Set',
    evidenceLabel: 'Why this beats their swing decisions',
    tabLabels: {
      'all': 'All Pitches',
      'kill-sheet': 'Putaway',
      'red-zone': 'RISP',
      'anti-blitz': 'High Leverage',
      '2-min-drill': 'Save Situation',
      'script': 'Inning Plan',
      'arsenal': '⚡ Arsenal',
    },
  },
  warzone: {
    playLabel: 'tactics',
    formationLabel: 'Setup',
    evidenceLabel: 'Why this wins this situation',
    tabLabels: {
      'all': 'All Tactics',
      'kill-sheet': 'Loadouts',
      'red-zone': 'Endgame',
      'anti-blitz': 'Rotations',
      '2-min-drill': 'Clutch Plays',
      'script': 'Game Script',
      'arsenal': '⚡ Arsenal',
    },
  },
  fortnite: {
    playLabel: 'tactics',
    formationLabel: 'Setup',
    evidenceLabel: 'Why this wins this fight',
    tabLabels: {
      'all': 'All Tactics',
      'kill-sheet': 'Box Fights',
      'red-zone': 'Endgame',
      'anti-blitz': 'Resets',
      '2-min-drill': 'Clutch',
      'script': 'Drop Plan',
      'arsenal': '⚡ Arsenal',
    },
  },
  ufc5: {
    playLabel: 'combos',
    formationLabel: 'Stance',
    evidenceLabel: 'Why this works against their style',
    tabLabels: {
      'all': 'All Combos',
      'kill-sheet': 'Finishers',
      'red-zone': 'Clinch Work',
      'anti-blitz': 'Counter Strikes',
      '2-min-drill': 'Closing Round',
      'script': 'Round Plan',
      'arsenal': '⚡ Arsenal',
    },
  },
  pga2k25: {
    playLabel: 'shots',
    formationLabel: 'Lie',
    evidenceLabel: 'Why this scores on this hole',
    tabLabels: {
      'all': 'All Shots',
      'kill-sheet': 'Birdie Looks',
      'red-zone': 'Inside 100',
      'anti-blitz': 'Wind Plays',
      '2-min-drill': 'Save Game',
      'script': 'Round Plan',
      'arsenal': '⚡ Arsenal',
    },
  },
  undisputed: {
    playLabel: 'combos',
    formationLabel: 'Stance',
    evidenceLabel: 'Why this beats their guard',
    tabLabels: {
      'all': 'All Combos',
      'kill-sheet': 'KO Sequences',
      'red-zone': 'Closing Rounds',
      'anti-blitz': 'Counter Punches',
      '2-min-drill': 'Last Round',
      'script': 'Round Plan',
      'arsenal': '⚡ Arsenal',
    },
  },
  videopoker: {
    playLabel: 'holds',
    formationLabel: 'Hand',
    evidenceLabel: 'Why this is the optimal hold',
    tabLabels: {
      'all': 'All Holds',
      'kill-sheet': 'Top EV',
      'red-zone': 'Bonus Setups',
      'anti-blitz': 'Variance Plays',
      '2-min-drill': 'Session End',
      'script': 'Strategy',
      'arsenal': '⚡ Arsenal',
    },
  },
};

export function getTitleGameplanConfig(titleId: string): TitleGameplanConfig {
  return CONFIG[titleId] ?? DEFAULT_CONFIG;
}
