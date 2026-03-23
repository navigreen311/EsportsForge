"use client";

import { useState } from "react";
import { X } from "lucide-react";

export interface AnalyticsFilterState {
  dateRange: string;
  mode: string;
  opponent: string;
  title: string;
}

const DEFAULTS: AnalyticsFilterState = {
  dateRange: "Last 30d",
  mode: "All Modes",
  opponent: "All Opponents",
  title: "Madden 26",
};

const OPTIONS: Record<keyof AnalyticsFilterState, string[]> = {
  dateRange: ["Last 7d", "Last 30d", "Last 90d", "All Time"],
  mode: ["All Modes", "Ranked", "Tournament", "Training"],
  opponent: ["All Opponents", "Rivals Only", "Aggressive Rusher", "Blitz Heavy"],
  title: ["Madden 26", "CFB 26"],
};

const LABELS: Record<keyof AnalyticsFilterState, string> = {
  dateRange: "Date Range",
  mode: "Game Mode",
  opponent: "Opponent",
  title: "Title",
};

const selectClass =
  "bg-dark-900/50 border border-dark-700 text-dark-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-dark-500";

interface AnalyticsFiltersProps {
  onFilterChange?: (filters: AnalyticsFilterState) => void;
}

export default function AnalyticsFilters({ onFilterChange }: AnalyticsFiltersProps) {
  const [filters, setFilters] = useState<AnalyticsFilterState>({ ...DEFAULTS });

  const activeFilters = (Object.keys(DEFAULTS) as (keyof AnalyticsFilterState)[]).filter(
    (key) => filters[key] !== DEFAULTS[key]
  );

  const hasActiveFilters = activeFilters.length > 0;

  function updateFilter(key: keyof AnalyticsFilterState, value: string) {
    const next = { ...filters, [key]: value };
    setFilters(next);
    onFilterChange?.(next);
  }

  function resetFilter(key: keyof AnalyticsFilterState) {
    updateFilter(key, DEFAULTS[key]);
  }

  function resetAll() {
    setFilters({ ...DEFAULTS });
    onFilterChange?.({ ...DEFAULTS });
  }

  return (
    <div className="rounded-lg border border-dark-700/50 bg-dark-900/60 px-4 py-3">
      {/* Filter selects row */}
      <div className="flex flex-wrap gap-3">
        {(Object.keys(OPTIONS) as (keyof AnalyticsFilterState)[]).map((key) => (
          <select
            key={key}
            value={filters[key]}
            onChange={(e) => updateFilter(key, e.target.value)}
            className={selectClass}
            aria-label={LABELS[key]}
          >
            {OPTIONS[key].map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        ))}
      </div>

      {/* Active filter pills + reset */}
      {hasActiveFilters && (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {activeFilters.map((key) => (
            <span
              key={key}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-dark-700 text-dark-300 text-xs"
            >
              {filters[key]}
              <button
                type="button"
                onClick={() => resetFilter(key)}
                className="hover:text-dark-100"
                aria-label={`Remove ${LABELS[key]} filter`}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
          <button
            type="button"
            onClick={resetAll}
            className="text-xs text-forge-400 hover:text-forge-300"
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
}
