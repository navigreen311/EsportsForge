'use client';

import type { AudibleNode } from '@/types/gameplan';
import { ArrowDown } from 'lucide-react';

// Fallback Layer-3 counters, keyed by audible id — used only when an audible
// carries no plain-language counter (counterLookFor/counterDo) of its own.
export const LAYER3_COUNTERS: Record<string, string> = {
  'aud-1a': 'HB Dive — punish light box if they over-rotate to coverage',
  'aud-1b': 'PA Boot Over — roll out opposite if blitz persists',
  'aud-2a': 'Power Run — attack the gap vacated by aggressive LB',
  'aud-3a': 'Spot Concept — triangle read exploits single-high rotation',
  'aud-5a': 'Four Verticals — punish aggressive LB coverage drops',
  'aud-6a': 'HB Screen — dump behind overcommitting rush',
  'aud-8a': 'RPO Bubble — quick release to beat press',
  'aud-10a': 'Levels Sail — stretch the zone underneath',
};

interface ThreeLayerAudibleProps {
  playName: string;
  /** One-line "read" for the base call (Layer 1). */
  baseRead?: string;
  audibles: AudibleNode[];
}

function LayerConnector() {
  return (
    <div className="flex justify-center py-1">
      <div className="flex flex-col items-center">
        <div className="w-px h-3 bg-dark-600" />
        <ArrowDown className="w-4 h-4 text-dark-500" />
      </div>
    </div>
  );
}

/** A labeled micro-line: LOOK FOR / HOW TO TELL / DO. */
function ReadLine({ label, text }: { label: string; text: string }) {
  return (
    <div className="flex gap-2 text-xs">
      <span className="w-[4.5rem] shrink-0 pt-px text-[10px] font-semibold uppercase tracking-wider text-dark-500">
        {label}
      </span>
      <span className="flex-1 text-dark-300">{text}</span>
    </div>
  );
}

function hasReadDepth(a: AudibleNode): boolean {
  return Boolean(a.lookFor || a.recognize || a.do);
}
function hasCounterDepth(a: AudibleNode): boolean {
  return Boolean(a.counterLookFor || a.counterDo);
}

export default function ThreeLayerAudible({
  playName,
  baseRead,
  audibles,
}: ThreeLayerAudibleProps) {
  return (
    <div className="space-y-3">
      {/* LAYER 1 — Base Call */}
      <div className="rounded-lg border border-forge-500/30 bg-forge-500/5 p-3">
        <span className="text-[10px] uppercase tracking-wider text-forge-400">
          LAYER 1 — Base Call
        </span>
        <p className="text-sm font-bold text-dark-100">{playName}</p>
        {baseRead && (
          <p className="mt-1 text-xs leading-relaxed text-dark-300">{baseRead}</p>
        )}
      </div>

      {audibles.length > 0 && (
        <>
          <LayerConnector />

          {/* LAYER 2 — If the pre-snap look is wrong, change the play */}
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
            <span className="text-[10px] uppercase tracking-wider text-amber-400">
              LAYER 2 — If the look is wrong, change the play
            </span>
            <div className="mt-2 space-y-3">
              {audibles.map((audible) => (
                <div key={audible.id} className="flex flex-col gap-1">
                  <span className="font-medium text-dark-200">{audible.label}</span>
                  {hasReadDepth(audible) ? (
                    <div className="flex flex-col gap-1">
                      {audible.lookFor && <ReadLine label="Look for" text={audible.lookFor} />}
                      {audible.recognize && (
                        <ReadLine label="How to tell" text={audible.recognize} />
                      )}
                      {audible.do && <ReadLine label="Do" text={audible.do} />}
                    </div>
                  ) : (
                    <>
                      <span className="text-xs text-amber-400/80">when {audible.trigger}</span>
                      <span className="text-xs text-forge-400">
                        audible to {audible.targetPlay}
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>

          <LayerConnector />

          {/* LAYER 3 — If they adjust to your adjustment */}
          <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
            <span className="text-[10px] uppercase tracking-wider text-red-400">
              LAYER 3 — If they adjust to your adjustment
            </span>
            <div className="mt-2 space-y-3">
              {audibles.map((audible) => (
                <div key={audible.id} className="flex flex-col gap-1">
                  <span className="font-medium text-dark-200">{audible.label}</span>
                  {hasCounterDepth(audible) ? (
                    <div className="flex flex-col gap-1">
                      {audible.counterLookFor && (
                        <ReadLine label="Look for" text={audible.counterLookFor} />
                      )}
                      {audible.counterDo && <ReadLine label="Do" text={audible.counterDo} />}
                    </div>
                  ) : (
                    <span className="text-xs text-dark-300">
                      {LAYER3_COUNTERS[audible.id] ??
                        'Counter: run a draw play to punish over-pursuit'}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
