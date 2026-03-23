"use client";

import { TrendingDown, AlertOctagon } from "lucide-react";

// ---------------------------------------------------------------------------
// Mock data – maps playId → meta-version risk status
// ---------------------------------------------------------------------------
export const PLAY_META_RISK: Record<string, "trending-countered" | "expiry-risk" | null> = {
  "play-1": null,
  "play-2": null,
  "play-3": null,
  "play-4": "trending-countered",
  "play-5": null,
  "play-6": "expiry-risk",
  "play-7": null,
  "play-8": null,
  "play-9": "trending-countered",
  "play-10": null,
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
interface MetaVersionExpiryProps {
  playId: string;
}

export default function MetaVersionExpiry({ playId }: MetaVersionExpiryProps) {
  const risk = PLAY_META_RISK[playId] ?? null;

  if (!risk) return null;

  if (risk === "trending-countered") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/20 px-2 py-0.5 text-[10px] font-medium text-amber-400">
        <TrendingDown className="h-3 w-3" />
        Trending Countered
      </span>
    );
  }

  // risk === "expiry-risk"
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-red-500/30 bg-red-500/20 px-2 py-0.5 text-[10px] font-medium text-red-400">
      <AlertOctagon className="h-3 w-3" />
      Expiry Risk
    </span>
  );
}
