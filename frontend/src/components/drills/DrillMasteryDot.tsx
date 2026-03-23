"use client";

import clsx from "clsx";

type DrillMasteryLevel =
  | "mastered"
  | "practicing"
  | "learning"
  | "not-started";

export const DRILL_MASTERY: Record<string, DrillMasteryLevel> = {
  "drill-1": "practicing",
  "drill-2": "learning",
  "drill-3": "not-started",
  "drill-4": "not-started",
  "drill-5": "learning",
};

const MASTERY_STYLES: Record<DrillMasteryLevel, string> = {
  mastered: "bg-forge-400",
  practicing: "bg-amber-400",
  learning: "bg-dark-400",
  "not-started": "border border-dark-500 bg-transparent",
};

const MASTERY_TOOLTIPS: Record<DrillMasteryLevel, string> = {
  mastered: "Mastery: Mastered \u2014 competition verified",
  practicing: "Mastery: Practicing \u2014 6/10 required ranked sessions",
  learning: "Mastery: Learning \u2014 drill reps building",
  "not-started": "Not started",
};

interface DrillMasteryDotProps {
  drillId: string;
}

export function DrillMasteryDot({ drillId }: DrillMasteryDotProps) {
  const level: DrillMasteryLevel = DRILL_MASTERY[drillId] ?? "not-started";

  return (
    <div className="absolute top-2 right-2" title={MASTERY_TOOLTIPS[level]}>
      <div
        className={clsx("h-2 w-2 rounded-full", MASTERY_STYLES[level])}
      />
    </div>
  );
}
