/**
 * FirstFifteenScript — Opening 15 plays in order with rationale.
 * Full scripted opening drive with reasoning for each call.
 */

'use client';

import { ListOrdered, Info } from 'lucide-react';
import { useState } from 'react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';

interface ScriptedPlay {
  name: string;
  formation: string;
  rationale: string;
  expectedYards: string;
}

const FIRST_FIFTEEN: ScriptedPlay[] = [
  { name: 'PA Crossers', formation: 'Gun Trips TE', rationale: 'Establish play-action threat early; opponent bites on run fakes 74% of openers', expectedYards: '8-12' },
  { name: 'HB Dive', formation: 'Singleback Ace', rationale: 'Test interior run defense commitment after PA look', expectedYards: '3-5' },
  { name: 'Mesh Concept', formation: 'Shotgun Bunch', rationale: 'Exploit man coverage tendency shown on 1st drive 68% of the time', expectedYards: '6-9' },
  { name: 'RPO Bubble', formation: 'Shotgun Trips', rationale: 'Quick tempo change — OLB overcommits to run on 2nd-and-short 71% of the time', expectedYards: '5-8' },
  { name: 'Levels Sail', formation: 'Gun Trey Open', rationale: 'Flood the short zones on 3rd down; 83% conversion rate vs this opponent shell', expectedYards: '7-11' },
  { name: 'HB Stretch', formation: 'Singleback Deuce', rationale: 'Attack edge after 4 pass plays — opponent DE crashes inside 62% in this spot', expectedYards: '4-7' },
  { name: 'Four Verticals', formation: 'Gun Empty', rationale: 'Take a shot if single-high safety — opponent shows Cover 1 after run success 58%', expectedYards: '15-40' },
  { name: 'HB Screen', formation: 'Singleback Deuce Close', rationale: 'Punish aggressive pass rush — opponent blitzes 3rd-and-long 81% of the time', expectedYards: '6-12' },
  { name: 'Corner Strike', formation: 'Gun Trips TE', rationale: 'Red zone opportunity — attacks Cover 2 void between CB and safety', expectedYards: '10-20' },
  { name: 'Power Run', formation: 'I-Form Pro', rationale: 'Establish physicality; opponent A-gap stop rate only 31% in recent games', expectedYards: '4-6' },
  { name: 'Smash Concept', formation: 'Shotgun Doubles', rationale: 'High-low the corner — works vs both Cover 2 and Cover 4 shells', expectedYards: '8-15' },
  { name: 'Draw Play', formation: 'Shotgun Empty (shift)', rationale: 'Opponent over-pursues after empty formation shown; draw gashes for 7+ yards 44% of the time', expectedYards: '5-10' },
  { name: 'Post-Wheel', formation: 'Gun Trips TE', rationale: 'Seam shot vs Cover 3 — high probability after establishing short game', expectedYards: '12-25' },
  { name: 'Singleback Sweep', formation: 'Singleback Wing', rationale: 'Change the point of attack to the boundary after heavy field-side looks', expectedYards: '4-8' },
  { name: 'PA Shot Play', formation: 'Gun Doubles', rationale: 'End-of-script shot — opponent safeties bite on play-action after heavy run in plays 10-14', expectedYards: '20-40' },
];

export default function FirstFifteenScript() {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  return (
    <Card padding="md">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-forge-500/10 border border-forge-500/20">
            <ListOrdered className="h-5 w-5 text-forge-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-dark-100">First 15 Script</h3>
            <p className="text-[10px] text-dark-500">Opening drive call sequence with rationale</p>
          </div>
        </div>

        {/* Script list */}
        <div className="space-y-1">
          {FIRST_FIFTEEN.map((play, i) => {
            const isExpanded = expandedIdx === i;
            return (
              <div
                key={i}
                className="rounded-lg border border-dark-700/50 bg-dark-900/60 overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => setExpandedIdx(isExpanded ? null : i)}
                  className="flex w-full items-center gap-3 px-3 py-2.5 text-left hover:bg-dark-800/50 transition-colors"
                >
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-forge-500/20 text-[10px] font-black text-forge-400 flex-shrink-0">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-dark-100">{play.name}</span>
                    <span className="ml-2 text-xs text-dark-500">{play.formation}</span>
                  </div>
                  <span className="text-[10px] text-dark-500 tabular-nums flex-shrink-0">
                    ~{play.expectedYards} yds
                  </span>
                  <Info
                    className={clsx(
                      'h-3.5 w-3.5 flex-shrink-0 transition-colors',
                      isExpanded ? 'text-forge-400' : 'text-dark-600'
                    )}
                  />
                </button>

                {isExpanded && (
                  <div className="border-t border-dark-700/50 px-3 py-2 bg-dark-800/30">
                    <p className="text-xs text-dark-300 leading-relaxed">
                      <span className="font-semibold text-dark-200">Rationale:</span>{' '}
                      {play.rationale}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
