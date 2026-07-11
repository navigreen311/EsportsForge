/**
 * ActiveSessionBanner — global session header, mounted in the dashboard
 * layout so it stays visible across page transitions while a session is
 * running. Shows step flow, current step CTA, total session timer, and
 * an End Session affordance.
 */

'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Check, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';
import { getTitleById } from '@/lib/titles';
import { useUIStore } from '@/lib/store';
import {
  useSessionStore,
  useElapsed,
  type StepKey,
  type ActiveSession,
} from '@/lib/sessionStore';

type StepStatus = 'done' | 'current' | 'upcoming';

interface StepDef {
  key: StepKey;
  index: number;
  title: string;
  href?: string;
  ctaLabel: string;
  nowLine: (s: ActiveSession) => string;
}

const STEPS: StepDef[] = [
  {
    key: 'warRoom',
    index: 1,
    title: 'War Room',
    href: '/war-room',
    ctaLabel: 'Open War Room',
    nowLine: (s) =>
      s.opponent
        ? `Review the opponent briefing for ${s.opponent}.`
        : 'Review your opponent briefing.',
  },
  {
    key: 'gameplan',
    index: 2,
    title: 'Gameplan',
    href: '/gameplan',
    ctaLabel: 'Open Gameplan',
    nowLine: (s) =>
      s.opponent
        ? `Review your gameplan vs ${s.opponent}.`
        : 'Review your gameplan and kill sheet.',
  },
  {
    key: 'playing',
    index: 3,
    title: 'Play',
    ctaLabel: 'Go to Dashboard',
    href: '/dashboard',
    nowLine: () => 'Hit "I\'m In Game" on the dashboard when you queue up.',
  },
  {
    key: 'logged',
    index: 4,
    title: 'Log Result',
    ctaLabel: 'Log Result',
    href: '/dashboard',
    nowLine: () => 'Log how the game went so LoopAI can learn.',
  },
];

interface ActiveSessionBannerProps {
  onEndSession: () => void;
}

export function ActiveSessionBanner({ onEndSession }: ActiveSessionBannerProps) {
  const session = useSessionStore((s) => s.session);
  const hydrated = useSessionStore((s) => s.hydrated);
  const hydrate = useSessionStore((s) => s.hydrate);
  const selectedTitle = useUIStore((s) => s.selectedTitle);
  const titleInfo = getTitleById(selectedTitle);
  const elapsed = useElapsed(session?.startTime ?? null);
  const router = useRouter();

  useEffect(() => {
    if (!hydrated) hydrate();
  }, [hydrated, hydrate]);

  if (!session) return null;

  // First step that isn't done is the current step.
  const currentIdx = STEPS.findIndex((s) => !session.steps[s.key]);
  const currentStep = currentIdx === -1 ? STEPS[STEPS.length - 1]! : STEPS[currentIdx]!;

  const stepStatus = (idx: number): StepStatus => {
    if (idx < currentIdx || currentIdx === -1) return 'done';
    if (idx === currentIdx) return 'current';
    return 'upcoming';
  };

  const handleCta = () => {
    if (currentStep.key === 'logged') {
      router.push('/dashboard');
      onEndSession();
      return;
    }
    if (currentStep.href) router.push(currentStep.href);
  };

  return (
    <div
      className={clsx(
        'relative overflow-hidden border-b border-forge-500/30 bg-emerald-950/70',
        'before:absolute before:inset-y-0 before:left-0 before:w-1.5 before:bg-forge-400'
      )}
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-3 lg:px-6">
        {/* Top row: status + timer + title + end */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-forge-300">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-forge-500" />
            </span>
            {session.mode} Session Live
          </span>

          <span className="font-mono text-sm font-bold text-dark-50">{elapsed}</span>

          {titleInfo && (
            <span className="text-xs text-dark-400">
              {titleInfo.icon} {titleInfo.name}
            </span>
          )}

          <div className="ml-auto">
            <button
              type="button"
              onClick={onEndSession}
              className="text-[11px] font-medium text-red-400 transition-colors hover:text-red-300"
            >
              End Session
            </button>
          </div>
        </div>

        {/* Step flow */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          {STEPS.map((step, idx) => {
            const status = stepStatus(idx);
            const isLast = idx === STEPS.length - 1;
            return (
              <div key={step.key} className="flex items-center gap-2">
                <Link
                  href={step.href ?? '#'}
                  className={clsx(
                    'flex items-center gap-1.5 text-[11px] font-semibold transition-colors',
                    status === 'done' && 'text-forge-400',
                    status === 'current' && 'text-forge-300',
                    status === 'upcoming' && 'text-dark-500 hover:text-dark-300'
                  )}
                >
                  <StepBadge index={step.index} status={status} />
                  <span className="uppercase tracking-wider">Step {step.index}</span>
                  <span className="text-dark-300">{step.title}</span>
                </Link>
                {!isLast && <ChevronRight className="h-3 w-3 text-dark-600" />}
              </div>
            );
          })}
        </div>

        {/* Now line */}
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-xs text-dark-300">
            <span className="mr-1.5 font-bold text-forge-400">NOW:</span>
            {currentStep.nowLine(session)}
          </p>
          {currentStep.href && (
            <button
              type="button"
              onClick={handleCta}
              className="inline-flex items-center gap-1.5 rounded-md bg-forge-500 px-3 py-1 text-[11px] font-bold text-dark-950 transition-colors hover:bg-forge-400"
            >
              {currentStep.ctaLabel}
              <ChevronRight className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function StepBadge({
  index,
  status,
}: {
  index: number;
  status: StepStatus;
}) {
  if (status === 'done') {
    return (
      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-forge-500/30">
        <Check className="h-2.5 w-2.5 text-forge-300" />
      </span>
    );
  }
  if (status === 'current') {
    return (
      <span className="relative flex h-4 w-4 items-center justify-center rounded-full bg-forge-500/40 ring-2 ring-forge-400">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-50" />
        <span className="relative text-[9px] font-bold text-forge-200">{index}</span>
      </span>
    );
  }
  return (
    <span className="flex h-4 w-4 items-center justify-center rounded-full border border-dark-600 text-[9px] font-bold text-dark-500">
      {index}
    </span>
  );
}
