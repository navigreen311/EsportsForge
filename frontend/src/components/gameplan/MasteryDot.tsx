"use client";

import clsx from "clsx";

type MasteryLevel = "mastered" | "practicing" | "learning" | "not-installed";

export const PLAY_MASTERY: Record<string, MasteryLevel> = {
  "play-1": "mastered",
  "play-2": "mastered",
  "play-3": "practicing",
  "play-4": "learning",
  "play-5": "mastered",
  "play-6": "not-installed",
  "play-7": "practicing",
  "play-8": "mastered",
  "play-9": "learning",
  "play-10": "not-installed",
};

const MASTERY_STYLES: Record<MasteryLevel, string> = {
  mastered: "bg-forge-400",
  practicing: "bg-amber-400",
  learning: "bg-dark-400",
  "not-installed": "border border-dark-600 bg-transparent",
};

const MASTERY_TOOLTIPS: Record<MasteryLevel, string> = {
  mastered:
    "Mastery: Competition Ready \u2014 confirmed by TransferAI across 12 ranked games",
  practicing:
    "Mastery: Practicing \u2014 67% drill accuracy, building ranked reps",
  learning:
    "Mastery: Learning \u2014 installed in drills, not yet tested in ranked",
  "not-installed": "Not installed \u2014 add to drill queue",
};

interface MasteryDotProps {
  playId: string;
}

export function MasteryDot({ playId }: MasteryDotProps) {
  const level: MasteryLevel = PLAY_MASTERY[playId] ?? "not-installed";

  return (
    <div className="absolute top-2 right-2" title={MASTERY_TOOLTIPS[level]}>
      <div
        className={clsx("h-1.5 w-1.5 rounded-full", MASTERY_STYLES[level])}
      />
    </div>
  );
}
