'use client';

import { ListOrdered } from 'lucide-react';

interface ScriptedPlay {
  name: string;
  formation: string;
  callWhen: string;
}

const OPENING_DRIVE_SCRIPT: ScriptedPlay[] = [
  { name: 'PA Crossers', formation: 'Gun Trips TE', callWhen: 'Opening snap — establish play-action threat' },
  { name: 'HB Dive', formation: 'Singleback Ace', callWhen: '2nd series — test run defense commitment' },
  { name: 'Mesh Concept', formation: 'Shotgun Bunch', callWhen: 'If Cover 3 shown on plays 1-2' },
  { name: 'RPO Bubble', formation: 'Shotgun Trips', callWhen: 'Quick tempo change — read the OLB' },
  { name: 'Levels Sail', formation: 'Gun Trey Open', callWhen: '3rd down conversion situation' },
  { name: 'Four Verticals', formation: 'Gun Empty', callWhen: 'If opponent drops 7+ into coverage' },
  { name: 'HB Screen', formation: 'Singleback Deuce Close', callWhen: 'After 2+ pass plays — punish the rush' },
  { name: 'Corner Strike', formation: 'Gun Trips TE', callWhen: 'Red zone opportunity — attack Cover 2 void' },
];

interface First15ScriptViewProps {
  opponentName: string;
}

export default function First15ScriptView({ opponentName }: First15ScriptViewProps) {
  return (
    <div className="rounded-xl border border-forge-800/50 bg-gradient-to-b from-forge-950/40 to-dark-900/80 p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-forge-500/20 border border-forge-500/30 flex items-center justify-center">
          <ListOrdered className="w-5 h-5 text-forge-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-forge-400">Opening Drive Script</h2>
          <p className="text-sm text-dark-400">
            InstallAI-generated call sequence vs{' '}
            <span className="text-dark-200 font-medium">{opponentName}</span>
          </p>
        </div>
      </div>

      <div className="space-y-1">
        {OPENING_DRIVE_SCRIPT.map((play, i) => (
          <div
            key={i}
            className="rounded-lg border border-dark-700/50 bg-dark-900/60 px-4 py-3 flex items-start gap-4"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-forge-500/20 text-xs font-black text-forge-400 flex-shrink-0">
              {i + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-dark-100">{play.name}</p>
              <p className="text-sm text-dark-400">{play.formation}</p>
              <p className="text-xs text-amber-400/80 mt-1">Call when: {play.callWhen}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
