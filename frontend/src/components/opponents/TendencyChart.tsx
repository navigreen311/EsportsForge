'use client';

import { TendencyBreakdown } from '@/types/opponent';

interface TendencyChartProps {
  tendencies: TendencyBreakdown[];
  category: 'offense' | 'defense';
  label: string;
  barColor: string;
}

export default function TendencyChart({
  tendencies,
  category,
  label,
  barColor,
}: TendencyChartProps) {
  const filtered = tendencies.filter((t) => t.category === category);

  return (
    <div>
      <h3 className="text-sm font-medium mb-3" style={{ color: barColor }}>
        {label}
      </h3>
      <div className="space-y-2.5">
        {filtered.map((t) => (
          <div key={t.label} className="flex items-center gap-3">
            <span className="text-sm text-dark-300 w-32 truncate" title={t.label}>
              {t.label}
            </span>
            <div className="flex-1 bg-dark-800 rounded-full h-2.5">
              <div
                className="h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${t.percentage}%`, backgroundColor: barColor }}
              />
            </div>
            <span className="text-xs font-mono text-dark-400 w-10 text-right">
              {t.percentage}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
