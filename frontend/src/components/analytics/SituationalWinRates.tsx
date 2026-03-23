"use client";

import { Zap, TrendingUp, TrendingDown, Minus } from "lucide-react";

type Trend = "up" | "down" | "stable";

interface SituationCard {
  label: string;
  rate: number;
  target: number;
  trend: Trend;
}

const situations: SituationCard[] = [
  { label: "3rd Down Conversion", rate: 62, target: 65, trend: "up" },
  { label: "Red Zone Efficiency", rate: 54, target: 70, trend: "down" },
  { label: "2-Min Drill Win Rate", rate: 71, target: 60, trend: "up" },
  { label: "4th Quarter Close Rate", rate: 48, target: 55, trend: "down" },
  { label: "Comeback Rate", rate: 33, target: 40, trend: "stable" },
  { label: "Opening Drive Score Rate", rate: 68, target: 55, trend: "up" },
];

function getRateColor(rate: number, target: number): string {
  if (rate >= target) return "text-green-400";
  if (rate >= target - 10) return "text-amber-400";
  return "text-red-400";
}

function TrendIcon({ trend }: { trend: Trend }) {
  switch (trend) {
    case "up":
      return <TrendingUp className="h-4 w-4 text-forge-400" />;
    case "down":
      return <TrendingDown className="h-4 w-4 text-red-400" />;
    case "stable":
      return <Minus className="h-4 w-4 text-dark-400" />;
  }
}

export default function SituationalWinRates() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="mb-4 flex items-center gap-2">
        <Zap className="h-5 w-5 text-forge-400" />
        <h2 className="text-lg font-semibold text-white">
          Situational Win Rates
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {situations.map((s) => (
          <div
            key={s.label}
            className="cursor-pointer rounded-lg border border-dark-700/50 bg-dark-800/50 p-4 transition-colors hover:border-dark-500"
          >
            <p className="text-sm font-medium text-dark-200">{s.label}</p>

            <div className="mt-2 flex items-center justify-between">
              <span
                className={`font-mono text-2xl font-bold ${getRateColor(s.rate, s.target)}`}
              >
                {s.rate}%
              </span>
              <TrendIcon trend={s.trend} />
            </div>

            <p className="mt-1 text-[10px] text-dark-500">
              vs target: {s.target}%
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
