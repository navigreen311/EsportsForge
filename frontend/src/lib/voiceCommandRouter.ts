export interface VoiceCommand {
  patterns: string[];
  action: string;
  navigate: string | null;
  description: string;
}

export const VOICE_COMMANDS: VoiceCommand[] = [
  {
    patterns: ['generate gameplan', 'make gameplan', 'build gameplan'],
    action: 'GENERATE_GAMEPLAN',
    navigate: '/gameplan',
    description: 'Opening Gameplan page',
  },
  {
    patterns: ['start drill', 'begin drill', 'drill time'],
    action: 'START_DRILL',
    navigate: '/drills',
    description: 'Opening Drill Lab',
  },
  {
    patterns: ['scout opponent', 'show opponents', 'open opponents'],
    action: 'OPEN_OPPONENTS',
    navigate: '/opponents',
    description: 'Opening Opponents',
  },
  {
    patterns: ['show dashboard', 'go home', 'dashboard'],
    action: 'GO_DASHBOARD',
    navigate: '/dashboard',
    description: 'Going to Dashboard',
  },
  {
    patterns: ['show kill sheet', 'kill sheet'],
    action: 'SHOW_KILL_SHEET',
    navigate: null,
    description: 'Opening Kill Sheet',
  },
  {
    patterns: ['next drill', 'skip drill'],
    action: 'NEXT_DRILL',
    navigate: null,
    description: 'Skipping to next drill',
  },
  {
    patterns: ['read briefing', 'briefing', 'what should i do', 'give me my plan'],
    action: 'READ_BRIEFING',
    navigate: null,
    description: 'Reading your briefing',
  },
  {
    patterns: ['end session', 'stop session', 'session complete'],
    action: 'END_SESSION',
    navigate: null,
    description: 'Ending session',
  },
  {
    patterns: ['show analytics', 'analytics', 'show stats'],
    action: 'SHOW_ANALYTICS',
    navigate: '/analytics',
    description: 'Opening Analytics',
  },
];

export function matchVoiceCommand(transcript: string): VoiceCommand | null {
  const lower = transcript.toLowerCase();

  for (const command of VOICE_COMMANDS) {
    for (const pattern of command.patterns) {
      if (lower.includes(pattern)) {
        return command;
      }
    }
  }

  return null;
}
