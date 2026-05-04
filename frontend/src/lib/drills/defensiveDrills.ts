/**
 * Mock defensive drill catalog for the Drill Lab.
 *
 * Real ImpactRank scoring of defensive priorities lives behind a separate
 * data pipeline that doesn't exist yet — these IRs are illustrative
 * baselines so the queue UI has something meaningful to render. When the
 * real DefensivePriority pipeline lands, swap this catalog for a server
 * fetch.
 */

export interface DefensiveDrill {
  id: string;
  name: string;
  category: string;
  impactRank: number; // 0–10
  description: string;
  reps: number;
  durationMinutes: number;
}

export const DEFENSIVE_DRILLS_BY_TITLE: Record<string, DefensiveDrill[]> = {
  'madden-26': [
    {
      id: 'user-coverage-recognition',
      name: 'User Coverage Recognition',
      category: 'Coverage',
      impactRank: 9.1,
      description:
        'Cover the TE after the snap. Stay on his hip. Do not get beaten on the seam route.',
      reps: 12,
      durationMinutes: 8,
    },
    {
      id: 'blitz-timing',
      name: 'Blitz Timing',
      category: 'Pressure',
      impactRank: 8.7,
      description: 'Time the A-gap blitz to hit the QB on release.',
      reps: 10,
      durationMinutes: 6,
    },
    {
      id: 'qb-contain',
      name: 'QB Contain Discipline',
      category: 'Run Defense',
      impactRank: 8.2,
      description: 'Stay in your lane. Do not over-pursue. Force the QB back inside.',
      reps: 10,
      durationMinutes: 6,
    },
    {
      id: 'zone-drop-assignment',
      name: 'Zone Drop Assignment',
      category: 'Coverage',
      impactRank: 7.8,
      description: 'Drop to your assigned zone. Read QB eyes. Do not jump routes.',
      reps: 12,
      durationMinutes: 8,
    },
    {
      id: 'red-zone-press',
      name: 'Red Zone Press Coverage',
      category: 'Coverage',
      impactRank: 7.4,
      description: 'Press the receiver at the line. Disrupt timing routes.',
      reps: 10,
      durationMinutes: 6,
    },
  ],
  'cfb-26': [
    {
      id: 'option-read-defense',
      name: 'Option Read Defense',
      category: 'Run Defense',
      impactRank: 8.9,
      description: 'Stay in your lane on triple option. Spy the QB on read look.',
      reps: 12,
      durationMinutes: 8,
    },
    {
      id: 'rpo-killer',
      name: 'RPO Killer Drop',
      category: 'Coverage',
      impactRank: 8.5,
      description: 'Robber drop into slant window — eyes on QB, not receiver.',
      reps: 10,
      durationMinutes: 7,
    },
  ],
  'nba-2k26': [
    {
      id: 'on-ball-pressure',
      name: 'On-Ball Pressure',
      category: 'On-Ball',
      impactRank: 9.0,
      description: 'Stay between your man and the basket. Mirror the dribble.',
      reps: 12,
      durationMinutes: 7,
    },
    {
      id: 'pnr-hedge',
      name: 'PNR Hedge Timing',
      category: 'PNR',
      impactRank: 8.8,
      description: 'Show hard on the screen. Recover before they turn the corner.',
      reps: 10,
      durationMinutes: 6,
    },
    {
      id: 'closeout-discipline',
      name: 'Closeout Discipline',
      category: 'Closeout',
      impactRank: 8.5,
      description: 'Sprint then chop. High hand contest. Do not leave your feet early.',
      reps: 10,
      durationMinutes: 6,
    },
    {
      id: 'help-rotation',
      name: 'Help Defense Rotation',
      category: 'Help',
      impactRank: 8.1,
      description: 'Identify when teammate is beaten. Rotate to stop the drive.',
      reps: 8,
      durationMinutes: 5,
    },
  ],
  'eafc-26': [
    {
      id: 'jockey-timing',
      name: 'Jockey Timing',
      category: '1v1 Defending',
      impactRank: 9.2,
      description: 'Hold L2/LT to jockey. Force them toward the sideline.',
      reps: 12,
      durationMinutes: 7,
    },
    {
      id: 'tackle-discipline',
      name: 'Tackle Discipline',
      category: '1v1 Defending',
      impactRank: 8.9,
      description: 'Do not dive in. Wait for them to commit.',
      reps: 10,
      durationMinutes: 6,
    },
    {
      id: 'shape-hold',
      name: 'Defensive Shape Hold',
      category: 'Positioning',
      impactRank: 8.3,
      description: 'Stay in formation. Do not press without a trigger.',
      reps: 10,
      durationMinutes: 6,
    },
  ],
  'mlb-26': [
    {
      id: 'pitch-sequence',
      name: 'Two-Strike Sequence',
      category: 'Pitching',
      impactRank: 8.4,
      description: 'Climb the ladder, then break away. Set up the chase pitch.',
      reps: 10,
      durationMinutes: 6,
    },
  ],
  'warzone': [
    {
      id: 'cover-usage',
      name: 'Cover Usage',
      category: 'Positioning',
      impactRank: 9.0,
      description: 'Always use available cover. Peek and return after each shot.',
      reps: 12,
      durationMinutes: 6,
    },
    {
      id: 'rotation-defense',
      name: 'Defensive Rotation',
      category: 'Movement',
      impactRank: 8.6,
      description: 'Rotate to zone edge before circle closes.',
      reps: 8,
      durationMinutes: 6,
    },
  ],
  'fortnite': [
    {
      id: 'box-defense',
      name: 'Box Fight Defense',
      category: 'Building',
      impactRank: 8.8,
      description: 'Cone-stack defense. Replace pieces faster than they break them.',
      reps: 10,
      durationMinutes: 6,
    },
    {
      id: 'high-ground-retake',
      name: 'High Ground Retake',
      category: 'Building',
      impactRank: 8.4,
      description: 'Retake high without dying. Trigger the cone-90.',
      reps: 8,
      durationMinutes: 6,
    },
  ],
  'ufc-5': [
    {
      id: 'parry-timing',
      name: 'Parry Timing',
      category: 'Striking Defense',
      impactRank: 9.3,
      description: 'Time the parry to the punch frame.',
      reps: 12,
      durationMinutes: 6,
    },
    {
      id: 'head-movement',
      name: 'Head Movement',
      category: 'Striking Defense',
      impactRank: 8.8,
      description: 'Move off the centre line after every exchange.',
      reps: 10,
      durationMinutes: 6,
    },
    {
      id: 'takedown-defense',
      name: 'Takedown Defense',
      category: 'Grappling Defense',
      impactRank: 8.5,
      description: 'Sprawl the moment you feel the shoot. Hip back, weight forward.',
      reps: 10,
      durationMinutes: 7,
    },
  ],
  'pga-2k25': [
    {
      id: 'lay-up-decision',
      name: 'Lay Up Decision-Making',
      category: 'Course Management',
      impactRank: 8.0,
      description: 'When in trouble, lay up to your favourite yardage. No hero shots.',
      reps: 8,
      durationMinutes: 5,
    },
  ],
  'undisputed': [
    {
      id: 'shoulder-roll',
      name: 'Shoulder Roll Counter',
      category: 'Striking Defense',
      impactRank: 8.6,
      description: 'Slip the right hand off the shoulder, fire the lead hook.',
      reps: 10,
      durationMinutes: 6,
    },
    {
      id: 'block-timing',
      name: 'Block Timing',
      category: 'Striking Defense',
      impactRank: 8.0,
      description: 'Block low when the body shot is wound up.',
      reps: 10,
      durationMinutes: 5,
    },
  ],
  'video-poker': [
    {
      id: 'loss-limit',
      name: 'Loss Limit Discipline',
      category: 'Risk Management',
      impactRank: 9.0,
      description: 'When you hit your loss limit, walk. Every time.',
      reps: 5,
      durationMinutes: 4,
    },
  ],
};
