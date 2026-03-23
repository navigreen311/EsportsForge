"use client";

import { Flame } from "lucide-react";
import clsx from "clsx";

/* ------------------------------------------------------------------ */
/*  Mock data                                                         */
/* ------------------------------------------------------------------ */

const MOCK_STREAK = 7; // days — 0 means no active streak
const MOCK_LAST_DRILLED_DAYS_AGO = 2;

const MOCK_SKILL_HISTORY: Record<string, boolean[]> = {
  "Read Speed": [true, true, false, true, true, false, true],
  "Aim Precision": [true, false, true, true, false, true, true],
  "Map Awareness": [false, false, true, true, true, false, false],
};

const MOCK_MONTHLY_DAYS = 18;
const MOCK_MONTHLY_TOTAL = 30;

/* ------------------------------------------------------------------ */
/*  1. DrillStreak                                                    */
/* ------------------------------------------------------------------ */

export function DrillStreak() {
  const streak = MOCK_STREAK;
  const isActive = streak > 0;

  return (
    <span className="inline-flex items-center gap-1.5 text-sm font-medium">
      {isActive ? (
        <>
          <Flame className="h-4 w-4 text-orange-400" />
          <span>{streak}-day streak</span>
        </>
      ) : (
        <span className="text-dark-400">
          Last drilled: {MOCK_LAST_DRILLED_DAYS_AGO}d ago
        </span>
      )}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/*  2. SkillConsistency                                               */
/* ------------------------------------------------------------------ */

interface SkillConsistencyProps {
  skillName: string;
}

export function SkillConsistency({ skillName }: SkillConsistencyProps) {
  const days = MOCK_SKILL_HISTORY[skillName] ?? Array(7).fill(false);
  const drilledCount = days.filter(Boolean).length;

  return (
    <div className="flex flex-col gap-1">
      <div className="inline-flex items-center gap-1">
        {days.map((drilled, i) => (
          <div
            key={i}
            className={clsx(
              "h-2 w-2 rounded-full",
              drilled ? "bg-forge-400" : "bg-dark-700",
            )}
          />
        ))}
      </div>
      <span className="text-xs text-dark-400">
        Drilled {drilledCount} of last 7 days
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  3. MonthlyConsistency                                             */
/* ------------------------------------------------------------------ */

function getConsistencyColor(days: number): string {
  if (days >= 20) return "bg-green-500";
  if (days >= 10) return "bg-amber-500";
  return "bg-red-500";
}

function getConsistencyLabel(days: number): string {
  if (days >= 20) return "great consistency";
  if (days >= 10) return "good consistency";
  return "needs improvement";
}

export function MonthlyConsistency() {
  const days = MOCK_MONTHLY_DAYS;
  const total = MOCK_MONTHLY_TOTAL;
  const pct = Math.round((days / total) * 100);

  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-dark-400">
        Monthly Consistency: {days}/{total} days &mdash;{" "}
        {getConsistencyLabel(days)}
      </span>
      <div className="h-1 w-full rounded-full bg-dark-700">
        <div
          className={clsx("h-1 rounded-full", getConsistencyColor(days))}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
