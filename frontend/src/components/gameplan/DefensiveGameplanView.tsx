/**
 * Defense view for the Gameplan page.
 *
 * Calls POST /arsenal/defensive-gameplan with the active opponent and
 * renders the DefenseAI response (primary scheme, situational packages,
 * opponent counters, pre-snap keys, adjustment triggers, weaknesses,
 * practice points). Surfaces a readable error when the backend returns
 * 503 because ANTHROPIC_API_KEY is not configured.
 */

'use client';

import { useState } from 'react';
import {
  Shield,
  Sparkles,
  Loader2,
  Target,
  AlertTriangle,
  Eye,
  ListChecks,
  Volume2,
} from 'lucide-react';
import api from '@/lib/api';
import { useActiveArsenalTitle } from '@/hooks/useArsenal';
import { VoiceForgeService } from '@/lib/services/voiceforge';

interface SituationalPackage {
  situation: string;
  scheme: string;
  adjustment: string;
  confidence: number;
  why?: string;
  reasoning?: string; // legacy fallback
}

interface OpponentCounter {
  opponent_tendency: string;
  your_adjustment: string;
  confidence: number;
  why?: string;
  evidence?: string; // legacy fallback
}

// Teaching structure: what to look for → how to recognize it → what to do.
interface AdjustmentTrigger {
  trigger: string;
  look_for?: string;
  how_to_tell?: string;
  do?: string;
  adjustment?: string; // legacy fallback
  reason?: string; // legacy fallback
}

interface PreSnapKey {
  look_for: string;
  means: string;
}

interface PrimaryScheme {
  name: string;
  description: string;
  when_to_use: string;
  coverage_shell: string | null;
  blitz_rate: number;
  confidence: number;
}

export interface DefensivePlan {
  primary_scheme: PrimaryScheme;
  situational_packages: SituationalPackage[];
  opponent_counters: OpponentCounter[];
  pre_snap_keys: (string | PreSnapKey)[]; // string is the legacy form
  adjustment_triggers: AdjustmentTrigger[];
  weaknesses: string[];
  practice_points: string[];
}

interface Props {
  opponentId: string;
  opponentName: string;
}

