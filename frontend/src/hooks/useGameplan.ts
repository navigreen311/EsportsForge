'use client';

import { useState, useCallback, useMemo } from 'react';
import type { Play, Gameplan, PackageTab, MetaStatus } from '@/types/gameplan';
import { generateBackendGameplan } from '@/lib/gameplan/api';

const mockPlays: Play[] = [
  {
    id: 'play-1',
    name: 'PA Crossers',
    formation: 'Gun Trips TE',
    conceptTags: ['play-action', 'zone-beater'],
    situationTags: ['opening-drive'],
    confidenceScore: 92,
    isKillSheetPlay: true,
    description:
      'Play-action with dual crossing routes underneath. The TE leaks out to the flat as a safety valve. High-percentage throw against zone coverage.',
    beats: 'Cover 3',
    audibleOptions: [
      {
        id: 'aud-1a',
        label: 'Check to Inside Zone',
        trigger: 'Light box detected (6 or fewer)',
        targetPlay: 'Inside Zone',
      },
      {
        id: 'aud-1b',
        label: 'Hot Route Slant',
        trigger: 'Blitz look from WILL',
        targetPlay: 'Quick Slant',
      },
    ],
    // Explicit route geometry (proves the Phase-2 data path). Gun Trips TE:
    // dual crossers underneath (X over, slot shallow) + TE leaking to the flat.
    routes: [
      { receiver: 'X', points: [[10, 60], [10, 42], [66, 40]] },
      { receiver: 'SL', points: [[32, 59], [32, 54], [72, 51]] },
      { receiver: 'TE', points: [[64, 60], [64, 57], [88, 55]] },
      { receiver: 'Z', points: [[90, 60], [90, 34], [85, 38]] },
      { receiver: 'HB', points: [[46, 72], [46, 66], [58, 64]] },
    ],
  },
  {
    id: 'play-2',
    name: 'HB Dive',
    formation: 'Singleback Ace',
    conceptTags: ['run'],
    situationTags: ['red-zone', 'goal-line'],
    confidenceScore: 88,
    isKillSheetPlay: true,
    description:
      'Power run between the tackles. Both guards pull to create a running lane. Reliable short-yardage and goal-line option.',
    beats: 'Nickel/Dime Packages',
    audibleOptions: [
      {
        id: 'aud-2a',
        label: 'Check to PA Boot',
        trigger: 'Stacked box (8+)',
        targetPlay: 'PA Boot Over',
      },
    ],
  },
  {
    id: 'play-3',
    name: 'Mesh Concept',
    formation: 'Shotgun Bunch',
    conceptTags: ['man-beater', 'quick-pass'],
    situationTags: ['3rd-down', 'anti-blitz'],
    confidenceScore: 85,
    isKillSheetPlay: true,
    description:
      'Two receivers run shallow crossing routes in opposite directions, creating natural picks against man coverage. Quick release beats pressure.',
    beats: 'Man Coverage',
    audibleOptions: [
      {
        id: 'aud-3a',
        label: 'Fade to X',
        trigger: 'Single-high safety',
        targetPlay: 'Corner Strike',
      },
    ],
    // Explicit route geometry. Shotgun Bunch mesh: opposing shallow crossers
    // (X and Z) + slot corner + TE sit + HB to the flat.
    routes: [
      { receiver: 'X', points: [[12, 60], [12, 56], [64, 53]] },
      { receiver: 'Z', points: [[88, 60], [88, 56], [34, 53]] },
      { receiver: 'SL', points: [[30, 59], [30, 44], [16, 36]] },
      { receiver: 'TE', points: [[62, 60], [62, 48], [62, 52]] },
      { receiver: 'HB', points: [[46, 72], [46, 68], [66, 66]] },
    ],
  },
  {
    id: 'play-4',
    name: 'Corner Strike',
    formation: 'Gun Trips TE',
    conceptTags: ['zone-beater', 'deep-shot'],
    situationTags: ['red-zone'],
    confidenceScore: 78,
    isKillSheetPlay: false,
    description:
      'Flood concept with a corner route as the primary read. Attacks the void between the corner and safety in Cover 2.',
    beats: 'Cover 2',
    audibleOptions: [],
  },
  {
    id: 'play-5',
    name: 'RPO Bubble',
    formation: 'Shotgun Trips',
    conceptTags: ['rpo', 'quick-pass'],
    situationTags: ['anti-blitz', '2-minute'],
    confidenceScore: 81,
    isKillSheetPlay: true,
    description:
      'Run-pass option with a bubble screen to the trips side. Read the OLB — if he crashes, throw the bubble; if he drops, hand off.',
    beats: 'Aggressive LB Play',
    audibleOptions: [
      {
        id: 'aud-5a',
        label: 'Keep Run',
        trigger: 'OLB drops into coverage',
        targetPlay: 'Inside Zone Read',
      },
    ],
  },
  {
    id: 'play-6',
    name: 'Four Verticals',
    formation: 'Gun Empty',
    conceptTags: ['deep-shot', 'zone-beater'],
    situationTags: ['2-minute'],
    confidenceScore: 72,
    isKillSheetPlay: false,
    description:
      'All four receivers run vertical routes. Read the safeties — throw to the void between Cover 2 safeties or the seam against Cover 3.',
    beats: 'Cover 3',
    audibleOptions: [
      {
        id: 'aud-6a',
        label: 'Hot Slant',
        trigger: 'All-out blitz',
        targetPlay: 'Quick Slant',
      },
    ],
  },
  {
    id: 'play-7',
    name: 'HB Screen',
    formation: 'Singleback Deuce Close',
    conceptTags: ['screen', 'misdirection'],
    situationTags: ['anti-blitz'],
    confidenceScore: 76,
    isKillSheetPlay: false,
    description:
      'Let the pass rushers upfield, then dump it to the RB behind a wall of pulling linemen. Deadly against aggressive blitz packages.',
    beats: 'Man Blitz',
    audibleOptions: [],
  },
  {
    id: 'play-8',
    name: 'Levels Sail',
    formation: 'Gun Trey Open',
    conceptTags: ['zone-beater', 'quick-pass'],
    situationTags: ['3rd-down', '2-minute'],
    confidenceScore: 83,
    isKillSheetPlay: true,
    description:
      'Three-level passing concept stretching the defense vertically. Read high-to-low: sail route, dig, flat. Consistently beats zone coverages.',
    beats: 'Cover 3 / Cover 4',
    audibleOptions: [
      {
        id: 'aud-8a',
        label: 'Switch to Man Beater',
        trigger: 'Press man detected',
        targetPlay: 'Mesh Concept',
      },
    ],
  },
  {
    id: 'play-9',
    name: 'Power Run',
    formation: 'Pistol Strong',
    conceptTags: ['run'],
    situationTags: ['red-zone'],
    confidenceScore: 69,
    isKillSheetPlay: false,
    description:
      'Gap-scheme run with a pulling guard and lead fullback. Attacks the C-gap with overwhelming force. Best when defense is in base personnel.',
    beats: 'Light Boxes',
    audibleOptions: [],
  },
  {
    id: 'play-10',
    name: 'Spot Concept',
    formation: 'Shotgun Bunch',
    conceptTags: ['zone-beater', 'quick-pass'],
    situationTags: ['3rd-down'],
    confidenceScore: 74,
    isKillSheetPlay: false,
    description:
      'Triangle read concept from bunch — flat, curl, corner. Creates a high-low read on the flat defender. Quick, reliable 3rd-down conversion play.',
    beats: 'Cover 2 Zone',
    audibleOptions: [
      {
        id: 'aud-10a',
        label: 'Check to Mesh',
        trigger: 'Man coverage detected',
        targetPlay: 'Mesh Concept',
      },
    ],
  },
];

