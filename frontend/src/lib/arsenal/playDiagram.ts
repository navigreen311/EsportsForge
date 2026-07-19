/**
 * playDiagram — turn a Secret Weapon into a top-down football play diagram
 * (formation + routes) that renders client-side, no AnimaForge required.
 *
 * The weapons only carry text (name/category/description), so we match the play
 * to a concept by keyword and lay out a standard shotgun set with the matching
 * routes. Not a perfect playbook — a clear, animated demonstration of the concept.
 *
 * Coordinate space: 0..100 x 0..100. Line of scrimmage at y=60, offense below,
 * routes run UP the field (decreasing y). x grows left→right.
 */

export type Pt = [number, number];

export interface DiagPlayer {
  key: string;
  label: string;
  x: number;
  y: number;
  kind: 'skill' | 'qb' | 'ol';
}

export interface DiagRoute {
  key: string;
  color: string;
  points: Pt[];
}

export interface PlayData {
  title: string;
  formation: string;
  concept: string;
  players: DiagPlayer[];
  routes: DiagRoute[];
}

const LOS = 60;

// Skill spots (shotgun spread).
const SPOT = {
  X: { x: 8, y: LOS },
  SL: { x: 30, y: LOS - 2 },
  TE: { x: 66, y: LOS },
  Z: { x: 92, y: LOS },
  HB: { x: 44, y: LOS + 12 },
  QB: { x: 50, y: LOS + 10 },
} as const;

type SpotKey = keyof typeof SPOT;
type Spot = { x: number; y: number };

const clampX = (x: number) => Math.max(4, Math.min(96, x));
const clampY = (y: number) => Math.max(6, Math.min(94, y));
const toCenter = (x: number) => (x < 50 ? 1 : -1); // horizontal sign toward the middle
const P = (x: number, y: number): Pt => [clampX(x), clampY(y)];

// Route builders — each returns a polyline from the spot upfield.
const ROUTE = {
  go: (p: Spot) => [P(p.x, p.y), P(p.x, 8)],
  seam: (p: Spot) => [P(p.x, p.y), P(p.x + toCenter(p.x) * 4, 10)],
  slant: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 6), P(p.x + toCenter(p.x) * 16, p.y - 16)],
  dig: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 20), P(p.x + toCenter(p.x) * 24, p.y - 20)],
  post: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 18), P(p.x + toCenter(p.x) * 22, p.y - 42)],
  corner: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 18), P(p.x - toCenter(p.x) * 16, p.y - 32)],
  out: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 14), P(p.x - toCenter(p.x) * 15, p.y - 14)],
  flat: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 2), P(p.x - toCenter(p.x) * 16, p.y - 4)],
  drag: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 5), P(p.x + toCenter(p.x) * 42, p.y - 8)],
  curl: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 16), P(p.x, p.y - 12)],
  comeback: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 18), P(p.x - toCenter(p.x) * 5, p.y - 14)],
  wheel: (p: Spot) => [P(p.x, p.y), P(p.x - toCenter(p.x) * 12, p.y - 2), P(p.x - toCenter(p.x) * 16, p.y - 44)],
  checkdown: (p: Spot) => [P(p.x, p.y), P(p.x + toCenter(p.x) * 8, p.y - 1)],
  screen: (p: Spot) => [P(p.x, p.y), P(p.x - toCenter(p.x) * 6, p.y + 2), P(p.x - toCenter(p.x) * 16, p.y - 2)],
  block: (p: Spot) => [P(p.x, p.y), P(p.x, p.y - 2)],
} satisfies Record<string, (p: Spot) => Pt[]>;

type RouteName = keyof typeof ROUTE;
type Assign = Partial<Record<SpotKey, RouteName>>;

