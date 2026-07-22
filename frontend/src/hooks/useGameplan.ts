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
      'Two receivers cross over the middle, meeting right behind the linebackers. The play-fake is the whole play — it pulls the linebackers a step toward the run, which opens a window over the middle for the crosser. The tight end swings to the flat (the short area near the sideline) as an easy dump-off. Read it middle-first: hit the crosser if the linebackers bit on the fake, or the tight end in the flat if they didn\'t. It beats zone because zone defenders watch the QB, not a man — so the fake moves them and your crossers run in behind.',
    beats: 'Cover 3',
    baseRead:
      'Sell the fake, then read the middle: hit the crosser if the linebackers bit, or the tight end in the flat if the middle\'s covered.',
    whenToCall:
      'Early downs (1st or 2nd), and great on your opening script before the defense has seen your looks. The run has to be believable for the fake to work, so call it when a run would also make sense. Skip it on 3rd-and-long — the crossers take a beat to develop and you won\'t have time.',
    evidence: {
      why: 'This opponent sits in Cover 3 — three deep defenders, everyone else short — about two-thirds of their snaps. Cover 3 leaves a soft spot over the middle between the linebackers and the deep safety, exactly where your crossers end up.',
      data: 'They\'ve shown Cover 3 on 68% of dropbacks over their last 8 games — expect it more often than not, especially on early downs.',
      risk: 'The look that hurts you is Cover 2 Man with a safety over the top — the crossers get carried and a defender is waiting. Tell: two deep safeties and defenders trailing your receivers man-to-man. If you see that, get off it — the corner route or a checkdown is safer.',
      comparable: 'You ran this against a similar Cover-3 opponent (GridironGhost) last week and it hit 3 for 3 — same coverage, same open middle.',
    },
    audibleOptions: [
      {
        id: 'aud-1a',
        label: 'Check to Inside Zone',
        trigger: 'Light box detected (6 or fewer)',
        targetPlay: 'Inside Zone',
        lookFor: 'A light box — only 6 defenders near the line.',
        recognize:
          'Count the players in the box between the tackles; 6 or fewer means they\'re playing the pass, not the run.',
        do: 'Audible to Inside Zone and hand it off — with that few men up front, the run has numbers and easy yards.',
        counterLookFor:
          'After you punish it with runs, a safety dropping down late or an extra man crowding the middle — they\'ve over-rotated to stop the run.',
        counterDo: 'Come back with HB Dive up the gut — they\'ve thinned out to cover, so the middle is open again.',
      },
      {
        id: 'aud-1b',
        label: 'Hot Route Slant',
        trigger: 'Blitz look from WILL',
        targetPlay: 'Quick Slant',
        lookFor: 'The WILL — the weak-side linebacker — creeping down to the line like he\'s coming.',
        recognize: 'That walk-down is a blitz tell; a blitz means one fewer defender left in coverage.',
        do: 'Hot-route your slot to a Slant and throw it the moment you feel pressure.',
        counterLookFor: 'That same WILL still walking down even after your quick slant — the blitz keeps coming.',
        counterDo:
          'Call PA Boot Over — bootleg to the opposite side so you run away from the pressure and throw on the move.',
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
      'A straight-ahead run right between the tackles, behind your two guards who pull to clear a lane. It\'s your reliable short-yardage and goal-line call — low risk, and it gets the tough yard when you need it. Follow the guards into the hole and take what\'s blocked; don\'t dance.',
    beats: 'Nickel/Dime Packages',
    baseRead:
      'Take the handoff and follow your pulling guards straight up the middle — hit the first open crease and lean forward for extra yards.',
    whenToCall:
      'Short yardage and goal line — 3rd or 4th-and-1, or inside the 5. Best when the defense is in nickel or dime (extra defensive backs, fewer big bodies up front), because you\'ll out-muscle them at the point of attack.',
    evidence: {
      why: 'In the red zone this opponent stays in nickel/dime to cover your receivers, which leaves only small defenders in the middle. A downhill run with pulling guards overpowers that light front for the tough yard.',
      data: 'They\'re in nickel or lighter on 61% of red-zone snaps — expect small bodies inside near the goal line.',
      risk: 'If they stack the box (8+ near the line) you\'ll get stuffed. Tell: safeties creeping down pre-snap. Check to PA Boot to punish them for selling out on the run.',
      comparable: 'Same call vs BlitzMaster99 went 4 for 4 on 3rd-and-short last week.',
    },
    audibleOptions: [
      {
        id: 'aud-2a',
        label: 'Check to PA Boot',
        trigger: 'Stacked box (8+)',
        targetPlay: 'PA Boot Over',
        lookFor: 'A stacked box — 8 or more defenders crowded near the line.',
        recognize:
          'Count bodies within a few yards of the ball between the sidelines; 8+ means they\'re all-in to stop the run.',
        do: 'Check to PA Boot Over — fake the dive, roll out, and throw off the run they just committed to.',
        counterLookFor:
          'After the boot burns them, a linebacker or safety hanging back and spying instead of crashing the run.',
        counterDo: 'Go back to the dive — they\'re playing pass now, so the middle is soft again.',
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
      'Two receivers run shallow crossing routes that brush past each other over the middle — like setting a legal pick in basketball. Against man coverage the defenders chasing them run into each other, and one of your guys comes free. It\'s a fast, high-percentage throw that also beats the blitz because the ball comes out quick.',
    beats: 'Man Coverage',
    baseRead:
      'Right after the snap, watch the two crossers — throw to whichever one shakes free as they cross. If both are covered, take the tight end sitting in the middle.',
    whenToCall:
      'Great on 3rd-and-short-to-medium and any time you expect man coverage or a blitz. The quick crossers get the ball out before pressure gets home.',
    evidence: {
      why: 'This opponent plays man coverage a lot near the sticks, and man defenders have to follow your receivers — so when your crossers cross, their defenders collide and someone comes open.',
      data: 'They run man coverage on 59% of snaps in the red zone and on 3rd down — exactly where mesh shines.',
      risk: 'Zone, or a “switch” call where defenders pass you off instead of chasing, takes away the pick. Tell: defenders staying in an area instead of trailing your man. Against that, the corner route or a fade wins instead.',
      comparable: 'Vs PressKing88, mesh converted 4 of 4 in the red zone last week against the same press-man looks.',
    },
    audibleOptions: [
      {
        id: 'aud-3a',
        label: 'Fade to X',
        trigger: 'Single-high safety',
        targetPlay: 'Corner Strike',
        lookFor: 'One deep safety standing in the middle of the field (single-high).',
        recognize:
          'Single-high = just one safety deep in the middle, which leaves your outside receiver one-on-one with no help over the top.',
        do: 'Audible X to a Fade and give him a back-shoulder ball down the sideline — it\'s a 1-on-1 he can win.',
        counterLookFor: 'After the fade hits, the corner playing way off and giving cushion to stop the deep ball.',
        counterDo: 'Go back to the mesh underneath — he\'s bailing deep, so the short crossers are wide open.',
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
      'A flood concept: you send routes at three different depths to one side, with a corner route (angling toward the sideline pylon) as the main target. Against Cover 2 it attacks the gap between the cornerback (who sits short) and the safety (who is deep and wide) — a soft spot neither can reach in time.',
    beats: 'Cover 2',
    baseRead:
      'Read the corner route first — if the safety is late or too wide, throw it to the sideline; if not, work back down to the shorter routes and the flat.',
    whenToCall:
      'Red zone and 2nd-and-medium when you think they\'re in Cover 2 (two deep safeties). The corner route is a scoring shot into the back pylon.',
    evidence: {
      why: 'This opponent leans on Cover 2, which splits the field between a short corner and a deep safety. The corner route drops into the window neither defender owns.',
      data: 'They\'re in Cover 2 on 41% of 2nd-and-medium snaps — the exact down-and-distance this play is built for.',
      risk: 'Cover 4 (four deep defenders, “quarters”) takes the corner away because the safety sits on it. Tell: two safeties widening out pre-snap. Come down to the flat or checkdown instead.',
      comparable: 'Vs NeonEndzone this look produced 2 TDs against the same two-deep shell.',
    },
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
      'A run-pass option: you start a run, but you\'re really reading one defender — the outside linebacker over your bunch. If he crashes down to help on the run, you flip it out to the bubble screen behind him for easy yards; if he stays out to cover, you just hand it off. You can\'t be wrong — you take whatever he gives you.',
    beats: 'Aggressive LB Play',
    baseRead:
      'Eyes on the outside linebacker at the snap. He crashes in → throw the bubble. He widens or drops → hand off the run.',
    whenToCall:
      'Anytime you want a safe, fast play — great vs the blitz and in 2-minute. It\'s a built-in answer to aggressive defenders because you\'re reading them, not guessing.',
    evidence: {
      why: 'This opponent\'s linebackers fly downhill at the first sign of run. That aggressiveness is the whole plan — when they crash, the bubble behind them is wide open.',
      data: 'Their linebackers bite on run action 74% of the time on early downs — so the bubble is there more often than not.',
      risk: 'If the flat defender sits on the bubble instead of chasing the run, don\'t force it. Tell: a defender jumping the screen. Keep the ball and run it — they gave up a man to cover.',
      comparable: 'Vs BlitzHappyDave the bubble hit 5 times for 67 yards against these same downhill linebackers.',
    },
    audibleOptions: [
      {
        id: 'aud-5a',
        label: 'Keep Run',
        trigger: 'OLB drops into coverage',
        targetPlay: 'Inside Zone Read',
        lookFor: 'The outside linebacker widening or dropping into coverage instead of crashing.',
        recognize: 'If he\'s bailing out toward the bubble, the box is now light for a run.',
        do: 'Keep it and run Inside Zone — they\'ve vacated a defender to cover the screen.',
        counterLookFor: 'After you punish them running, a safety rotating down late to plug the run.',
        counterDo: 'Throw the bubble again — with the safety down, there is no one left over the top of the screen.',
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
      'Four receivers run straight downfield, stretching the deep defenders until one has to cover two men. Against Cover 3 (three deep) your two inside “seam” routes put the middle safety in a bind — he can\'t cover both, so one comes open down the middle. It\'s your big-chunk shot play.',
    beats: 'Cover 3',
    baseRead:
      'Read the deep middle safety. Whichever inside seam he doesn\'t cover, throw it. If everyone is covered deep, dump it to the checkdown underneath.',
    whenToCall:
      '2-minute drill and 2nd-or-3rd-and-long when you need a chunk of yards fast. You want them playing deep zone so the seams open up.',
    evidence: {
      why: 'This opponent plays Cover 3 with a single deep-middle safety. Send two seams at him and he can only take one — the other is a big play down the middle.',
      data: 'They\'re in Cover 3 on 64% of obvious passing downs — the coverage four verts is designed to beat.',
      risk: 'Cover 4 or quarters (two deep safeties splitting the field) covers both seams. Tell: two safeties standing deep and wide pre-snap. Check to the crossers underneath instead of forcing it deep.',
      comparable: 'Vs SkyCoverTwo this produced 2 deep touchdowns attacking the same single-high look.',
    },
    audibleOptions: [
      {
        id: 'aud-6a',
        label: 'Hot Slant',
        trigger: 'All-out blitz',
        targetPlay: 'Quick Slant',
        lookFor: 'An all-out blitz — more rushers than you can block, with no deep help behind them.',
        recognize: 'Count the rushers vs your blockers; if they bring more than you can block, someone is coming free.',
        do: 'Hot-route an inside receiver to a Slant and throw it now — beat the blitz with a quick, easy completion.',
        counterLookFor: 'After the slant burns the blitz, them backing off the pressure and dropping more into coverage.',
        counterDo: 'Go back to the verticals — with the blitz gone, you have time to let the deep routes develop.',
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
      'A trap for the pass rush: your line lets the rushers come, then you dump a quick pass to the running back behind a wall of blockers who slip out in front of him. The harder they rush, the better it works — you\'re using their aggression against them.',
    beats: 'Man Blitz',
    baseRead:
      'Let the rush come, then throw it to the back and let him follow his blockers. Don\'t hold it — the timing is quick.',
    whenToCall:
      'When you expect a heavy blitz or man coverage, especially on obvious passing downs. It punishes teams that sell out to get to the QB.',
    evidence: {
      why: 'This opponent blitzes hard and plays man behind it, so defenders turn their backs and chase. That leaves grass in front of your back and blockers out ahead of him.',
      data: 'They blitz on 48% of 3rd-and-long snaps — exactly when a screen turns their pressure into your big gain.',
      risk: 'A spy or a defender who reads the screen and sits can blow it up. Tell: a rusher who stops short instead of chasing the QB. If you see it pre-snap, get to a different call.',
      comparable: 'Vs a similar blitz-heavy opponent, screens averaged big chunks by baiting the rush upfield.',
    },
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
      'Three routes at three heights on the same side — a deep sail toward the sideline, a dig across the middle, and a flat underneath. Against zone you read them top-to-bottom: the defense can\'t cover all three levels, so you take whichever one the underneath defender leaves open.',
    beats: 'Cover 3 / Cover 4',
    baseRead:
      'Read high-to-low: sail first, then the dig, then the flat. Throw to the level the flat defender isn\'t covering.',
    whenToCall:
      '3rd-and-medium and 2-minute against zone teams. It\'s a reliable chain-mover because there is always an open level.',
    evidence: {
      why: 'This opponent plays zone and asks each defender to cover an area. Stacking three routes in one area overloads it — one man can\'t be in two places.',
      data: 'They allow a 72% completion rate on underneath routes vs Cover 3 over their last 6 games — the soft spot this play targets.',
      risk: 'A zone-blitz disguise (rushing a defensive back, dropping a lineman) can take the intermediate read. Tell: unusual pre-snap movement up front. Hot-route the back as a safety valve if it looks funky.',
      comparable: 'Vs TurboTactician this hit on 8 of 10 attempts moving the chains against the same zone looks.',
    },
    audibleOptions: [
      {
        id: 'aud-8a',
        label: 'Switch to Man Beater',
        trigger: 'Press man detected',
        targetPlay: 'Mesh Concept',
        lookFor: 'Press man — a defender lined up right on top of each receiver, with no cushion.',
        recognize:
          'Press = defenders jammed at the line face-to-face with your receivers instead of sitting back in a zone.',
        do: 'Check to Mesh — the crossing routes rub off press defenders and get someone free.',
        counterLookFor: 'After mesh works, defenders backing off into a zone to stop the crossers.',
        counterDo: 'Go back to Levels — vs zone the three-level stretch is open again.',
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
      'A physical gap-scheme run: a guard pulls across and a lead blocker (fullback) attacks the hole, so you hit the C-gap (just outside the tackle) with two extra blockers leading the way. It\'s a downhill, move-the-pile run that wears a defense down.',
    beats: 'Light Boxes',
    baseRead:
      'Follow your pulling guard and fullback through the hole outside the tackle — press it downhill and lean forward for extra yards.',
    whenToCall:
      'Short yardage and red zone when the box is light (6 or fewer defenders up front). With extra blockers leading, you win the numbers game at the point of attack.',
    evidence: {
      why: 'When this opponent plays a light box, you have more blockers than they have defenders at the hole. Power puts a pulling guard and a fullback right there to clear it.',
      data: 'They keep a light box on 58% of standard downs — favorable numbers for a downhill run.',
      risk: 'A shooting nose tackle or an interior stunt can blow it up before it starts. Tell: a defensive tackle crowding your center. Slide the protection or run away from him.',
      comparable: 'Vs a base-personnel opponent, power averaged solid gains and 2 short TDs pounding a light front.',
    },
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
      'A quick triangle out of a bunch: a flat route, a curl (comeback) sitting down, and a corner route — three routes that box in the flat defender. Whatever he does is wrong: cover the flat and the curl is open; sink to the curl and the flat is open. It\'s a fast, dependable 3rd-down answer.',
    beats: 'Cover 2 Zone',
    baseRead:
      'Read the flat defender (the outside underneath man). If he jumps the flat, throw the curl behind him; if he sinks to the curl, throw the flat in front of him.',
    whenToCall:
      '3rd-and-short-to-medium against zone. The quick triangle gives you an easy, high-percentage throw to move the chains.',
    evidence: {
      why: 'This opponent plays zone on 3rd down, so the flat defender has to choose between two of your routes. The triangle makes him wrong either way.',
      data: 'They sit in Cover 2 zone on 47% of 3rd downs — the exact defender-in-conflict this play attacks.',
      risk: 'Man coverage takes away the natural read because defenders follow your men instead of choosing. Tell: defenders trailing receivers across the field. Check to a man-beater like Mesh.',
      comparable: 'Vs zone-heavy opponents this spot triangle has been a steady chain-mover on money downs.',
    },
    audibleOptions: [
      {
        id: 'aud-10a',
        label: 'Check to Mesh',
        trigger: 'Man coverage detected',
        targetPlay: 'Mesh Concept',
        lookFor: 'Man coverage — defenders locked onto individual receivers pre-snap.',
        recognize:
          'If each defender mirrors a receiver (and follows motion), it\'s man, not zone — the triangle read won\'t work.',
        do: 'Check to Mesh — the crossing routes rub man defenders off and spring someone free.',
        counterLookFor: 'After mesh burns them, defenders dropping into zone to stop the crossers.',
        counterDo: 'Go back to Spot — vs zone the flat-defender triangle is open again.',
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
