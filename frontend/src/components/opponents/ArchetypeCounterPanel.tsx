'use client';

import { Modal } from '@/components/shared/Modal';
import { Shield, Zap } from 'lucide-react';

interface ArchetypeCounterPanelProps {
  archetype: string;
  opponentName: string;
  open: boolean;
  onClose: () => void;
}

interface CounterPlay {
  name: string;
  formation: string;
}

interface CounterPackage {
  plays: CounterPlay[];
  defenseScheme: string;
  keyAdjustment: string;
}

const counterPackages: Record<string, CounterPackage> = {
  'Aggressive Rusher': {
    plays: [
      { name: 'HB Screen', formation: 'Singleback Ace' },
      { name: 'Quick Slant', formation: 'Shotgun Trips' },
      { name: 'RPO Bubble', formation: 'Gun Spread' },
      { name: 'Draw Play', formation: 'Pistol Strong' },
    ],
    defenseScheme: 'Spread formations to thin the rush lanes',
    keyAdjustment:
      'ID the blitzer pre-snap — hot route the RB to the vacated gap',
  },
  'Pocket Passer': {
    plays: [
      { name: 'Cover 3 Sky', formation: 'Nickel 3-3-5' },
      { name: 'Tampa 2 Blitz', formation: '4-3 Under' },
      { name: 'Sim Pressure', formation: 'Dollar 3-2-6' },
      { name: 'Zone Drop DE', formation: '3-4 Odd' },
    ],
    defenseScheme: 'Disguise coverages and rotate safeties post-snap',
    keyAdjustment:
      'Collapse the pocket with interior pressure — force early throws into zone windows',
  },
  'Scrambler': {
    plays: [
      { name: 'QB Spy Mike', formation: 'Nickel 2-4-5' },
      { name: 'Contain Rush', formation: '4-3 Over' },
      { name: 'Edge Set', formation: '3-4 Bear' },
      { name: 'Zone Bracket', formation: 'Big Dime' },
    ],
    defenseScheme: 'Disciplined rush lanes with spy assignments on the LB',
    keyAdjustment:
      'Never crash the DE — set the edge and force the QB back into the spy',
  },
  'Blitz Heavy': {
    plays: [
      { name: 'Max Protect', formation: 'Singleback Jumbo' },
      { name: 'Slide Protection', formation: 'Shotgun Doubles' },
      { name: 'TE Delay', formation: 'Gun Bunch TE' },
      { name: 'Wheel Route', formation: 'Pistol Weak' },
    ],
    defenseScheme: 'Keep extra blockers in and exploit vacated zones',
    keyAdjustment:
      'Identify the overload side pre-snap — slide protection toward it and leak the back opposite',
  },
  'Zone Specialist': {
    plays: [
      { name: 'Flood Concept', formation: 'Shotgun Trips TE' },
      { name: 'Smash Route', formation: 'Gun Split Close' },
      { name: 'Drive Concept', formation: 'Singleback Deuce' },
      { name: 'Levels Sail', formation: 'Gun Empty Trey' },
    ],
    defenseScheme: 'Attack zone soft spots with high-low reads',
    keyAdjustment:
      'Sit in the windows between zone defenders — use crossers to pull LBs out of position',
  },
  'Run First': {
    plays: [
      { name: 'Pinch Buck', formation: '4-4 Split' },
      { name: 'Bear Front Stuff', formation: '3-4 Bear' },
      { name: 'Safety Run Fit', formation: 'Nickel 3-3-5' },
      { name: 'LB Scrape', formation: '4-3 Under' },
    ],
    defenseScheme: 'Stack the box and force them to beat you through the air',
    keyAdjustment:
      'Set the edge aggressively — fill gaps downhill with unblocked safeties',
  },
};

const fallbackPackage: CounterPackage = {
  plays: [
    { name: 'Cover 2 Man', formation: 'Nickel Normal' },
    { name: 'Curl Flat', formation: '3-4 Odd' },
    { name: 'PA Crosser', formation: 'Singleback Ace' },
    { name: 'HB Dive', formation: 'I-Form Pro' },
  ],
  defenseScheme: 'Play sound fundamental defense and adjust after the first drive',
  keyAdjustment:
    'Study their opening script — most opponents show tendencies in the first 5 plays',
};

export default function ArchetypeCounterPanel({
  archetype,
  opponentName,
  open,
  onClose,
}: ArchetypeCounterPanelProps) {
  const pkg = counterPackages[archetype] ?? fallbackPackage;

  return (
    <Modal open={open} onClose={onClose} title={`Counter Package: ${archetype}`} size="lg">
      <div className="space-y-6">
        {/* Opponent context */}
        <p className="text-sm text-dark-400">
          Tailored counters for <span className="font-medium text-dark-200">{opponentName}</span>
        </p>

        {/* Proven Plays */}
        <section>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-dark-400">
            Proven Plays
          </h3>
          <ul className="space-y-2">
            {pkg.plays.map((play, idx) => (
              <li
                key={play.name}
                className="flex items-center gap-3 rounded-lg border border-dark-700/50 bg-dark-800/50 px-4 py-3"
              >
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-forge-500/20 text-sm font-bold text-forge-400">
                  {idx + 1}
                </span>
                <div className="min-w-0">
                  <p className="truncate font-medium text-dark-100">{play.name}</p>
                  <p className="truncate text-sm text-dark-400">{play.formation}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* Defensive Scheme */}
        <section className="rounded-lg border border-dark-700/50 bg-dark-800/50 px-4 py-3">
          <div className="mb-1 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-dark-400">
            <Shield className="h-4 w-4 text-forge-400" />
            Defensive Scheme
          </div>
          <p className="text-dark-200">{pkg.defenseScheme}</p>
        </section>

        {/* Key Adjustment */}
        <section className="rounded-lg border border-dark-700/50 bg-dark-800/50 px-4 py-3">
          <div className="mb-1 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-dark-400">
            <Zap className="h-4 w-4 text-yellow-400" />
            Key Adjustment
          </div>
          <p className="text-dark-200">{pkg.keyAdjustment}</p>
        </section>

        {/* Add to Gameplan */}
        <button
          type="button"
          className="w-full rounded-lg bg-forge-500 py-3 text-center font-bold text-white transition-colors hover:bg-forge-600 active:bg-forge-700"
        >
          Add to Gameplan
        </button>
      </div>
    </Modal>
  );
}
