/**
 * VisionAudioForge detection configs.
 *
 * Each config tells the monitor endpoint what kind of execution it should
 * recognise in a frame and what counts as success vs. failure. Configs are
 * keyed by a logical scenario type (3rd-and-medium, red-zone, secret-weapon
 * etc.) and crossed with the title to produce the prompt the vision model
 * sees.
 *
 * The configs intentionally describe *intent*, not pixel layouts — the
 * vision model receives the natural-language criteria along with the frame
 * and decides accordingly.
 */

export type DetectionScenarioType =
  | '3rd-and-medium'
  | '2-minute-drill'
  | 'red-zone'
  | '4th-and-short'
  | 'backed-up'
  | 'protect-lead'
  | 'down-7-late'
  | 'bunch-trips'
  | 'secret-weapon'
  | 'custom';

export interface DetectionConfig {
  type: DetectionScenarioType;
  /** Title IDs this config is valid for. 'all' means any title. */
  titleId: string | string[] | 'all';
  watchFor: string[];
  successCriteria: Record<string, unknown>;
  failCriteria: Record<string, unknown>;
  promptContext: string;
}

const SIMLAB_CONFIGS: Record<DetectionScenarioType, DetectionConfig> = {
  '3rd-and-medium': {
    type: '3rd-and-medium',
    titleId: ['madden-26', 'cfb-26'],
    watchFor: [
      'play_called',
      'down_and_distance',
      'coverage_identified_pre_snap',
      'play_result',
    ],
    successCriteria: {
      preSnapRead: true,
      coverageMatched: true,
      gainedFirstDown: true,
    },
    failCriteria: {
      snapTooFast: true,
      wrongPlay: true,
      turnover: true,
    },
    promptContext:
      'Watching for 3rd & medium execution. ' +
      'Success = pre-snap read + correct play call + first down. ' +
      'Fail = rushed snap or wrong concept for coverage shown.',
  },

  '2-minute-drill': {
    type: '2-minute-drill',
    titleId: ['madden-26', 'cfb-26'],
    watchFor: [
      'hurry_up_offense_active',
      'clock_management',
      'sideline_route_completion',
      'timeout_usage',
    ],
    successCriteria: {
      clockManaged: true,
      sidelineComplete: true,
      noTurnover: true,
    },
    failCriteria: {
      clockRunOut: true,
      turnover: true,
      badTimeout: true,
    },
    promptContext:
      'Watching 2-minute drill execution. ' +
      'Success = good clock management + sideline completions. ' +
      'Fail = clock mismanagement or turnover.',
  },

  'red-zone': {
    type: 'red-zone',
    titleId: ['madden-26', 'cfb-26'],
    watchFor: ['field_position_inside_20', 'play_result', 'formation_used'],
    successCriteria: {
      inRedZone: true,
      result: ['touchdown', 'first_down'],
    },
    failCriteria: {
      result: ['turnover', 'incompletion_on_4th'],
    },
    promptContext:
      'Watching red zone execution. ' +
      'Success = score or first down inside the 20. ' +
      'Fail = turnover or failed 4th down.',
  },

  '4th-and-short': {
    type: '4th-and-short',
    titleId: ['madden-26', 'cfb-26'],
    watchFor: ['down_4th', 'distance_short', 'play_called', 'result'],
    successCriteria: { converted: true },
    failCriteria: { turnoverOnDowns: true, fumble: true },
    promptContext:
      'Watching 4th & short conversion. ' +
      'Success = first down or touchdown. ' +
      'Fail = turnover on downs, fumble, interception.',
  },

  'backed-up': {
    type: 'backed-up',
    titleId: ['madden-26', 'cfb-26'],
    watchFor: ['field_position_inside_own_5', 'play_result', 'formation_used'],
    successCriteria: { gainedYardsToBreathingRoom: true, noTurnover: true },
    failCriteria: { safety: true, turnover: true },
    promptContext:
      'Watching backed-up offense (inside own 5). ' +
      'Success = pick up first down or punt safely from the +20. ' +
      'Fail = safety, turnover, or busted protection.',
  },

  'protect-lead': {
    type: 'protect-lead',
    titleId: ['madden-26', 'cfb-26'],
    watchFor: ['clock_burn', 'first_down_conversions', 'turnover_avoided'],
    successCriteria: { clockBurned: true, possessionMaintained: true },
    failCriteria: { turnover: true, threeAndOut: true },
    promptContext:
      'Watching offense that needs to bleed clock with a lead. ' +
      'Success = run clock + convert chains. ' +
      'Fail = three-and-out, turnover, or quick scoring drive given up.',
  },

  'down-7-late': {
    type: 'down-7-late',
    titleId: ['madden-26', 'cfb-26'],
    watchFor: ['hurry_up', 'sideline_completions', 'red_zone_entry', 'result'],
    successCriteria: {
      reachedRedZone: true,
      result: ['touchdown', 'tying_score'],
    },
    failCriteria: { clockRunOut: true, turnover: true },
    promptContext:
      'Watching desperation drive — down 7 with under 2:00. ' +
      'Success = touchdown to tie or 2-point conversion to lead. ' +
      'Fail = clock out, turnover, fourth-down stop.',
  },

  'bunch-trips': {
    type: 'bunch-trips',
    titleId: ['madden-26', 'cfb-26'],
    watchFor: [
      'pre_snap_alignment',
      'coverage_called',
      'completion_to_bunch_side',
    ],
    successCriteria: {
      coverageCalledCorrectly: true,
      noBigPlayAllowed: true,
    },
    failCriteria: {
      explosivePlayAllowed: true,
      busted_coverage: true,
    },
    promptContext:
      'Watching defense vs. 3x1 bunch/trips. ' +
      'Success = correct coverage call + no explosive given up. ' +
      'Fail = blown coverage, easy completion to back-shoulder.',
  },

  'secret-weapon': {
    type: 'secret-weapon',
    titleId: 'all',
    watchFor: [
      'formation_matches_weapon',
      'play_called_matches_weapon',
      'execution_quality',
      'result',
    ],
    successCriteria: {
      correctFormation: true,
      correctPlay: true,
      executedCleanly: true,
    },
    failCriteria: {
      wrongFormation: true,
      executionError: true,
      turnover: true,
    },
    promptContext:
      'Watching secret weapon execution. ' +
      'Success = correct formation + clean execution. ' +
      'Fail = wrong play, fumbled execution, or turnover.',
  },

  custom: {
    type: 'custom',
    titleId: 'all',
    watchFor: ['play_in_progress', 'rep_completed', 'result'],
    successCriteria: { repCompletedSuccessfully: true },
    failCriteria: { turnover: true },
    promptContext:
      'Watching custom drill rep. Success = clean execution of stated objective.',
  },
};

