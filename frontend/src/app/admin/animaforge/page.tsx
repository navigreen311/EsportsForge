/**
 * Admin > AnimaForge — Agent #10.
 *
 * Surfaces operational stats from `/api/v1/animaforge/admin/stats`:
 *   - Jobs completed today
 *   - Average render time (seconds)
 *   - Storage used (MB)
 *   - Queue depth
 *
 * Sits alongside the existing AI Performance widgets. When AnimaForge is
 * offline (or the endpoint is not yet wired), the page still renders with
 * zero values and an "Offline" banner so the admin nav never breaks.
 */

'use client';

import { useEffect, useState } from 'react';
import {
  Clock,
  Database,
  Film,
  ListOrdered,
  Loader2,
  WifiOff,
} from 'lucide-react';

import api from '@/lib/api';

interface AdminStats {
  jobs_today: number;
  avg_render_seconds: number;
  storage_mb: number;
  queue_depth: number;
}

const ZERO: AdminStats = {
  jobs_today: 0,
  avg_render_seconds: 0,
  storage_mb: 0,
  queue_depth: 0,
};

export default function AdminAnimaForgePage() {
  const [stats, setStats] = useState<AdminStats>(ZERO);
  const [loading, setLoading] = useState(true);
  const [reachable, setReachable] = useState(true);
  const [animaForgeOnline, setAnimaForgeOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // Stats — admin endpoint
      try {
        const res = await api.get<AdminStats>('/animaforge/admin/stats');
        if (!cancelled) {
          setStats({ ...ZERO, ...res.data });
          setReachable(true);
        }
      } catch {
        if (!cancelled) {
          setStats(ZERO);
          setReachable(false);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
      // Live status badge
      try {
        const res = await api.get<{ available: boolean }>('/animaforge/status');
        if (!cancelled) setAnimaForgeOnline(res.data.available);
      } catch {
        if (!cancelled) setAnimaForgeOnline(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const offline = animaForgeOnline === false;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Film className="h-6 w-6 text-forge-400" />
          <h1 className="text-2xl font-bold text-dark-50">AnimaForge</h1>
        </div>
        {animaForgeOnline === null ? (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-dark-700/40 px-2.5 py-1 text-xs font-medium text-dark-400">
            <Loader2 className="h-3 w-3 animate-spin" />
            Checking…
          </span>
        ) : animaForgeOnline ? (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Online
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            Offline
          </span>
        )}
      </div>

      {(offline || !reachable) && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-sm">
          <WifiOff className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <div>
            <p className="font-medium text-amber-300">
              AnimaForge stats are unavailable
            </p>
            <p className="text-xs text-amber-200/80">
              Showing zeros. Counters will populate automatically once the
              service is reachable.
            </p>
          </div>
        </div>
      )}

      {/* Stat tiles */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<Film className="h-4 w-4" />}
          label="Jobs Today"
          value={
            loading ? '—' : stats.jobs_today.toLocaleString()
          }
          hint="Completed in the last 24h"
        />
        <StatCard
          icon={<Clock className="h-4 w-4" />}
          label="Average Render Time"
          value={loading ? '—' : `${stats.avg_render_seconds.toFixed(1)}s`}
          hint="Across recent completions"
        />
        <StatCard
          icon={<Database className="h-4 w-4" />}
          label="Storage Used"
          value={loading ? '—' : `${stats.storage_mb.toFixed(1)} MB`}
          hint="Aggregate across all users"
        />
        <StatCard
          icon={<ListOrdered className="h-4 w-4" />}
          label="Queue Depth"
          value={loading ? '—' : stats.queue_depth.toLocaleString()}
          hint="Jobs pending render"
        />
      </div>

      <p className="text-xs text-dark-500">
        AnimaForge powers Arsenal play diagrams, drill demonstrations, gameplan
        animations, and Share Your Win cards.
      </p>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  hint,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
      <div className="flex items-center gap-2 text-xs text-dark-400">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-2xl font-bold text-dark-50">{value}</p>
      {hint && <p className="mt-1 text-xs text-dark-500">{hint}</p>}
    </div>
  );
}