// Concept library: keyword → route assignment for the 5 skill spots.
const CONCEPTS: { keys: string[]; concept: string; a: Assign }[] = [
  { keys: ['four vert', '4 vert', 'vertical', 'seam bender'], concept: 'Four Verticals',
    a: { X: 'go', SL: 'seam', TE: 'seam', Z: 'go', HB: 'checkdown' } },
  { keys: ['mesh'], concept: 'Mesh',
    a: { X: 'drag', Z: 'drag', SL: 'corner', TE: 'curl', HB: 'flat' } },
  { keys: ['sail', 'y-sail', 'flood', 'two-deep side'], concept: 'Sail / Flood',
    a: { TE: 'corner', SL: 'out', Z: 'go', X: 'drag', HB: 'flat' } },
  { keys: ['smash', 'corner-flat', 'hole shot', 'bench', 'y-corner'], concept: 'Smash',
    a: { Z: 'corner', SL: 'flat', X: 'slant', TE: 'curl', HB: 'checkdown' } },
  { keys: ['dagger', 'dig-post', 'dig'], concept: 'Dagger',
    a: { SL: 'go', X: 'dig', TE: 'curl', Z: 'comeback', HB: 'checkdown' } },
  { keys: ['slant', 'hot ', 'quick'], concept: 'Quick / Hot',
    a: { X: 'slant', SL: 'slant', Z: 'slant', TE: 'flat', HB: 'checkdown' } },
  { keys: ['wheel'], concept: 'Wheel',
    a: { HB: 'wheel', SL: 'go', X: 'slant', Z: 'comeback', TE: 'flat' } },
  { keys: ['screen'], concept: 'Screen',
    a: { HB: 'screen', X: 'block', Z: 'block', SL: 'flat', TE: 'block' } },
  { keys: ['fade', 'back-shoulder', 'goal-line', 'goal line'], concept: 'Fade',
    a: { X: 'go', Z: 'go', SL: 'slant', TE: 'flat', HB: 'checkdown' } },
  { keys: ['rpo', 'glance', 'bubble'], concept: 'RPO',
    a: { SL: 'slant', X: 'screen', Z: 'slant', TE: 'block', HB: 'checkdown' } },
  { keys: ['boot', 'play-action', 'play action', 'pa '], concept: 'Play-Action Boot',
    a: { TE: 'corner', SL: 'flat', X: 'drag', Z: 'comeback', HB: 'flat' } },
  { keys: ['drive', 'shallow', 'cross'], concept: 'Drive',
    a: { X: 'drag', SL: 'dig', Z: 'comeback', TE: 'curl', HB: 'checkdown' } },
];

const DEFAULT_CONCEPT: Assign = { X: 'go', SL: 'slant', TE: 'corner', Z: 'comeback', HB: 'flat' };

const ROUTE_COLORS: Record<SpotKey, string> = {
  X: '#f97316', SL: '#22d3ee', TE: '#a3e635', Z: '#f472b6', HB: '#fbbf24', QB: '#e5e7eb',
};

export interface WeaponLike {
  name?: string | null;
  category?: string | null;
  play_name?: string | null;
  formation?: string | null;
  description?: string | null;
}

export function weaponToPlay(weapon: WeaponLike): PlayData {
  const text = [weapon.name, weapon.category, weapon.play_name, weapon.description]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();

  const match = CONCEPTS.find((c) => c.keys.some((k) => text.includes(k)));
  const assign: Assign = match ? match.a : DEFAULT_CONCEPT;
  const concept = match ? match.concept : 'Base Concept';

  const skillKeys: SpotKey[] = ['X', 'SL', 'TE', 'Z', 'HB'];
  const players: DiagPlayer[] = [
    { key: 'QB', label: 'QB', x: SPOT.QB.x, y: SPOT.QB.y, kind: 'qb' },
    ...skillKeys.map((k) => ({
      key: k,
      label: k === 'SL' ? 'Y' : k,
      x: SPOT[k].x,
      y: SPOT[k].y,
      kind: 'skill' as const,
    })),
    ...[40, 45, 50, 55, 60].map((x, i) => ({
      key: `OL${i}`,
      label: '',
      x,
      y: LOS + 1,
      kind: 'ol' as const,
    })),
  ];

  const routes: DiagRoute[] = skillKeys
    .map((k): DiagRoute | null => {
      const rn = assign[k];
      if (!rn || rn === 'block') return null;
      return { key: k, color: ROUTE_COLORS[k], points: ROUTE[rn](SPOT[k]) };
    })
    .filter((r): r is DiagRoute => r !== null);

  return {
    title: weapon.name ?? 'Play',
    formation: weapon.formation ?? 'Shotgun',
    concept,
    players,
    routes,
  };
}
