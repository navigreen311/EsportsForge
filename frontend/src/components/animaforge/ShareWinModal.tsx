/**
 * ShareWinModal — celebration modal for milestone share-win cards (Agent #9).
 *
 * Renders the AnimaForge share-win video and lets the player share the
 * achievement on X, copy the link, or download the MP4. Mounted globally via
 * <ShareWinModalHost /> in the dashboard layout.
 *
 * Note: Imports `AnimaPlayer` and `useAnimaForgeAvailable` from the shared
 * AnimaForge module owned by Agent #3. This component is a pure consumer.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { Copy, Download, Twitter, X } from "lucide-react";
// Owned by Agent #3 — import only.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { AnimaPlayerType } from "@/lib/animaforge/types";
import { AnimaPlayer } from "@/components/animaforge/AnimaPlayer";
import { useAnimaForgeAvailable } from "@/hooks/useAnimaForge";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface ShareWinModalData {
  /** Trigger type — drives the headline label. */
  triggerType:
    | "tournament-win"
    | "benchmark-milestone"
    | "win-streak"
    | "impactrank-fix"
    | "playertwin-milestone"
    | string;
  /** Human-readable headline ("5-Game Win Streak on Madden 26"). */
  title: string;
  /** AnimaForge job id (preferred — modal will poll until complete). */
  jobId?: string;
  /** Direct video URL (if already known). */
  videoUrl?: string;
  thumbnailUrl?: string;
  /** Pre-formatted share text from the spec (e.g. "5-game win streak..."). */
  shareText?: string;
  /** Hashtags — appended to the tweet text. */
  hashtags?: string[];
}

export interface ShareWinModalProps {
  open: boolean;
  data: ShareWinModalData | null;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TRIGGER_HEADLINES: Record<string, string> = {
  "tournament-win": "Tournament Champion",
  "benchmark-milestone": "BenchmarkAI Milestone",
  "win-streak": "Win Streak",
  "impactrank-fix": "Weakness Fixed",
  "playertwin-milestone": "PlayerTwin Milestone",
};

function buildTweetUrl(shareText: string, videoUrl: string, hashtags: string[]): string {
  const tags = hashtags.length ? " " + hashtags.join(" ") : "";
  const text = `${shareText}${tags}`.trim();
  const params = new URLSearchParams({ text, url: videoUrl });
  return `https://twitter.com/intent/tweet?${params.toString()}`;
}

function downloadFilename(triggerType: string): string {
  const date = new Date().toISOString().slice(0, 10);
  const safeType = triggerType.replace(/[^a-z0-9-]/gi, "");
  return `esportsforge-${safeType}-${date}.mp4`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ShareWinModal({ open, data, onClose }: ShareWinModalProps) {
  const animaforgeAvailable = useAnimaForgeAvailable();
  const [copied, setCopied] = useState(false);
  const [resolvedUrl, setResolvedUrl] = useState<string | undefined>(data?.videoUrl);

  // Reset state when the modal data changes.
  useEffect(() => {
    setResolvedUrl(data?.videoUrl);
    setCopied(false);
  }, [data?.jobId, data?.videoUrl]);

  // Escape closes.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  const handleShareOnX = useCallback(() => {
    if (!data || !resolvedUrl) return;
    const url = buildTweetUrl(data.shareText ?? "New milestone on @EsportsForge", resolvedUrl, data.hashtags ?? []);
    window.open(url, "_blank", "noopener,noreferrer");
  }, [data, resolvedUrl]);

  const handleCopy = useCallback(async () => {
    if (!resolvedUrl) return;
    try {
      await navigator.clipboard.writeText(resolvedUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // No-op — clipboard API may be unavailable in some browsers/iframes.
    }
  }, [resolvedUrl]);

  if (!open || !data) return null;
  if (!animaforgeAvailable) return null;

  const headlineLabel = TRIGGER_HEADLINES[data.triggerType] ?? "Milestone";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-dark-950/80 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-2xl rounded-xl border border-dark-700/50 bg-dark-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-dark-700/50 px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-forge-400">
              {`\u{1F3C6} You hit a milestone!`}
            </p>
            <h2 className="mt-1 text-lg font-semibold text-dark-50">{data.title}</h2>
            <p className="mt-0.5 text-xs text-dark-400">{headlineLabel}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200"
            aria-label="Dismiss"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* AnimaPlayer */}
        <div className="px-6 py-4">
          <div className="overflow-hidden rounded-lg border border-dark-700/50 bg-dark-950">
            <AnimaPlayer
              jobId={data.jobId}
              videoUrl={data.videoUrl}
              thumbnailUrl={data.thumbnailUrl}
              type="share-win"
              autoPlay
              loop
              onReady={(url) => setResolvedUrl(url)}
            />
          </div>

