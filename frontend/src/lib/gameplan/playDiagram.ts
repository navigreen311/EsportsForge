/**
 * gameplan/playDiagram — resolve a gameplan `Play` into renderable diagram data
 * (players + route polylines), with a graceful degradation chain:
 *
 *   1. EXPLICIT   — the play carries validated `routes` (Phase 2: LLM-generated,
 *                   server-validated coordinates). Rendered faithfully.
 *   2. TEMPLATE   — no explicit routes → derive a concept approximation from the
 *                   play's name + tags via the existing arsenal engine
 *                   (`weaponToPlay`). Recognizable as the concept, NOT the exact
 *                   Madden play.
 *   3. FORMATION  — the template produced no routes (e.g. a pure run) → show the
 *                   formation with players but no routes.
 *
 * If even that fails, `resolvePlayDiagram` returns null and the caller falls
 * back to the play's text description.
 *
 * Coordinate space matches `lib/arsenal/playDiagram`: 0–100 × 0–100, LOS at
 * y=60, offense below, routes run up (decreasing y).
 */

import {
  weaponToPlay,
  type PlayData,
  type DiagPlayer,
  type DiagRoute,
  type Pt,
} from '@/lib/arsenal/playDiagram';
import type { Play, DiagramRoute } from '@/types/gameplan';

const LOS = 60;

/** Where explicit-route diagrams get their non-receiver players from. */
const QB_SPOT: Pt = [50, 70];
const OL_XS = [40, 45, 50, 55, 60];

/** Cycle these for explicit routes (arsenal uses per-spot colors; explicit
 *  routes are keyed by arbitrary receiver labels, so we cycle instead). */
const EXPLICIT_COLORS = ['#f97316', '#22d3ee', '#a3e635', '#f472b6', '#fbbf24', '#818cf8'];

export type DiagramSource = 'explicit' | 'template' | 'formation';

export interface ResolvedDiagram {
  data: PlayData;
  source: DiagramSource;
}

const isFiniteNum = (n: unknown): n is number =>
  typeof n === 'number' && Number.isFinite(n);
const clamp = (n: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, n));

/**
 * Validate + clean explicit routes. Returns a clamped copy when structurally
 * sound, or null to trigger the template fallback. This is the guard that makes
 * the Phase-2 LLM path safe: garbage geometry falls back instead of rendering.
 */
export function validateExplicitRoutes(
  routes: DiagramRoute[] | undefined,
): DiagramRoute[] | null {
  if (!Array.isArray(routes) || routes.length === 0) return null;

  const cleaned: DiagramRoute[] = [];
  for (const r of routes) {
    if (!r || typeof r.receiver !== 'string' || !r.receiver.trim()) return null;
    if (!Array.isArray(r.points) || r.points.length < 2) return null;

    const pts: Pt[] = [];
    for (const p of r.points) {
      if (!Array.isArray(p) || p.length < 2) return null;
      const [x, y] = p;
      if (!isFiniteNum(x) || !isFiniteNum(y)) return null;
      pts.push([clamp(x, 0, 100), clamp(y, 0, 100)]);
    }

    // Sanity: the receiver should start at/near the LOS or in the backfield
    // (offense side), not already downfield. A start well above the LOS means
    // the coordinates are almost certainly bad — bail to the template.
    const startY = pts[0]![1];
    if (startY < LOS - 8) return null;

    // Reject a degenerate (zero-extent) path — nothing to animate.
    const moved = pts.some((p) => Math.abs(p[0] - pts[0]![0]) > 1 || Math.abs(p[1] - pts[0]![1]) > 1);
    if (!moved) return null;

    cleaned.push({ receiver: r.receiver.trim(), points: pts });
  }
  return cleaned;
}

function buildFromExplicit(play: Play, routes: DiagramRoute[]): PlayData {
  const players: DiagPlayer[] = [
    { key: 'QB', label: 'QB', x: QB_SPOT[0], y: QB_SPOT[1], kind: 'qb' },
    ...OL_XS.map((x, i) => ({ key: `OL${i}`, label: '', x, y: LOS + 1, kind: 'ol' as const })),
    ...routes.map((r) => ({
      key: r.receiver,
      label: r.receiver === 'SL' ? 'Y' : r.receiver,
      x: r.points[0]![0],
      y: r.points[0]![1],
      kind: 'skill' as const,
    })),
  ];

  const diagRoutes: DiagRoute[] = routes.map((r, i) => ({
    key: r.receiver,
    color: EXPLICIT_COLORS[i % EXPLICIT_COLORS.length]!,
    points: r.points,
  }));

  return {
    title: play.name,
    formation: play.formation,
    concept: play.conceptTags[0] ?? 'Play',
    players,
    routes: diagRoutes,
  };
}

/**
 * Resolve a Play into a renderable diagram. Never throws; returns null only if
 * nothing renderable could be produced (in practice the template path always
 * yields at least a formation).
 */
export function resolvePlayDiagram(play: Play): ResolvedDiagram | null {
  try {
    // 1. Explicit routes (Phase 2 data path) — validate then render faithfully.
    const explicit = validateExplicitRoutes(play.routes);
    if (explicit) {
      return { data: buildFromExplicit(play, explicit), source: 'explicit' };
    }

    // 2/3. Template concept approximation via the arsenal engine. Feed it the
    // play's text so it keyword-matches a concept; tags widen the match.
    const data = weaponToPlay({
      name: play.name,
      category: play.conceptTags.join(' '),
      formation: play.formation,
      description: play.description,
    });
    // Preserve the gameplan formation label rather than the engine's fallback.
    data.formation = play.formation;

    return {
      data,
      source: data.routes.length > 0 ? 'template' : 'formation',
    };
  } catch {
    return null;
  }
}
