/**
 * Per-drill detection configs consumed by the VisionAudioForge → Claude
 * vision pipeline.
 *
 * Each entry tells the backend monitor *what to look at* for a given drill
 * type. The actual rep classification happens server-side: the backend reads
 * the config, builds the system prompt, sends the frame to Claude vision,
 * and returns a rep verdict.
 *
 * Title IDs map to the canonical IDs in `lib/titles.ts`.
 */

export type TitleId =
  | 'madden26'
  | 'cfb26'
  | 'nba2k26'
  | 'fc26'
  | 'mlbtheshow26'
  | 'warzone'
  | 'fortnite'
  | 'ufc5'
  | 'pga2k25'
  | 'undisputed'
  | 'videopoker';

export interface DetectionConfig {
  /** Title IDs this config applies to. */
  titles: TitleId[];
  /** Visual/audio cues the model should look for in each frame. */
  watchFor: string[];
  /** Plain-language description of what counts as a successful rep. */
  successCriteria: string;
  /** Plain-language description of a failed rep. */
  failCriteria: string;
  /** Hint about how often a rep is expected (used to throttle false matches). */
  expectedRepDurationSec?: { min: number; max: number };
}

export const DRILL_DETECTION_CONFIGS: Record<string, DetectionConfig> = {
  // ---------------- Football (Madden / CFB) ----------------
  'pre-snap-reads': {
    titles: ['madden26', 'cfb26'],
    watchFor: [
      'pre-snap defensive alignment',
      'play-clock countdown',
      'safety rotation / late shifts',
      'hot-route or audible indicator',
    ],
    successCriteria:
      'Player spent 2-6 seconds at the line and made a hot-route or audible reflecting the defensive shell, or completed the throw against the predicted coverage.',
    failCriteria:
      'Snapped under 1.5s with no pre-snap adjustment, or the throw was clearly into the called coverage with no read.',
    expectedRepDurationSec: { min: 6, max: 30 },
  },
  'clutch-drive': {
    titles: ['madden26', 'cfb26'],
    watchFor: [
      'game clock under 2:00',
      'score differential',
      'sideline route windows',
      'play result banner',
    ],
    successCriteria:
      'Drive ends in a touchdown before the clock expires.',
    failCriteria:
      'Turnover, sack-fumble, or clock expires short of the end zone.',
    expectedRepDurationSec: { min: 30, max: 180 },
  },
  'anti-meta-coverage': {
    titles: ['madden26', 'cfb26'],
    watchFor: [
      'post-snap coverage rotation (Cover 3 / Cover 2 Man / Tampa 2)',
      'route-combo development',
      'completion or interception animation',
    ],
    successCriteria:
      'Completion against the targeted coverage, ideally to a route designed to beat it.',
    failCriteria: 'Sack, incompletion, or interception against the targeted coverage.',
    expectedRepDurationSec: { min: 6, max: 20 },
  },
  'pocket-pressure': {
    titles: ['madden26', 'cfb26'],
    watchFor: [
      'pass rush converging on QB',
      'QB step-up or roll-out animation',
      'check-down completion or scramble for positive yards',
    ],
    successCriteria: 'Completed checkdown or scramble for net positive yardage.',
    failCriteria: 'Sack, fumble, or thrown away under no real pressure.',
    expectedRepDurationSec: { min: 4, max: 15 },
  },
  'red-zone-efficiency': {
    titles: ['madden26', 'cfb26'],
    watchFor: ['field position inside the 20', 'play result', 'formation chosen'],
    successCriteria: 'Drive ends in a touchdown.',
    failCriteria: 'Field-goal attempt, turnover on downs, or interception.',
    expectedRepDurationSec: { min: 6, max: 60 },
  },

  // ---------------- Basketball (NBA 2K) ----------------
  'shot-timing': {
    titles: ['nba2k26'],
    watchFor: ['shot meter visible', 'release point relative to green window', 'shot result'],
    successCriteria: 'Release lands in the green window AND the shot is made.',
    failCriteria: 'Release in the red zone, or a clear miss off the rim.',
    expectedRepDurationSec: { min: 1, max: 5 },
  },
  'paint-finishing': {
    titles: ['nba2k26'],
    watchFor: ['drive into the paint', 'contest / contact animation', 'finish result'],
    successCriteria: 'Layup or dunk converted (with or without contact).',
    failCriteria: 'Block, miss, or charge.',
    expectedRepDurationSec: { min: 2, max: 8 },
  },

  // ---------------- Soccer (EA FC 26) ----------------
  'skill-moves': {
    titles: ['fc26'],
    watchFor: ['ball-control animation', 'defender response', 'possession state'],
    successCriteria: 'Defender beaten and possession kept.',
    failCriteria: 'Tackled, ball lost, or cleared.',
    expectedRepDurationSec: { min: 2, max: 8 },
  },
  'set-piece-conversion': {
    titles: ['fc26'],
    watchFor: ['free kick or corner setup', 'ball trajectory', 'goal/save indicator'],
    successCriteria: 'Goal scored from the set piece.',
    failCriteria: 'Saved, blocked, or wide.',
    expectedRepDurationSec: { min: 4, max: 15 },
  },

  // ---------------- Baseball (MLB The Show) ----------------
  'plate-discipline': {
    titles: ['mlbtheshow26'],
    watchFor: ['pitch trajectory', 'PCI / strike zone overlay', 'swing decision', 'umpire call'],
    successCriteria: 'Pitch in the zone is swung at; pitch out of the zone is taken.',
    failCriteria: 'Chased a ball out of the zone or took a strike down the middle.',
    expectedRepDurationSec: { min: 2, max: 8 },
  },
  'pitching-tunnels': {
    titles: ['mlbtheshow26'],
    watchFor: ['pitch type sequence', 'release point', 'batter swing/take'],
    successCriteria:
      'Two consecutive pitches share an early tunnel and produce a swing-and-miss or weak contact.',
    failCriteria: 'Hung breaking ball or pitch yanked out of the tunnel for a hard hit.',
    expectedRepDurationSec: { min: 6, max: 20 },
  },

  // ---------------- FPS (Warzone) ----------------
  'crosshair-placement': {
    titles: ['warzone'],
    watchFor: ['head-level crosshair on common angles', 'engagement initiated', 'damage numbers'],
    successCriteria: 'First-shot connects on the head/upper torso of the engaged target.',
    failCriteria: 'Crosshair below waist or whiffed first shot.',
    expectedRepDurationSec: { min: 1, max: 4 },
  },
  'rotational-positioning': {
    titles: ['warzone'],
    watchFor: ['minimap rotation cues', 'gas circle position', 'cover usage on movement'],
    successCriteria: 'Reached safe rotation cover before the next gas tick without taking damage.',
    failCriteria: 'Caught in the open, downed, or hit by gas.',
    expectedRepDurationSec: { min: 5, max: 30 },
  },

  // ---------------- Building (Fortnite) ----------------
  'building-edits': {
    titles: ['fortnite'],
    watchFor: ['build piece placed', 'edit overlay', 'edit confirmation timing'],
    successCriteria:
      'Edit placed and confirmed under ~0.4s with the intended cut.',
    failCriteria: 'Cancelled edit, mis-cut, or confirmation > 0.8s.',
    expectedRepDurationSec: { min: 1, max: 3 },
  },
  'box-fights': {
    titles: ['fortnite'],
    watchFor: ['adjacent boxes', 'edit takes', 'damage or elimination indicator'],
    successCriteria: 'Eliminated the opponent in the box exchange.',
    failCriteria: 'Got eliminated or forced into a retreat take.',
    expectedRepDurationSec: { min: 5, max: 20 },
  },

  // ---------------- Combat (UFC 5) ----------------
  'submission-defense': {
    titles: ['ufc5'],
    watchFor: ['submission-attempt overlay', 'escape meter', 'tap-out indicator'],
    successCriteria: 'Escape meter completes and submission attempt is broken.',
    failCriteria: 'Tap-out or referee stoppage from the submission.',
    expectedRepDurationSec: { min: 5, max: 30 },
  },
  'striking-combos': {
    titles: ['ufc5'],
    watchFor: ['three-strike combos', 'opponent block/parry indicator', 'damage numbers'],
    successCriteria:
      'At least 2 of 3 strikes land cleanly through the guard.',
    failCriteria: 'All three blocked or eaten a counter.',
    expectedRepDurationSec: { min: 2, max: 8 },
  },

  // ---------------- Combat (Undisputed Boxing) ----------------
  'jab-control': {
    titles: ['undisputed'],
    watchFor: ['lead-hand jab cadence', 'opponent posture / block animation', 'damage feedback'],
    successCriteria:
      'Jab lands cleanly while maintaining range — opponent posture broken or no counter.',
    failCriteria: 'Counter overhand or hook lands while jabbing.',
    expectedRepDurationSec: { min: 1, max: 5 },
  },
  'counter-punching': {
    titles: ['undisputed'],
    watchFor: ['opponent attack tell', 'slip/parry animation', 'counter strike landing'],
    successCriteria: 'Slipped/blocked the incoming strike and landed a counter cleanly.',
    failCriteria: 'Ate the strike or threw the counter into a block.',
    expectedRepDurationSec: { min: 2, max: 6 },
  },

  // ---------------- Precision (PGA 2K25) ----------------
  'tempo-swing': {
    titles: ['pga2k25'],
    watchFor: ['swing tempo arc', 'transition timing pip', 'ball flight result'],
    successCriteria: 'Tempo bar lands in the perfect zone and ball flight matches intended shape.',
    failCriteria: 'Fast/slow tempo grade or shot shape opposite of intended.',
    expectedRepDurationSec: { min: 3, max: 8 },
  },
  'green-reading': {
    titles: ['pga2k25'],
    watchFor: ['green grid overlay', 'aim line vs read', 'putt result'],
    successCriteria: 'Putt holes out or finishes within tap-in range.',
    failCriteria: 'Misread direction or speed by more than one cup.',
    expectedRepDurationSec: { min: 4, max: 12 },
  },

  // ---------------- Card (Video Poker) ----------------
  'optimal-hold': {
    titles: ['videopoker'],
    watchFor: ['initial five-card deal', 'held / discarded indicators', 'final hand strength'],
    successCriteria:
      'Player held the cards an optimal-strategy chart would hold for the dealt hand.',
    failCriteria: 'Held a sub-optimal combination — cost expected value.',
    expectedRepDurationSec: { min: 2, max: 8 },
  },
};

/** Look up the detection config for a (drillType, titleId) pair. */
export function getDetectionConfig(
  drillType: string | undefined,
  titleId: string,
): DetectionConfig | null {
  if (!drillType) return null;
  const cfg = DRILL_DETECTION_CONFIGS[drillType];
  if (!cfg) return null;
  if (!cfg.titles.includes(titleId as TitleId)) return null;
  return cfg;
}

/** True when we have any vision config we can run for this drill+title. */
export function isAutoDetectableDrill(
  drillType: string | undefined,
  titleId: string,
): boolean {
  return getDetectionConfig(drillType, titleId) !== null;
}
