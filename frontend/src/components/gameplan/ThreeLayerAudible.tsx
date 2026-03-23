'use client';

import type { AudibleNode } from '@/types/gameplan';
import { ArrowDown } from 'lucide-react';
import clsx from 'clsx';

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

export default function ThreeLayerAudible({ playName, audibles }: ThreeLayerAudibleProps) {
  return (
    <div className="space-y-3">
      {/* LAYER 1 — Base Call */}
      <div className="rounded-lg border border-forge-500/30 bg-forge-500/5 p-3">
        <span className="text-[10px] uppercase tracking-wider text-forge-400">
          LAYER 1 — Base Call
        </span>
        <p className="text-sm font-bold text-dark-100">{playName}</p>
      </div>

      {audibles.length > 0 && (
        <>
          <LayerConnector />

          {/* LAYER 2 — If Bagged */}
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
            <span className="text-[10px] uppercase tracking-wider text-amber-400">
              LAYER 2 — If Bagged
            </span>
            <div className="mt-2 space-y-2">
              {audibles.map((audible) => (
                <div key={audible.id} className="flex flex-col gap-0.5">
                  <span className="font-medium text-dark-200">{audible.label}</span>
                  <span className="text-xs text-amber-400/80">when {audible.trigger}</span>
                  <span className="text-xs text-forge-400">audible to {audible.targetPlay}</span>
                </div>
              ))}
            </div>
          </div>

          <LayerConnector />

          {/* LAYER 3 — If They Adjust */}
          <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
            <span className="text-[10px] uppercase tracking-wider text-red-400">
              LAYER 3 — If They Adjust
            </span>
            <div className="mt-2 space-y-2">
              {audibles.map((audible) => (
                <div key={audible.id} className="text-xs text-dark-300">
                  <span className="font-medium text-dark-200">{audible.label}:</span>{' '}
                  {LAYER3_COUNTERS[audible.id] ??
                    'Counter: Run a draw play to punish over-pursuit'}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