          <p className="mt-3 text-sm text-dark-300">Share your achievement:</p>

          {/* Action buttons */}
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <button
              type="button"
              onClick={handleShareOnX}
              disabled={!resolvedUrl}
              className="flex items-center justify-center gap-2 rounded-lg bg-forge-500 px-3 py-2 text-sm font-medium text-dark-950 transition-colors hover:bg-forge-400 disabled:cursor-not-allowed disabled:bg-dark-700 disabled:text-dark-400"
            >
              <Twitter className="h-4 w-4" />
              Share on X
            </button>

            <button
              type="button"
              onClick={handleCopy}
              disabled={!resolvedUrl}
              className="flex items-center justify-center gap-2 rounded-lg border border-dark-700/50 bg-dark-800 px-3 py-2 text-sm font-medium text-dark-100 transition-colors hover:bg-dark-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Copy className="h-4 w-4" />
              {copied ? "Link copied ✓" : "Copy Link"}
            </button>

            <a
              href={resolvedUrl ?? "#"}
              download={downloadFilename(data.triggerType)}
              aria-disabled={!resolvedUrl}
              className={
                "flex items-center justify-center gap-2 rounded-lg border border-dark-700/50 bg-dark-800 px-3 py-2 text-sm font-medium text-dark-100 transition-colors hover:bg-dark-700 " +
                (!resolvedUrl ? "pointer-events-none opacity-50" : "")
              }
            >
              <Download className="h-4 w-4" />
              Download
            </a>

            <button
              type="button"
              onClick={onClose}
              className="flex items-center justify-center gap-2 rounded-lg border border-dark-700/50 bg-dark-900 px-3 py-2 text-sm font-medium text-dark-300 transition-colors hover:bg-dark-800"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Host — global mount that polls /pending-wins on dashboard load
// ---------------------------------------------------------------------------

interface PendingWinDto {
  job_id: string;
  trigger_type: string;
  status: string;
  video_url: string | null;
  thumbnail_url: string | null;
  share_text: string | null;
  hashtags: string[];
  completed_at: string | null;
}

interface PendingWinsResponseDto {
  items: PendingWinDto[];
}

const DISMISSED_KEY = "esportsforge.share_win.dismissed_v1";

function loadDismissed(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = window.localStorage.getItem(DISMISSED_KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw) as string[]);
  } catch {
    return new Set();
  }
}

function saveDismissed(set: Set<string>): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(DISMISSED_KEY, JSON.stringify(Array.from(set)));
  } catch {
    /* ignore */
  }
}

function humanizeTrigger(trigger: string, _hashtags: string[]): string {
  switch (trigger) {
    case "tournament-win":
      return "Tournament Win";
    case "benchmark-milestone":
      return "BenchmarkAI Milestone";
    case "win-streak":
      return "Win Streak Milestone";
    case "impactrank-fix":
      return "ImpactRank Fix Confirmed";
    case "playertwin-milestone":
      return "PlayerTwin 75% Accuracy";
    default:
      return "New Milestone";
  }
}

export function ShareWinModalHost() {
  const animaforgeAvailable = useAnimaForgeAvailable();
  const [data, setData] = useState<ShareWinModalData | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!animaforgeAvailable) return;
    let cancelled = false;

    (async () => {
      try {
        const apiModule = await import("@/lib/api");
        const api = apiModule.default;
        const res = await api.get<PendingWinsResponseDto>("/animaforge/pending-wins");
        if (cancelled) return;
        const dismissed = loadDismissed();
        const candidate = (res.data?.items ?? []).find(
          (item) =>
            (item.status === "complete" || item.status === "rendering" || item.status === "pending") &&
            !dismissed.has(item.job_id)
        );
        if (!candidate) return;
        setData({
          triggerType: candidate.trigger_type,
          title: humanizeTrigger(candidate.trigger_type, candidate.hashtags),
          jobId: candidate.job_id,
          videoUrl: candidate.video_url ?? undefined,
          thumbnailUrl: candidate.thumbnail_url ?? undefined,
          shareText: candidate.share_text ?? undefined,
          hashtags: candidate.hashtags ?? [],
        });
        setOpen(true);
      } catch {
        // Endpoint may not exist yet — fail silently per graceful-degradation rule.
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [animaforgeAvailable]);

  const handleClose = useCallback(() => {
    if (data?.jobId) {
      const dismissed = loadDismissed();
      dismissed.add(data.jobId);
      saveDismissed(dismissed);
    }
    setOpen(false);
  }, [data?.jobId]);

  if (!animaforgeAvailable) return null;
  return <ShareWinModal open={open} data={data} onClose={handleClose} />;
}

export default ShareWinModal;