const SIMLAB_TYPE_BY_SCENARIO_ID: Record<string, DetectionScenarioType> = {
  '3rd-medium': '3rd-and-medium',
  '2min-drill': '2-minute-drill',
  'red-zone': 'red-zone',
  'backed-up': 'backed-up',
  '4th-short': '4th-and-short',
  'protect-lead': 'protect-lead',
  'down-7-late': 'down-7-late',
  'bunch-trips': 'bunch-trips',
};

export function getSimLabDetectionConfig(
  scenarioId: string | undefined,
  weaponName?: string,
  formation?: string,
  playName?: string
): DetectionConfig {
  if (weaponName) {
    const base = SIMLAB_CONFIGS['secret-weapon'];
    return {
      ...base,
      promptContext:
        `Watching secret weapon execution: ${weaponName}. ` +
        (formation ? `Formation: ${formation}. ` : '') +
        (playName ? `Play: ${playName}. ` : '') +
        'Success = correct formation + clean execution. ' +
        'Fail = wrong play, fumbled execution, or turnover.',
    };
  }
  const type = scenarioId
    ? SIMLAB_TYPE_BY_SCENARIO_ID[scenarioId]
    : undefined;
  return SIMLAB_CONFIGS[type ?? 'custom'];
}

export const DETECTION_CONFIGS = SIMLAB_CONFIGS;
