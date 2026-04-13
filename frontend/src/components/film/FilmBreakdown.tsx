"use client";

import {
  Award,
  AlertTriangle,
  Zap,
  Tag,
  TrendingUp,
  Share2,
  FileDown,
  Archive,
  Crosshair,
} from "lucide-react";

interface Play {
  timestamp: string;
  playType: string;
  result: string;
  category: "Pre-snap" | "Post-snap" | "Mechanical" | "Mental" | "Scheme";
}

interface Fix {
  description: string;
  winRateImpact: string;
}

interface FilmBreakdownProps {
  result: {
    grade: string;
    topMistake: string;
    topStrength: string;
    totalPlaysTagged: number;
    plays: Play[];
    fixes: Fix[];
  };
}

function gradeColor(grade: string): string {
  if (grade.startsWith("A")) return "text-forge-400";
  if (grade.startsWith("B")) return "text-amber-400";
  return "text-red-400";
}

function gradeBg(grade: string): string {
  if (grade.startsWith("A")) return "bg-forge-400/10 border-forge-400/30";
  if (grade.startsWith("B")) return "bg-amber-400/10 border-amber-400/30";
  return "bg-red-400/10 border-red-400/30";
}

function categoryColor(category: Play["category"]): string {
  switch (category) {
    case "Pre-snap":
      return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    case "Post-snap":
      return "bg-purple-500/15 text-purple-400 border-purple-500/30";
    case "Mechanical":
      return "bg-orange-500/15 text-orange-400 border-orange-500/30";
    case "Mental":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    case "Scheme":
      return "bg-teal-500/15 text-teal-400 border-teal-500/30";
    default:
      return "bg-dark-700 text-dark-300 border-dark-600";
  }
}

export default function FilmBreakdown({ result }: FilmBreakdownProps) {
  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="rounded-xl border border-dark-700 bg-dark-800/60 p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-400 mb-4">
          Game Summary
        </h3>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {/* Grade */}
          <div
            className={`flex flex-col items-center rounded-lg border p-4 ${gradeBg(
              result.grade
            )}`}
          >
            <Award className={`h-5 w-5 mb-1 ${gradeColor(result.grade)}`} />
            <span
              className={`text-3xl font-black ${gradeColor(result.grade)}`}
            >
              {result.grade}
            </span>
            <span className="text-xs text-dark-400 mt-1">Overall Grade</span>
          </div>

          {/* Top Mistake */}
          <div className="flex flex-col rounded-lg border border-dark-700 bg-dark-900/40 p-4">
            <AlertTriangle className="h-4 w-4 text-red-400 mb-2" />
            <span className="text-xs text-dark-400 mb-1">Top Mistake</span>
            <span className="text-sm text-red-400 font-medium leading-snug">
              {result.topMistake}
            </span>
          </div>

          {/* Top Strength */}
          <div className="flex flex-col rounded-lg border border-dark-700 bg-dark-900/40 p-4">
            <Zap className="h-4 w-4 text-forge-400 mb-2" />
            <span className="text-xs text-dark-400 mb-1">Top Strength</span>
            <span className="text-sm text-forge-400 font-medium leading-snug">
              {result.topStrength}
            </span>
          </div>

          {/* Total Plays */}
          <div className="flex flex-col items-center justify-center rounded-lg border border-dark-700 bg-dark-900/40 p-4">
            <Tag className="h-4 w-4 text-dark-400 mb-2" />
            <span className="text-3xl font-black text-white">
              {result.totalPlaysTagged}
            </span>
            <span className="text-xs text-dark-400 mt-1">Plays Tagged</span>
          </div>
        </div>
      </div>

      {/* Play-by-Play */}
      <div className="rounded-xl border border-dark-700 bg-dark-800/60 p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-400 mb-4">
          Play-by-Play Breakdown
        </h3>

        <div className="max-h-72 overflow-y-auto pr-1 space-y-1.5 scrollbar-thin scrollbar-thumb-dark-600 scrollbar-track-transparent">
          {/* Header row */}
          <div className="grid grid-cols-[60px_1fr_1fr_120px] gap-3 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-dark-500">
            <span>Time</span>
            <span>Play</span>
            <span>Result</span>
            <span>Category</span>
          </div>

          {result.plays.map((play, i) => (
            <div
              key={i}
              className="grid grid-cols-[60px_1fr_1fr_120px] gap-3 items-center rounded-lg px-3 py-2.5 bg-dark-900/30 hover:bg-dark-900/60 transition-colors"
            >
              <span className="text-sm font-mono text-dark-400">
                {play.timestamp}
              </span>
              <span className="text-sm text-white font-medium">
                {play.playType}
              </span>
              <span className="text-sm text-dark-300">{play.result}</span>
              <span
                className={`inline-flex items-center justify-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${categoryColor(
                  play.category
                )}`}
              >
                {play.category}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 3 Priority Fixes */}
      <div className="rounded-xl border border-dark-700 bg-dark-800/60 p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-4 w-4 text-forge-400" />
          <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-400">
            Priority Fixes — ImpactRank
          </h3>
        </div>

        <div className="space-y-3">
          {result.fixes.map((fix, i) => (
            <div
              key={i}
              className="flex items-start gap-4 rounded-lg border border-dark-700 bg-dark-900/40 p-4"
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-forge-400/15 text-sm font-bold text-forge-400">
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white leading-relaxed">
                  {fix.description}
                </p>
                <p className="mt-1 text-xs text-forge-400 font-semibold">
                  Win rate impact: {fix.winRateImpact}
                </p>
              </div>
              <button
                type="button"
                className="shrink-0 flex items-center gap-1.5 rounded-lg border border-forge-400/30 bg-forge-400/10 px-3 py-1.5 text-xs font-semibold text-forge-400 transition-colors hover:bg-forge-400/20"
              >
                <Crosshair className="h-3 w-3" />
                Create Drill
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Export Row */}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="flex items-center gap-2 rounded-lg border border-dark-600 px-4 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-400 hover:text-white"
        >
          <Share2 className="h-4 w-4" />
          Share Breakdown
        </button>
        <button
          type="button"
          className="flex items-center gap-2 rounded-lg border border-dark-600 px-4 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-400 hover:text-white"
        >
          <FileDown className="h-4 w-4" />
          Download PDF
        </button>
        <button
          type="button"
          className="flex items-center gap-2 rounded-lg border border-dark-600 px-4 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-400 hover:text-white"
        >
          <Archive className="h-4 w-4" />
          Add to Vault
        </button>
      </div>
    </div>
  );
}