const mockMetaStatus: MetaStatus = {
  rating: 'Strong',
  patchVersion: 'Title Update 4.2',
  lastUpdated: '2026-03-21T18:30:00Z',
};

const mockOpponents = [
  { id: 'opp-1', name: 'xXDragonSlayerXx' },
  { id: 'opp-2', name: 'GridironGhost' },
  { id: 'opp-3', name: 'BlitzKing_99' },
  { id: 'opp-4', name: 'PocketPresser' },
];

export function useGameplan() {
  const [selectedOpponentId, setSelectedOpponentId] = useState('opp-1');
  const [activeTab, setActiveTab] = useState<PackageTab>('all');
  const [selectedPlayId, setSelectedPlayId] = useState<string | null>('play-1');
  const [isGenerating, setIsGenerating] = useState(false);
  // Live plays from the backend generate endpoint. Null until the user hits
  // "Generate" and it succeeds; on failure we keep the mock so the page never
  // breaks. When present, live plays carry real (validated) route geometry.
  const [livePlays, setLivePlays] = useState<Play[] | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const opponent = mockOpponents.find((o) => o.id === selectedOpponentId) ?? mockOpponents[0]!;
  const plays = livePlays ?? mockPlays;

  const gameplan: Gameplan = useMemo(
    () => ({
      id: 'gp-1',
      name: `Gameplan vs ${opponent.name}`,
      opponentId: opponent.id,
      opponentName: opponent.name,
      plays,
      killSheet: plays.filter((p) => p.isKillSheetPlay),
      redZonePackage: plays.filter((p) => p.situationTags.includes('red-zone')),
      antiBlitzPackage: plays.filter((p) => p.situationTags.includes('anti-blitz')),
      twoMinDrillPackage: plays.filter((p) => p.situationTags.includes('2-minute')),
      metaStatus: mockMetaStatus,
      createdAt: '2026-03-20T10:00:00Z',
      updatedAt: '2026-03-21T18:30:00Z',
    }),
    [opponent, plays]
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

  const selectedPlay =
    plays.find((p) => p.id === selectedPlayId) ?? plays[0] ?? null;

  const generateGameplan = useCallback(async () => {
    setIsGenerating(true);
    setGenerateError(null);
    try {
      const live = await generateBackendGameplan({ scheme: 'west_coast' });
      if (live.length > 0) {
        setLivePlays(live);
        setSelectedPlayId(live[0]!.id); // select into the new list
      }
    } catch {
      // Backend unreachable / errored — keep the mock plays in place.
      setGenerateError('Live generation is unavailable — showing the sample gameplan.');
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const selectPlay = useCallback((play: Play) => {
    setSelectedPlayId(play.id);
  }, []);

  return {
    opponents: mockOpponents,
    selectedOpponentId,
    setSelectedOpponentId,
    opponent,
    gameplan,
    activeTab,
    setActiveTab,
    filteredPlays,
    selectedPlay,
    selectPlay,
    isGenerating,
    generateGameplan,
    isLive: livePlays !== null,
    generateError,
  };
}
