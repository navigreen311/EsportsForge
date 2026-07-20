/**
 * mapBackend — translate a backend Madden26 gameplan (rich schema) into the
 * frontend `Play` shape the Gameplan page renders, including the animated-
 * diagram `routes`. Lossy by design: the backend play carries more than the UI
 * needs, and some backend enums (formation names, tags) are wider than the
 * frontend unions — we cast/normalize and drop what doesn't map.
 */

import type {
  Play,
  Formation,
  ConceptTag,
  SituationTag,
  DiagramRoute,
} from '@/types/gameplan';

// -- backend wire shapes (subset we consume) --------------------------------

export interface BackendRoute {
  receiver: string;
  points: number[][];
}

export interface BackendPlay {
  name: string;
  formation: string;
  play_type: string;
  concept: string;
  primary_read: string;
  beats?: string[];
  situation_tags?: string[];
  notes?: string | null;
  routes?: BackendRoute[] | null;
}

export interface BackendGameplan {
  id: string;
  scheme: string;
  plays: BackendPlay[];
  opening_script?: string[];
  confidence: number;
  notes?: string | null;
}

// -- normalization tables ----------------------------------------------------

const PLAY_TYPE_TO_CONCEPT: Record<string, ConceptTag> = {
  run: 'run',
  pass_short: 'quick-pass',
  pass_medium: 'zone-beater',
  pass_deep: 'deep-shot',
  rpo: 'rpo',
  screen: 'screen',
  play_action: 'play-action',
  qb_run: 'run',
};

// Backend uses snake_case + extra tags; map the ones the frontend union knows.
const SITUATION_TAG_MAP: Record<string, SituationTag> = {
  red_zone: 'red-zone',
  goal_line: 'goal-line',
  '3rd_and_short': '3rd-down',
  '3rd_and_medium': '3rd-down',
  '3rd_and_long': '3rd-down',
  anti_blitz: 'anti-blitz',
  shot_play: 'opening-drive',
};

const prettifyBeat = (b: string): string =>
  b
    .replace(/_/g, ' ')
    .replace(/\bcover (\d)\b/i, 'Cover $1')
    .replace(/^\w/, (c) => c.toUpperCase());

const slug = (s: string): string => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

function mapRoutes(routes: BackendRoute[] | null | undefined): DiagramRoute[] | undefined {
  if (!routes || routes.length === 0) return undefined;
  return routes.map((r) => ({
    receiver: r.receiver,
    // backend points are number[][]; the diagram wants [x, y] tuples.
    points: r.points.map((p) => [p[0]!, p[1]!] as [number, number]),
  }));
}

export function mapBackendPlay(p: BackendPlay, index: number, confidence: number): Play {
  const conceptTags: ConceptTag[] = [];
  const c = PLAY_TYPE_TO_CONCEPT[p.play_type];
  if (c) conceptTags.push(c);

  const situationTags: SituationTag[] = [];
  for (const t of p.situation_tags ?? []) {
    const mapped = SITUATION_TAG_MAP[t];
    if (mapped && !situationTags.includes(mapped)) situationTags.push(mapped);
  }

  return {
    id: `be-${index}-${slug(p.name)}`,
    name: p.name,
    formation: p.formation as Formation, // backend names are wider than the union
    conceptTags,
    situationTags,
    confidenceScore: Math.round(confidence * 100),
    isKillSheetPlay: (p.situation_tags ?? []).includes('kill_sheet'),
    description: p.notes || p.primary_read,
    beats: p.beats && p.beats.length > 0 ? prettifyBeat(p.beats[0]!) : undefined,
    routes: mapRoutes(p.routes),
  };
}

export function mapBackendGameplan(gp: BackendGameplan): Play[] {
  return gp.plays.map((p, i) => mapBackendPlay(p, i, gp.confidence));
}
