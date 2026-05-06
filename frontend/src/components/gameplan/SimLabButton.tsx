'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FlaskConical, Zap, X } from 'lucide-react';
import type { Play } from '@/types/gameplan';

interface SimulateButtonProps {
  play: Play;
  opponentName: string;
  /** Opponent's most likely coverage shell — drives the IF/THEN predictions. */
  opponentCoverage?: string | null;
}

interface Scenario {
  ifText: string;
  thenText: string;
  tone: 'high' | 'medium';
}

function buildScenarios(
  play: Play,
  coverage: string | null
): { scenarios: Scenario[]; overall: number } {
  const scenarios: Scenario[] = [];

  // Primary scenario — the play's natural coverage matchup. If we have an
  // explicit `play.beats` string, we lead with it; otherwise we fall back to
  // the opponent's most-likely coverage.
  const primaryCoverage = play.beats ?? coverage ?? 'his base coverage';
  scenarios.push({
    ifText: `IF he shows ${primaryCoverage}`,
    thenText: `${play.name} hits the void. High confidence — primary call.`,
    tone: 'high',
  });

  // Audible-driven adjustment scenarios
  (play.audibleOptions ?? []).slice(0, 2).forEach((a) => {
    scenarios.push({
      ifText: `IF ${a.trigger.toLowerCase()}`,
      thenText: `${a.label} — ${a.targetPlay}.`,
      tone: 'medium',
    });
  });

  // Tag-derived fallback when audibles are sparse
  if (scenarios.length < 3) {
    if (play.conceptTags?.includes('quick-pass')) {
      scenarios.push({
        ifText: 'IF he brings a blitz look',
        thenText: 'Hot route Slant — immediate release.',
        tone: 'medium',
      });
    } else if (play.conceptTags?.includes('run')) {
      scenarios.push({
        ifText: 'IF he stacks the box',
        thenText: 'Audible to PA Boot — hit the seam off the run fake.',
        tone: 'medium',
      });
    } else {
      scenarios.push({
        ifText: 'IF he rotates coverage post-snap',
        thenText: 'Read the safety rotation and check progression to the flat.',
        tone: 'medium',
      });
    }
  }

  // Overall confidence — derive from play.confidenceScore with a small
  // simulation-uncertainty haircut (we're modelling, not in-game).
  const overall = Math.min(
    95,
    Math.max(55, Math.round(play.confidenceScore - 5))
  );
  return { scenarios, overall };
}

export default function SimLabButton({
  play,
  opponentName,
  opponentCoverage = null,
}: SimulateButtonProps) {
  const [open, setOpen] = useState(false);
  const { scenarios, overall } = buildScenarios(play, opponentCoverage);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title={`Simulate ${play.name} vs. ${opponentName}'s coverage tendencies`}
        className="inline-flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800/50 px-3 py-1.5 text-xs font-medium text-dark-200 transition-colors hover:border-forge-500/50 hover:bg-dark-800 hover:text-forge-400"
      >
        <FlaskConical className="h-3.5 w-3.5" />
        Simulate
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-lg rounded-xl border border-dark-700 bg-dark-900 p-5 shadow-xl"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="flex items-start justify-between">
              <h3 className="flex items-center gap-2 text-base font-semibold text-dark-50">
                <Zap className="h-4 w-4 text-amber-400" />
                Simulation — {play.name} vs {opponentName}
              </h3>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="rounded-md p-1 text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200"
                aria-label="Close simulation"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
                AdaptAI says
              </p>
              <ul className="mt-2 space-y-3">
                {scenarios.map((s, i) => (
                  <li
                    key={i}
                    className="rounded-lg border border-dark-700/60 bg-dark-800/40 p-3"
                  >
                    <p
                      className={
                        s.tone === 'high'
                          ? 'text-sm font-semibold text-forge-300'
                          : 'text-sm font-semibold text-amber-300'
                      }
                    >
                      {s.ifText}
                    </p>
                    <p className="mt-1 text-sm text-dark-300">{s.thenText}</p>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-4 rounded-lg border border-forge-500/30 bg-forge-500/10 px-3 py-2">
              <p className="text-xs text-forge-200/90">
                <span className="font-semibold text-forge-300">OVERALL:</span>{' '}
                {overall}% chance this play gains 7+ yards against his base
                coverage
              </p>
            </div>

            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="rounded-lg border border-dark-700 bg-dark-800/80 px-3 py-1.5 text-xs font-medium text-dark-200 transition-colors hover:border-dark-500 hover:bg-dark-700 hover:text-dark-50"
              >
                Close
              </button>
              <Link
                href={`/drills/simlab?play=${encodeURIComponent(play.id)}&opponent=${encodeURIComponent(
                  opponentName
                )}${
                  opponentCoverage
                    ? `&coverage=${encodeURIComponent(opponentCoverage)}`
                    : ''
                }`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-forge-500/40 bg-forge-500/15 px-3 py-1.5 text-xs font-semibold text-forge-300 transition-colors hover:bg-forge-500/25 hover:border-forge-500/60"
                onClick={() => setOpen(false)}
              >
                Test in SimLab →
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
