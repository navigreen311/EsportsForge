// ---------------------------------------------------------------------------
// Title roster – pure data module (no React, no "use client")
// ---------------------------------------------------------------------------

export type TitleCategory =
  | 'football'
  | 'sports'
  | 'fps'
  | 'combat'
  | 'precision'
  | 'card';

export interface FullTitle {
  id: string;
  name: string;
  shortName: string;
  category: TitleCategory;
  icon: string;
  color: string;
  requiredTier: 'free' | 'competitive' | 'elite';
}

// ---- Full 11-title roster -------------------------------------------------

export const FULL_TITLE_LIST: FullTitle[] = [
  { id: 'madden26',     name: 'Madden NFL 26',                shortName: 'Madden 26',    category: 'football',  icon: '\u{1F3C8}', color: '#4ADE80', requiredTier: 'free' },
  { id: 'cfb26',        name: 'EA Sports College Football 26', shortName: 'CFB 26',       category: 'football',  icon: '\u{1F393}', color: '#4ADE80', requiredTier: 'free' },
  { id: 'nba2k26',      name: 'NBA 2K26',                     shortName: 'NBA 2K26',     category: 'sports',    icon: '\u{1F3C0}', color: '#F97316', requiredTier: 'competitive' },
  { id: 'fc26',         name: 'EA Sports FC 26',              shortName: 'EA FC 26',     category: 'sports',    icon: '\u26BD',     color: '#3B82F6', requiredTier: 'competitive' },
  { id: 'mlbtheshow26', name: 'MLB The Show 26',              shortName: 'MLB 26',       category: 'sports',    icon: '\u26BE',     color: '#EF4444', requiredTier: 'competitive' },
  { id: 'warzone',      name: 'Call of Duty: Warzone',        shortName: 'Warzone',      category: 'fps',       icon: '\u{1F3AF}', color: '#6B7280', requiredTier: 'competitive' },
  { id: 'fortnite',     name: 'Fortnite',                     shortName: 'Fortnite',     category: 'fps',       icon: '\u26A1',     color: '#A855F7', requiredTier: 'competitive' },
  { id: 'ufc5',         name: 'UFC 5',                        shortName: 'UFC 5',        category: 'combat',    icon: '\u{1F94A}', color: '#DC2626', requiredTier: 'elite' },
  { id: 'pga2k25',      name: 'PGA TOUR 2K25',                shortName: 'PGA 2K25',     category: 'precision', icon: '\u26F3',     color: '#16A34A', requiredTier: 'elite' },
  { id: 'undisputed',   name: 'Undisputed',                   shortName: 'Undisputed',   category: 'combat',    icon: '\u{1F94A}', color: '#7C3AED', requiredTier: 'elite' },
  { id: 'videopoker',   name: 'Video Poker',                  shortName: 'Video Poker',  category: 'card',      icon: '\u{1F0CF}', color: '#D97706', requiredTier: 'elite' },
];

// ---- Category helpers -----------------------------------------------------

export const CATEGORY_ORDER: TitleCategory[] = [
  'football',
  'sports',
  'fps',
  'combat',
  'precision',
  'card',
];

export const CATEGORY_LABELS: Record<TitleCategory, string> = {
  football:  'Football',
  sports:    'Sports',
  fps:       'FPS / Battle Royale',
  combat:    'Combat',
  precision: 'Precision',
  card:      'Card',
};

/** Display labels for required tier names. */
export const TIER_REQUIRED: Record<string, string> = {
  free: 'Free',
  competitive: 'Competitive',
  elite: 'Elite',
  team: 'Team',
};

// ---- Tier helpers ---------------------------------------------------------

export const TIER_HIERARCHY: Record<string, number> = {
  free:        0,
  competitive: 1,
  elite:       2,
  team:        3,
};

/**
 * Returns `true` when the user's tier is high enough to unlock a title.
 */
export function isTitleUnlocked(requiredTier: string, userTier: string): boolean {
  const required = TIER_HIERARCHY[requiredTier] ?? Infinity;
  const user = TIER_HIERARCHY[userTier] ?? -1;
  return user >= required;
}

/**
 * Look up a title by its unique `id`.
 */
export function getTitleById(id: string): FullTitle | undefined {
  return FULL_TITLE_LIST.find((t) => t.id === id);
}
