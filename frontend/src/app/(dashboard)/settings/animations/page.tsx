/**
 * My Animations library — Agent #10.
 *
 * Lists every AnimaForge job for the current user, with Watch/Delete/Share
 * actions per row. The page is client-rendered so it can poll while jobs are
 * still rendering.
 *
 * Data comes from `GET /api/v1/animaforge/jobs` (Agent #1's endpoint). When
 * the endpoint is not yet wired we render an empty state instead of an error
 * — graceful degradation per the contract.
 */

'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowLeft,
  Film,
  Loader2,
  Play,
  Share2,
  Trash2,
  WifiOff,
} from 'lucide-react';

import api from '@/lib/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AnimaJob {
  id?: string;
  job_id: string;
  type: 'weapon-diagram' | 'drill-demo' | 'play-diagram' | 'share-win';
  title_id?: string | null;
  source_id?: string | null;
  status: 'pending' | 'rendering' | 'complete' | 'failed';
  video_url?: string | null;
  thumbnail_url?: string | null;
  size_mb?: number | null;
  created_at?: string | null;
  completed_at?: string | null;
}

const TYPE_LABEL: Record<AnimaJob['type'], string> = {
  'weapon-diagram': 'Weapon Diagram',
  'drill-demo': 'Drill Demo',
  'play-diagram': 'Play Diagram',
  'share-win': 'Share Card',
};

const STATUS_LABEL: Record<AnimaJob['status'], string> = {
  pending: 'Pending',
  rendering: 'Rendering',
  complete: 'Ready',
  failed: 'Failed',
};

const STATUS_TONE: Record<AnimaJob['status'], string> = {
  pending: 'bg-dark-700/40 text-dark-300',
  rendering: 'bg-blue-500/10 text-blue-300',
  complete: 'bg-emerald-500/10 text-emerald-300',
  failed: 'bg-red-500/10 text-red-300',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return '—';
  }
}

function deriveTitle(job: AnimaJob): string {
  // Best-effort label until the backend returns a friendly title field.
  if (job.source_id) {
    const parts = job.source_id.split(':');
    return parts[parts.length - 1].replace(/[-_]/g, ' ');
  }
  return TYPE_LABEL[job.type];
}