export default function DefensiveGameplanView({
  opponentId,
  opponentName,
}: Props) {
  const titleId = useActiveArsenalTitle();
  const [plan, setPlan] = useState<DefensivePlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<DefensivePlan>(
        '/arsenal/defensive-gameplan',
        { title_id: titleId, opponent_id: opponentId }
      );
      setPlan(data);
    } catch (e: unknown) {
      type AxiosErr = { response?: { status?: number; data?: { detail?: string } } };
      const ax = e as AxiosErr;
      if (ax?.response?.status === 503) {
        setError(
          ax.response?.data?.detail ??
            'DefenseAI is offline — set ANTHROPIC_API_KEY in backend/.env.'
        );
      } else if (ax?.response?.status === 502) {
        setError('DefenseAI returned an unparseable response. Try again.');
      } else {
        setError(e instanceof Error ? e.message : 'Failed to generate defense plan.');
      }
    } finally {
      setLoading(false);
    }
  };

  const readBriefing = () => {
    if (!plan) return;
    const lines: string[] = [
      `Defensive plan vs ${opponentName}.`,
      `Primary scheme: ${plan.primary_scheme.name}.`,
      plan.primary_scheme.description,
      ...plan.opponent_counters
        .slice(0, 3)
        .map((c) => `Counter to ${c.opponent_tendency}: ${c.your_adjustment}.`),
    ];
    VoiceForgeService.speak(lines.join(' '), { interruptCurrent: true });
  };

  return (
    <div className="space-y-5">
      {/* Generate button */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-sky-500/30 bg-sky-500/5 px-4 py-3">
        <div className="flex items-center gap-3">
          <Shield className="h-6 w-6 text-sky-300" />
          <div>
            <p className="text-sm font-bold text-sky-100">
              Defensive Gameplan vs {opponentName}
            </p>
            <p className="text-[11px] text-dark-400">
              DefenseAI counters this opponent's offensive tendencies
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {plan && (
            <button
              type="button"
              onClick={readBriefing}
              className="inline-flex items-center gap-2 rounded-md border border-sky-500/40 bg-sky-500/10 px-3 py-1.5 text-xs font-bold text-sky-200 hover:bg-sky-500/20"
            >
              <Volume2 className="h-3.5 w-3.5" />
              Read Briefing
            </button>
          )}
          <button
            type="button"
            onClick={generate}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-dark-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {loading ? 'Generating…' : plan ? 'Regenerate' : 'Generate Defense Plan'}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {!plan && !loading && !error && (
        <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-10 text-center">
          <Shield className="mx-auto mb-3 h-10 w-10 text-dark-600" />
          <p className="text-sm text-dark-400">
            No defensive plan generated yet — click <span className="font-bold text-sky-300">Generate Defense Plan</span>{' '}
            to build one for this opponent.
          </p>
        </div>
      )}

      {plan && (
        <>
          {/* Primary scheme */}
          <div className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-5">
            <p className="text-[11px] font-bold uppercase tracking-wider text-sky-300">
              Primary Scheme
            </p>
            <h3 className="mt-1 text-xl font-bold text-dark-50">
              {plan.primary_scheme.name}
            </h3>
            <p className="mt-2 text-xs text-dark-300">
              {plan.primary_scheme.description}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Stat label="Coverage" value={plan.primary_scheme.coverage_shell ?? '—'} />
              <Stat
                label="Blitz Rate"
                value={`${Math.round(plan.primary_scheme.blitz_rate * 100)}%`}
              />
              <Stat
                label="Confidence"
                value={`${Math.round(plan.primary_scheme.confidence * 100)}%`}
              />
              <Stat label="When" value={plan.primary_scheme.when_to_use} small />
            </div>
          </div>

          {/* Opponent counters */}
          <Section
            title="Opponent Counters"
            icon={Target}
            empty="No opponent counters in this plan."
          >
            {plan.opponent_counters.map((c, i) => (
              <li key={i} className="rounded-lg bg-dark-800/60 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-sky-300">
                  vs. {c.opponent_tendency}
                </p>
                <p className="mt-1 text-sm font-medium text-dark-100">
                  {c.your_adjustment}
                </p>
                <p className="mt-1 text-[11px] text-dark-400">
                  <span className="font-semibold">Why:</span> {c.why ?? c.evidence}
                </p>
                <p className="text-[10px] text-dark-500">
                  Confidence: {Math.round(c.confidence * 100)}%
                </p>
              </li>
            ))}
          </Section>

          {/* Situational packages */}
          <Section
            title="Situational Packages"
            icon={ListChecks}
            empty="No situational packages."
          >
            {plan.situational_packages.map((p, i) => (
              <li key={i} className="rounded-lg bg-dark-800/60 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-sky-300">
                  {p.situation}
                </p>
                <p className="mt-1 text-sm font-medium text-dark-100">
                  {p.scheme} — {p.adjustment}
                </p>
                <p className="mt-1 text-[11px] text-dark-400">{p.why ?? p.reasoning}</p>
                <p className="text-[10px] text-dark-500">
                  Confidence: {Math.round(p.confidence * 100)}%
                </p>
              </li>
            ))}
          </Section>

          {/* Pre-snap keys — what to look at, and what it tells you */}
          <Section title="Pre-Snap Keys" icon={Eye} empty="No pre-snap keys.">
            {plan.pre_snap_keys.map((k, i) =>
              typeof k === 'string' ? (
                <li key={i} className="rounded-md bg-dark-800/60 p-2 text-sm text-dark-200">
                  {k}
                </li>
              ) : (
                <li key={i} className="rounded-lg bg-dark-800/60 p-3">
                  <p className="text-sm font-medium text-dark-100">{k.look_for}</p>
                  <p className="mt-1 text-[11px] text-dark-400">
                    <span className="font-semibold">Means:</span> {k.means}
                  </p>
                </li>
              )
            )}
          </Section>

          {/* Adjustment triggers */}
          <Section
            title="Adjustment Triggers"
            icon={AlertTriangle}
            empty="No adjustment triggers."
          >
            {plan.adjustment_triggers.map((t, i) => (
              <li key={i} className="rounded-lg bg-dark-800/60 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-300">
                  If {t.trigger}
                </p>
                {t.look_for || t.how_to_tell || t.do ? (
                  <div className="mt-1.5 flex flex-col gap-1">
                    {t.look_for && <ReadLine label="Look for" text={t.look_for} />}
                    {t.how_to_tell && <ReadLine label="How to tell" text={t.how_to_tell} />}
                    {t.do && <ReadLine label="Do" text={t.do} />}
                  </div>
                ) : (
                  <>
                    <p className="mt-1 text-sm font-medium text-dark-100">{t.adjustment}</p>
                    <p className="mt-1 text-[11px] text-dark-400">{t.reason}</p>
                  </>
                )}
              </li>
            ))}
          </Section>

          {/* Weaknesses + practice points */}
          {(plan.weaknesses.length > 0 || plan.practice_points.length > 0) && (
            <div className="grid gap-3 md:grid-cols-2">
              {plan.weaknesses.length > 0 && (
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-amber-300">
                    Plan Weaknesses
                  </p>
                  <ul className="mt-2 space-y-1 text-xs text-dark-300">
                    {plan.weaknesses.map((w, i) => (
                      <li key={i}>• {w}</li>
                    ))}
                  </ul>
                </div>
              )}
              {plan.practice_points.length > 0 && (
                <div className="rounded-xl border border-forge-500/30 bg-forge-500/5 p-4">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-forge-300">
                    Practice Points
                  </p>
                  <ul className="mt-2 space-y-1 text-xs text-dark-300">
                    {plan.practice_points.map((p, i) => (
                      <li key={i}>• {p}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/** A labeled micro-line: Look for / How to tell / Do. */
function ReadLine({ label, text }: { label: string; text: string }) {
  return (
    <div className="flex gap-2 text-xs">
      <span className="w-[4.5rem] shrink-0 pt-px text-[10px] font-semibold uppercase tracking-wider text-dark-500">
        {label}
      </span>
      <span className="flex-1 text-dark-300">{text}</span>
    </div>
  );
}

function Stat({
  label,
  value,
  small,
}: {
  label: string;
  value: string;
  small?: boolean;
}) {
  return (
    <div className="rounded-lg bg-dark-900/60 p-2">
      <p className="text-[10px] font-bold uppercase tracking-wider text-dark-500">
        {label}
      </p>
      <p
        className={
          small
            ? 'text-[11px] text-dark-200'
            : 'text-sm font-bold text-dark-100'
        }
      >
        {value}
      </p>
    </div>
  );
}

function Section({
  title,
  icon: Icon,
  empty,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  empty: string;
  children: React.ReactNode;
}) {
  const items = Array.isArray(children)
    ? children
    : [children];
  const hasItems = items && items.length > 0 && items.every(Boolean);
  return (
    <section>
      <div className="mb-2 flex items-center gap-2">
        <Icon className="h-4 w-4 text-sky-300" />
        <h4 className="text-sm font-bold text-dark-100">{title}</h4>
      </div>
      {hasItems ? (
        <ul className="space-y-2">{children}</ul>
      ) : (
        <p className="text-xs text-dark-500">{empty}</p>
      )}
    </section>
  );
}
