'use client';

import { ChevronDown } from 'lucide-react';
import { useState } from 'react';

interface WhyThisDrillProps {
  drillId: string;
}

interface DrillRationale {
  damage: number;
  lift: number;
  why: string;
  weakness: string;
}

const mockData: Record<string, DrillRationale> = {
  'drill-1': {
    damage: -8.3,
    lift: 5.7,
    why: 'Your coverage recognition miss rate in ranked games is 3x your drill rate — this gap is costing wins',
    weakness: 'Coverage Read Speed',
  },
  'drill-2': {
    damage: -6.1,
    lift: 4.2,
    why: 'Clutch conversion rate drops 40% in final 2 minutes — you need reps under time pressure',
    weakness: 'Clutch Performance',
  },
  'drill-3': {
    damage: -4.8,
    lift: 3.5,
    why: 'Meta coverage schemes are beating you 62% of the time — your route combos need updating',
    weakness: 'Anti-Meta Adaptability',
  },
  'drill-4': {
    damage: -3.9,
    lift: 2.8,
    why: 'You hold the ball 0.4s too long under pressure — faster decisions save sacks',
    weakness: 'Pocket Awareness',
  },
  'drill-5': {
    damage: -5.1,
    lift: 3.9,
    why: 'Red zone TD rate 41% vs 59% league avg — leaving points on the field',
    weakness: 'Red Zone Efficiency',
  },
};

export default function WhyThisDrill({ drillId }: WhyThisDrillProps) {
  const [expanded, setExpanded] = useState(false);
  const data = mockData[drillId];

  if (!data) return null;

  return (
    <div className="rounded-lg border border-dark-700/50 bg-dark-800/30 p-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-sm text-dark-400 hover:text-dark-200 transition-colors"
      >
        <ChevronDown
          className={`w-4 h-4 transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
          }`}
        />
        Why this drill?
      </button>

      {expanded && (
        <div className="mt-3 space-y-3">
          {/* Damage / Lift grid */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[10px] text-dark-500 uppercase tracking-wider mb-0.5">
                Win-Rate Damage
              </p>
              <p className="text-lg font-bold text-red-400">
                {data.damage}%
              </p>
            </div>
            <div>
              <p className="text-[10px] text-dark-500 uppercase tracking-wider mb-0.5">
                Expected Lift
              </p>
              <p className="text-lg font-bold text-green-400">
                +{data.lift}%
              </p>
            </div>
          </div>

          {/* Why now */}
          <div>
            <p className="text-[10px] text-dark-500 uppercase tracking-wider mb-0.5">
              Why Now
            </p>
            <p className="text-sm text-dark-300 leading-relaxed">
              {data.why}
            </p>
          </div>

          {/* Connected weakness */}
          <div>
            <p className="text-[10px] text-dark-500 uppercase tracking-wider mb-0.5">
              Connected Weakness
            </p>
            <a
              href="/analytics/weakness-heatmap"
              className="text-sm font-medium text-forge-400 hover:text-forge-300 transition-colors"
            >
              {data.weakness} →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
