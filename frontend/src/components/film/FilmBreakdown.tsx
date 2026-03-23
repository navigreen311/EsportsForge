"use client";

interface FilmBreakdownProps {
  result: {
    grade: string;
    topMistake: string;
    topStrength: string;
    playCount: number;
    mistakeCount: number;
    fixes: string[];
  };
}

export default function FilmBreakdown({ result }: FilmBreakdownProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Summary Card */}
      <div className="mb-6">
        <p className="text-3xl font-black text-white mb-4">{result.grade}</p>

        <div className="space-y-2">
          <p className="text-red-400">
            <span className="font-semibold">Top Mistake:</span>{" "}
            {result.topMistake}
          </p>
          <p className="text-green-400">
            <span className="font-semibold">Top Strength:</span>{" "}
            {result.topStrength}
          </p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="mb-6 flex gap-6">
        <div className="rounded-lg bg-dark-800 px-4 py-2">
          <span className="text-lg font-bold text-white">
            {result.playCount}
          </span>{" "}
          <span className="text-dark-300">plays analyzed</span>
        </div>
        <div className="rounded-lg bg-dark-800 px-4 py-2">
          <span className="text-lg font-bold text-white">
            {result.mistakeCount}
          </span>{" "}
          <span className="text-dark-300">mistakes tagged</span>
        </div>
      </div>

      {/* Priority Fixes */}
      <div className="mb-6">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-dark-300">
          Priority Fixes
        </h3>
        <ol className="list-decimal space-y-1 pl-5 text-white">
          {result.fixes.map((fix, i) => (
            <li key={i}>{fix}</li>
          ))}
        </ol>
      </div>

      {/* Share Button */}
      <button
        type="button"
        className="rounded-lg border border-dark-600 px-4 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-400 hover:text-white"
      >
        Share Breakdown
      </button>
    </div>
  );
}