function totalStorageMB(jobs: AnimaJob[]): number {
  // If the backend returns sizes use them, else estimate at 3.5 MB per
  // completed clip — same constant the admin endpoint uses.
  let known = 0;
  let unknownComplete = 0;
  for (const j of jobs) {
    if (typeof j.size_mb === 'number' && Number.isFinite(j.size_mb)) {
      known += j.size_mb;
    } else if (j.status === 'complete') {
      unknownComplete += 1;
    }
  }
  return known + unknownComplete * 3.5;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function MyAnimationsPage() {
  const [jobs, setJobs] = useState<AnimaJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [reachable, setReachable] = useState(true);
  const [confirmClear, setConfirmClear] = useState(false);
  const [clearing, setClearing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<{ jobs?: AnimaJob[] } | AnimaJob[]>(
        '/animaforge/jobs'
      );
      const data = res.data;
      const list = Array.isArray(data) ? data : data?.jobs ?? [];
      setJobs(list);
      setReachable(true);
    } catch {
      setJobs([]);
      setReachable(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const handleDelete = useCallback(
    async (job: AnimaJob) => {
      const idForDelete = job.job_id || job.id || '';
      if (!idForDelete) return;
      // Optimistic
      setJobs((prev) => prev.filter((j) => (j.job_id || j.id) !== idForDelete));
      try {
        await api.delete(`/animaforge/jobs/${encodeURIComponent(idForDelete)}`);
      } catch {
        // Reload to recover the row if delete failed.
        void load();
      }
    },
    [load]
  );

  const handleShare = useCallback((job: AnimaJob) => {
    if (!job.video_url) return;
    const text =
      job.type === 'share-win'
        ? 'Check out my latest milestone on @EsportsForge'
        : 'New AnimaForge clip from @EsportsForge';
    const url = job.video_url;
    const intent = `https://twitter.com/intent/tweet?text=${encodeURIComponent(
      text
    )}&url=${encodeURIComponent(url)}`;
    if (typeof window !== 'undefined') {
      window.open(intent, '_blank', 'noopener,noreferrer');
    }
  }, []);

  const handleClearAll = useCallback(async () => {
    setClearing(true);
    const ids = jobs
      .map((j) => j.job_id || j.id || '')
      .filter((s): s is string => Boolean(s));
    // Fire deletes in parallel; tolerate individual failures.
    await Promise.all(
      ids.map((id) =>
        api
          .delete(`/animaforge/jobs/${encodeURIComponent(id)}`)
          .catch(() => null)
      )
    );
    setClearing(false);
    setConfirmClear(false);
    await load();
  }, [jobs, load]);

  const totalMB = totalStorageMB(jobs);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link
            href="/dashboard/settings"
            className="mb-2 inline-flex items-center gap-1.5 text-xs text-dark-400 transition-colors hover:text-dark-200"
          >
            <ArrowLeft className="h-3 w-3" />
            Back to Settings
          </Link>
          <h1 className="flex items-center gap-3 text-2xl font-bold text-dark-50">
            <Film className="h-6 w-6 text-forge-400" />
            My Animations
          </h1>
          <p className="mt-1 text-sm text-dark-400">
            Every animation generated by AnimaForge for your account
          </p>
        </div>

        {!confirmClear ? (
          <button
            type="button"
            disabled={!jobs.length}
            onClick={() => setConfirmClear(true)}
            className="inline-flex items-center gap-2 rounded-lg border border-red-500/40 bg-transparent px-3 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Trash2 className="h-4 w-4" />
            Clear All
          </button>
        ) : (
          <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 text-xs">
            <span className="text-red-300">Delete all animations?</span>
            <button
              type="button"
              disabled={clearing}
              onClick={handleClearAll}
              className="rounded-md bg-red-600 px-2.5 py-1 text-[11px] font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-60"
            >
              {clearing ? 'Deleting…' : 'Confirm'}
            </button>
            <button
              type="button"
              onClick={() => setConfirmClear(false)}
              className="rounded-md border border-dark-600 bg-dark-800 px-2.5 py-1 text-[11px] font-medium text-dark-300 transition-colors hover:bg-dark-700"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Status banner when API unreachable */}
      {!reachable && !loading && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-sm">
          <WifiOff className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <div>
            <p className="font-medium text-amber-300">AnimaForge is offline</p>
            <p className="text-xs text-amber-200/80">
              We could not load your animation library. Try again once the
              service is back online.
            </p>
          </div>
        </div>
      )}

      {/* Table card */}
      <div className="rounded-xl border border-dark-700/60 bg-dark-900">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-sm text-dark-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading animations…
          </div>
        ) : jobs.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-16 text-center">
            <Film className="h-10 w-10 text-dark-600" />
            <p className="text-sm font-medium text-dark-200">
              No animations yet
            </p>
            <p className="max-w-md text-xs text-dark-500">
              Generated animations will appear here. Save a weapon, start a drill,
              or hit a milestone to create one.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Title</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => {
                  const id = job.job_id || job.id || '';
                  const isReady =
                    job.status === 'complete' && Boolean(job.video_url);
                  return (
                    <tr
                      key={id}
                      className="border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
                    >
                      <td className="px-4 py-3 font-medium text-dark-100">
                        {TYPE_LABEL[job.type] ?? job.type}
                      </td>
                      <td className="px-4 py-3 capitalize text-dark-300">
                        {deriveTitle(job)}
                      </td>
                      <td className="px-4 py-3 text-dark-300">
                        {fmtDate(job.completed_at || job.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_TONE[job.status] ?? STATUS_TONE.pending}`}
                        >
                          {STATUS_LABEL[job.status] ?? job.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-2">
                          {isReady ? (
                            <a
                              href={job.video_url || '#'}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 rounded-md border border-dark-600 bg-dark-800 px-2 py-1 text-[11px] font-medium text-dark-200 transition-colors hover:border-forge-500 hover:text-forge-300"
                            >
                              <Play className="h-3 w-3" /> Watch
                            </a>
                          ) : job.status === 'failed' ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-red-300">
                              <AlertTriangle className="h-3 w-3" /> Failed
                            </span>
                          ) : (
                            <span className="text-[11px] text-dark-500">—</span>
                          )}
                          {job.type === 'share-win' && isReady && (
                            <button
                              type="button"
                              onClick={() => handleShare(job)}
                              className="inline-flex items-center gap-1 rounded-md border border-dark-600 bg-dark-800 px-2 py-1 text-[11px] font-medium text-dark-200 transition-colors hover:border-forge-500 hover:text-forge-300"
                            >
                              <Share2 className="h-3 w-3" /> Share
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleDelete(job)}
                            className="inline-flex items-center gap-1 rounded-md border border-dark-600 bg-dark-800 px-2 py-1 text-[11px] font-medium text-red-300 transition-colors hover:border-red-500/40 hover:bg-red-500/5"
                          >
                            <Trash2 className="h-3 w-3" /> Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer / storage line */}
      <div className="flex items-center justify-between text-xs text-dark-400">
        <span>
          Total storage used:{' '}
          <span className="font-medium text-dark-200">
            {totalMB.toFixed(1)} MB
          </span>{' '}
          of 500 MB ({jobs.length} clip{jobs.length === 1 ? '' : 's'})
        </span>
      </div>
    </div>
  );
}
