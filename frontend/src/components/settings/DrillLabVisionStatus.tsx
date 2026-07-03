'use client';

import { Info } from 'lucide-react';

import { drillLabVisionEnabled } from '@/lib/vafFlags';

/**
 * Read-only exposure of the Drill Lab live-vision flag (ADR 0001: env-var flag,
 * engineer-controlled, no in-app flip). Displays the SAME value the Drill Lab
 * page enforces (both call `drillLabVisionEnabled`). Intentionally has NO
 * interactive control — a flip UI would diverge from ADR 0001.
 */
export default function DrillLabVisionStatus() {
  const on = drillLabVisionEnabled();
  return (
    <div data-testid="drill-lab-vision-status">
      <label className="block text-sm font-medium text-dark-300 mb-1.5">
        Drill Lab Live Vision
      </label>
      <div className="flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800 px-3 py-2">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${
            on ? 'bg-emerald-500/15 text-emerald-400' : 'bg-dark-700 text-dark-400'
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${on ? 'bg-emerald-400' : 'bg-dark-500'}`} />
          {on ? 'On' : 'Off'}
        </span>
        <span className="text-sm text-dark-300">{on ? 'Enabled' : 'Disabled'}</span>
      </div>
      <p className="text-xs text-dark-500 mt-1 flex items-center gap-1">
        <Info className="w-3 h-3" /> Engineer-controlled (deployment config, ADR 0001) — not
        toggleable in-app.
      </p>
    </div>
  );
}
