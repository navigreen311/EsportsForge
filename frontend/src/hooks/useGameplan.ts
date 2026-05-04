'use client';

/**
 * useGameplan — owns opponent list, selection, generation lifecycle, and the
 * structured gameplan returned by GameplanAI.
 *
 * Generated state shape comes from the backend /gameplans/generate response.
 * Mock fallbacks remain so the UI renders before the first generate, and so
 * the page survives backend outages without crashing.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useUIStore } from '@/lib/store';
import {
  generateGameplan as generateGameplanApi,
  listOpponents,
  type OpponentSummaryDTO,
} from '@/lib/api/gameplan';
import type {
  Gameplan,
  KillSheetEntry,
  MetaStatus,
  OpponentSummary,
  PackageHealth,
  PackageTab,
  Play,
  ScriptViewEntry,
  TwoMinDrillEntry,
} from '@/types/gameplan';

// ---------------------------------------------------------------------------
// Helpers — map AI plays → frontend Play type so existing components work
// ---------------------------------------------------------------------------

interface AIPlay {
  id: string;
  rank: number;
  name: string;
  formation: string;
  tags?: string[];
  confidence: number;
  impactScore?: number;
  masteryLevel?: string;
  executionRate?: number;
  isTrendingCountered?: boolean;
  isKillSheetPlay?: boolean;
  whenToCall?: string;
  conceptBreakdown?: string;
  evidence?: Play['evidence'];
  proofAIConfidence?: number;
  callStructure?: Play['callStructure'];
  metaStatus?: string;
  patchVersion?: string;
}

function mapPlay(p: AIPlay): Play {
  const tags = p.tags ?? [];
  return {
    id: p.id,
    name: p.name,
    formation: p.formation,
    conceptTags: tags,
    situationTags: tags.filter((t) =>
      ['red-zone', 'goal-line', '3rd-down', '2-minute', 'opening-drive', 'anti-blitz', 'prevent', 'hurry-up'].includes(t),
    ) as Play['situationTags'],
    confidenceScore: p.confidence,
    isKillSheetPlay: !!p.isKillSheetPlay,
    description: p.conceptBreakdown ?? '',
    rank: p.rank,
    tags,
    impactScore: p.impactScore,
    masteryLevel: p.masteryLevel,
    executionRate: p.executionRate,
    isTrendingCountered: p.isTrendingCountered,
    whenToCall: p.whenToCall,
    conceptBreakdown: p.conceptBreakdown,
    evidence: p.evidence,
    proofAIConfidence: p.proofAIConfidence,
    callStructure: p.callStructure,
    metaStatus: p.metaStatus,
    patchVersion: p.patchVersion,
  };
}

const fallbackMetaStatus: MetaStatus = {
  rating: 'Neutral',
  patchVersion: 'unknown',
  lastUpdated: new Date().toISOString(),
};

function emptyGameplan(opponentName: string): Gameplan {
  return {
    id: 'pending',
    name: opponentName ? `Gameplan vs ${opponentName}` : 'New gameplan',
    opponentId: '',
    opponentName,
    plays: [],
    killSheet: [],
    redZonePackage: [],
    antiBlitzPackage: [],
    twoMinDrillPackage: [],
    metaStatus: fallbackMetaStatus,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

function buildGameplan(args: {
  generatedId: string;
  source: 'claude' | 'mock' | 'cache';
  cached: boolean;
  opponentId: string;
  opponentName: string;
  raw: Record<string, unknown>;
}): Gameplan {
  const raw = args.raw;
  const aiPlays = (raw.plays as AIPlay[]) ?? [];
  const plays = aiPlays.map(mapPlay);
  const killSheetStructured = (raw.killSheet as KillSheetEntry[]) ?? [];
  const scriptView = (raw.scriptView as ScriptViewEntry[]) ?? [];
  const antiBlitzPackageHealth = raw.antiBlitzPackage as PackageHealth | undefined;
  const redZonePackageHealth = raw.redZonePackage as PackageHealth | undefined;
  const twoMinDrill = (raw.twoMinDrill as TwoMinDrillEntry[]) ?? [];
  const opponentSummary = raw.opponentSummary as OpponentSummary | undefined;
  const metaVersion = (raw.metaVersion as string | undefined) ?? 'unknown';

  // Fan plays out into the legacy package buckets so existing tab UI keeps
  // working without further changes.
  const tagged = (tag: string) =>
    plays.filter((p) =>
      (p.tags ?? []).some((t) => t === tag) || p.situationTags.includes(tag as Play['situationTags'][number]),
    );

  return {
    id: args.generatedId,
    generatedId: args.generatedId,
    source: args.source,
    cached: args.cached,
    name: args.opponentName ? `Gameplan vs ${args.opponentName}` : 'Generated gameplan',
    opponentId: args.opponentId,
    opponentName: args.opponentName,
    plays,
    killSheet: plays.filter((p) => p.isKillSheetPlay),
    redZonePackage: tagged('red-zone'),
    antiBlitzPackage: tagged('anti-blitz'),
    twoMinDrillPackage: tagged('2-minute').concat(tagged('2-min-drill')),
    metaStatus: {
      rating:
        ((raw.opponentSummary as OpponentSummary | undefined)?.winRate ?? 50) >= 55 ? 'Countered' : 'Strong',
      patchVersion: metaVersion,
      lastUpdated: new Date().toISOString(),
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    killSheetStructured,
    scriptView,
    antiBlitzPackageHealth,
    redZonePackageHealth,
    twoMinDrill,
    opponentSummary,
    metaVersion,
    overallStrategy: raw.overallStrategy as string | undefined,
    patchVersion: metaVersion,
  };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export const LOADING_MESSAGES = [
  "Analyzing opponent tendencies…",
  "Selecting plays for their coverage shell…",
  "Building your kill sheet…",
  "Calculating confidence scores…",
  "Stress-testing the script vs their adjustments…",
];

export function useGameplan() {
  const titleId = useUIStore((s) => s.selectedTitle);

  const [opponents, setOpponents] = useState<OpponentSummaryDTO[]>([]);
  const [opponentsLoaded, setOpponentsLoaded] = useState(false);
  const [selectedOpponentId, setSelectedOpponentId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<PackageTab>('all');
  const [selectedPlayId, setSelectedPlayId] = useState<string | null>(null);

  const [generatedGameplan, setGeneratedGameplan] = useState<Gameplan | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);

  // ----- opponent loading ----------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await listOpponents(titleId);
        if (cancelled) return;
        setOpponents(list);
        if (list.length > 0 && !selectedOpponentId) {
          setSelectedOpponentId(list[0].id);
        }
      } catch (err) {
        console.warn('[useGameplan] opponent list failed', err);
      } finally {
        if (!cancelled) setOpponentsLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [titleId]);

  // ----- rotating loading message -------------------------------------------
  useEffect(() => {
    if (!isGenerating) return undefined;
    setLoadingMessageIndex(0);
    const id = window.setInterval(() => {
      setLoadingMessageIndex((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 2000);
    return () => window.clearInterval(id);
  }, [isGenerating]);

  const opponent = useMemo(
    () =>
      opponents.find((o) => o.id === selectedOpponentId) ?? {
        id: '',
        gamertag: 'No opponent selected',
        title: titleId,
        archetype: null,
        encounter_count: 0,
        has_dossier: false,
      },
    [opponents, selectedOpponentId, titleId],
  );

  const gameplan = useMemo<Gameplan>(
    () => generatedGameplan ?? emptyGameplan(opponent.gamertag),
    [generatedGameplan, opponent.gamertag],
  );

  const filteredPlays = useMemo(() => {
    switch (activeTab) {
      case 'kill-sheet':
        return gameplan.killSheet;
      case 'red-zone':
        return gameplan.redZonePackage;
      case 'anti-blitz':
        return gameplan.antiBlitzPackage;
      case '2-min-drill':
        return gameplan.twoMinDrillPackage;
      default:
        return gameplan.plays;
    }
  }, [activeTab, gameplan]);

  const selectedPlay = useMemo(
    () => gameplan.plays.find((p) => p.id === selectedPlayId) ?? gameplan.plays[0] ?? null,
    [gameplan.plays, selectedPlayId],
  );

  const generateGameplan = useCallback(
    async (opts?: { bypassCache?: boolean }) => {
      setIsGenerating(true);
      setGenerateError(null);
      try {
        const res = await generateGameplanApi({
          titleId,
          opponentId: selectedOpponentId || undefined,
          mode: 'ranked',
          bypassCache: opts?.bypassCache,
        });
        const built = buildGameplan({
          generatedId: res.gameplan_id,
          source: res.cached ? 'cache' : res.source,
          cached: res.cached,
          opponentId: selectedOpponentId,
          opponentName: opponent.gamertag,
          raw: res.gameplan,
        });
        setGeneratedGameplan(built);
        if (built.plays.length > 0) {
          setSelectedPlayId(built.plays[0].id);
        }
      } catch (err) {
        console.error('[useGameplan] generate failed', err);
        setGenerateError('GameplanAI hit a snag — try again.');
      } finally {
        setIsGenerating(false);
      }
    },
    [titleId, selectedOpponentId, opponent.gamertag],
  );

  const selectPlay = useCallback((play: Play) => setSelectedPlayId(play.id), []);

  return {
    opponents,
    opponentsLoaded,
    selectedOpponentId,
    setSelectedOpponentId,
    opponent: { id: opponent.id, name: opponent.gamertag, archetype: opponent.archetype },
    gameplan,
    activeTab,
    setActiveTab,
    filteredPlays,
    selectedPlay,
    selectPlay,
    isGenerating,
    generateError,
    loadingMessage: LOADING_MESSAGES[loadingMessageIndex],
    generateGameplan,
  };
}
