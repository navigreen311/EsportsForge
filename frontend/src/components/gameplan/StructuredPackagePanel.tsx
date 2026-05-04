/**
 * Structured rendering for the GameplanAI package payloads — kill sheet,
 * script view, package health (anti-blitz / red-zone), and 2-min drill
 * scenarios.
 *
 * Sits ABOVE the existing play list on the matching tab so the user sees
 * both the structured AI summary and the underlying play cards.
 */

'use client';

import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Crosshair,
  ListOrdered,
} from 'lucide-react';
import { clsx } from 'clsx';
import type {
  KillSheetEntry,
  PackageHealth,
  ScriptViewEntry,
  TwoMinDrillEntry,
} from '@/types/gameplan';

export function KillSheetSummary({ entries }: { entries: KillSheetEntry[] }) {
  if (!entries.length) return null;
  return (
    <div className="rounded-xl border border-forge-500/30 bg-forge-500/5 p-4">
      <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-forge-400">
        <Crosshair className="h-4 w-4" /> Kill Sheet — top {entries.length}
      </h3>
      <ol className="mt-3 space-y-2">
        {entries.map((e) => (
          <li key={`${e.rank}-${e.name}`} className="flex items-start gap-3 text-sm">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-forge-500/40 bg-forge-500/10 text-[11px] font-bold tabular-nums text-forge-400">
              {e.rank}
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-dark-100">
                {e.name}
                <span className="ml-2 text-xs font-normal text-dark-400">
                  · {e.formation}
                </span>
              </p>
              <p className="text-xs text-dark-400">{e.whenToCall}</p>
            </div>
            <span className="shrink-0 rounded-md bg-dark-800 px-2 py-0.5 text-[11px] font-bold tabular-nums text-forge-400">
              {e.confidence}%
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function ScriptViewPanel({ entries }: { entries: ScriptViewEntry[] }) {
  if (!entries.length) return null;
  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/60 p-4">
      <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-dark-300">
        <ListOrdered className="h-4 w-4 text-forge-400" /> Script — opening sequence
      </h3>
      <ol className="mt-3 space-y-2">
        {entries.map((e) => (
          <li key={e.order} className="flex items-start gap-3 text-sm">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-dark-800 text-[11px] font-bold tabular-nums text-dark-300">
              #{e.order}
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-dark-100">
                {e.playName}
                <span className="ml-2 text-xs font-normal text-dark-400">· {e.formation}</span>
              </p>
              <p className="text-xs text-dark-400">Call when: {e.callWhen}</p>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-dark-500">
                <span>Conf {e.confidence}%</span>
                <span className="text-dark-700">·</span>
                <span>Impact {e.impactScore}</span>
                <span className="text-dark-700">·</span>
                <span>{e.masteryLevel}</span>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function PackageHealthCard({
  title,
  health,
}: {
  title: string;
  health?: PackageHealth | null;
}) {
  if (!health) return null;
  const tone = health.complete
    ? 'border-forge-500/30 bg-forge-500/5 text-forge-300'
    : 'border-amber-500/30 bg-amber-500/5 text-amber-300';
  const Icon = health.complete ? CheckCircle2 : AlertTriangle;
  return (
    <div className={clsx('rounded-xl border p-4', tone)}>
      <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider">
        <Icon className="h-4 w-4" /> {title} package
        <span className="ml-1 text-[10px] font-medium uppercase tracking-wider opacity-70">
          {health.complete ? 'complete' : 'incomplete'}
        </span>
      </h3>
      {health.healthMessage && (
        <p className="mt-2 text-xs text-dark-200">{health.healthMessage}</p>
      )}
      {!!health.plays.length && (
        <ul className="mt-3 grid grid-cols-1 gap-1 sm:grid-cols-2">
          {health.plays.map((p) => (
            <li key={p} className="flex items-center gap-1.5 text-xs text-dark-200">
              <CheckCircle2 className="h-3 w-3 shrink-0 text-forge-400" /> {p}
            </li>
          ))}
        </ul>
      )}
      {health.missing && (
        <p className="mt-2 text-xs">
          <span className="font-semibold uppercase tracking-wider opacity-70">Missing: </span>
          <span className="text-dark-200">{health.missing}</span>
        </p>
      )}
    </div>
  );
}

export function TwoMinDrillTable({ entries }: { entries: TwoMinDrillEntry[] }) {
  if (!entries.length) return null;
  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/60 p-4">
      <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-dark-300">
        <Clock className="h-4 w-4 text-forge-400" /> 2-Min Drill — situational tree
      </h3>
      <div className="mt-3 overflow-hidden rounded-lg border border-dark-700/50">
        <table className="w-full text-left text-sm">
          <thead className="bg-dark-800/60 text-[10px] uppercase tracking-wider text-dark-400">
            <tr>
              <th className="px-3 py-2 font-semibold">Time</th>
              <th className="px-3 py-2 font-semibold">Situation</th>
              <th className="px-3 py-2 font-semibold">Call</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr key={i} className="border-t border-dark-700/40">
                <td className="px-3 py-2 font-mono text-xs text-forge-400">{e.time}</td>
                <td className="px-3 py-2 text-dark-200">{e.situation}</td>
                <td className="px-3 py-2 text-dark-300">{e.call}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
