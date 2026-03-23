'use client';

import { useState } from 'react';
import { FileText, Database, AlertTriangle, Users, ChevronDown } from 'lucide-react';
import clsx from 'clsx';

interface EvidencePanelProps {
  playId: string;
}

export const PLAY_EVIDENCE: Record<string, { why: string; data: string; risk: string; comparable: string }> = {
  'play-1': {
    why: 'PA Crossers exploits Cover 3 void between LBs and safety, xXDragonSlayerXx runs Cover 3 68% of the time',
    data: 'xXDragonSlayerXx Cover 3 shell: 68% of the time in last 8 games',
    risk: 'Vulnerable to Cover 2 Man with safety help over the top — corner route is the counter',
    comparable: 'Similar result vs GridironGhost — worked 3/3 times in W14',
  },
  'play-2': {
    why: 'Inside Zone targets weak run fits when opponent stacks the box with only 6 defenders',
    data: 'Opponent 6-man box rate: 54% on 1st & 10 situations',
    risk: 'Stuffed consistently by Pinch Buck O — audible to a quick pass if they shift pre-snap',
    comparable: 'Similar result vs BlitzMaster99 — averaged 6.2 YPC in W11',
  },
  'play-3': {
    why: 'Corner Strike beats Cover 2 flat zones by attacking the void behind the corner and in front of the safety',
    data: 'Opponent Cover 2 usage: 41% on 2nd & medium',
    risk: 'Picked off if safety reads the route early — pump fake or check down is the bail-out',
    comparable: 'Similar result vs NeonEndzone — 2 TDs in W9',
  },
  'play-4': {
    why: 'HB Stretch exploits slow edge containment when opponent runs Cover 4 with no edge blitz',
    data: 'Opponent edge contain failure rate: 37% in last 5 games',
    risk: 'Blown up by outside blitz or aggressive DE — flip the run direction or pass-protect',
    comparable: 'Similar result vs ShadowRush42 — 3 runs of 15+ yards in W12',
  },
  'play-5': {
    why: 'Levels Concept floods the short-to-intermediate zones, overwhelming Cover 3 underneath defenders',
    data: 'Opponent Cover 3 underneath completion rate allowed: 72% over last 6 games',
    risk: 'Zone blitz disguises can take away the intermediate read — hot route the RB as a safety valve',
    comparable: 'Similar result vs TurboTactician — 8/10 completions in W10',
  },
  'play-6': {
    why: 'Power Run exploits A-gap weakness when opponent consistently shifts LBs outside pre-snap',
    data: 'Opponent A-gap run stop rate: only 31% in last 4 games',
    risk: 'DT nose tackle sheds blocks fast — combo block needed or audible to draw play',
    comparable: 'Similar result vs IronCurtainD — 2 rushing TDs in W13',
  },
  'play-7': {
    why: 'Mesh Concept creates natural picks against man coverage, exploiting aggressive CB play',
    data: 'Opponent man coverage rate: 59% in red zone situations',
    risk: 'Switch coverage or bracket assignments neutralize the mesh — read the safety rotation',
    comparable: 'Similar result vs PressKing88 — 4/4 red zone conversions in W8',
  },
  'play-8': {
    why: 'Four Verticals stretches Cover 2 safeties and creates 1-on-1 matchups down the seam',
    data: 'Opponent Cover 2 safety split: averages 28 yards apart at snap',
    risk: 'Cover 4 or quarters takes away deep shots — check to crossers underneath',
    comparable: 'Similar result vs SkyCoverTwo — 2 deep TDs in W15',
  },
  'play-9': {
    why: 'RPO Bubble exploits overly aggressive LB flow toward the run, leaving the flat wide open',
    data: 'Opponent LB bite rate on play-action: 74% on early downs',
    risk: 'Flat defender sits on the bubble — keep the ball on the run if the DE crashes',
    comparable: 'Similar result vs BlitzHappyDave — 5 completions for 67 yards in W7',
  },
  'play-10': {
    why: 'Singleback Dive attacks the interior when opponent plays light boxes in nickel formations',
    data: 'Opponent nickel formation rate: 63% on standard downs',
    risk: 'Interior stunts and delayed blitzes can blow up the play — slide protection or use a lead blocker',
    comparable: 'Similar result vs NickelNightmare — 4.8 YPC and 2 TDs in W6',
  },
};

const EVIDENCE_ITEMS = [
  { key: 'why' as const, label: 'WHY', icon: FileText, labelColor: 'text-dark-200' },
  { key: 'data' as const, label: 'DATA', icon: Database, labelColor: 'text-dark-200' },
  { key: 'risk' as const, label: 'RISK', icon: AlertTriangle, labelColor: 'text-amber-400' },
  { key: 'comparable' as const, label: 'COMPARABLE', icon: Users, labelColor: 'text-dark-200' },
];

export default function EvidencePanel({ playId }: EvidencePanelProps) {
  const [expanded, setExpanded] = useState(true);

  const evidence = PLAY_EVIDENCE[playId];

  if (!evidence) return null;

  return (
    <div className="rounded-lg border border-dark-700/50 bg-dark-800/30 p-3 space-y-2">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between"
      >
        <div className="flex items-center gap-1.5">
          <FileText className="h-3 w-3 text-dark-500" />
          <span className="text-[11px] font-medium text-dark-200">Evidence</span>
        </div>
        <ChevronDown
          className={clsx(
            'h-3 w-3 text-dark-500 transition-transform',
            expanded && 'rotate-180'
          )}
        />
      </button>

      {expanded && (
        <div className="space-y-2">
          {EVIDENCE_ITEMS.map(({ key, label, icon: Icon, labelColor }) => (
            <div key={key} className="flex flex-row items-start gap-2">
              <Icon className="h-3 w-3 text-dark-500 mt-0.5 shrink-0" />
              <div className="flex flex-col gap-0.5">
                <span className={clsx('text-[11px] font-medium', labelColor)}>{label}</span>
                <span className="text-[11px] text-dark-300">{evidence[key]}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
