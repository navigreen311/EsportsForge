/**
 * SessionTimeline — compact "PRE-GAME / IN GAME / POST-GAME" timeline
 * shown at the bottom of the dashboard during an active session. Each
 * stage shows what is complete, what is current, and what is next.
 */

'use client';

import { useRouter } from 'next/navigation';
import { Check, ChevronRight, Circle } from 'lucide-react';
import { clsx } from 'clsx';
import { useSessionStore } from '@/lib/sessionStore';

type Stage = 'pre' | 'in' | 'post';

interface Item {
  label: string;
  href?: string;
  done: () => boolean;
  isCurrent: () => boolean;
}

export function SessionTimeline() {
  const session = useSessionStore((s) => s.session);
  const router = useRouter();

  if (!session) return null;

  const stages: { key: Stage; title: string; items: Item[] }[] = [
    {
      key: 'pre',
      title: 'Pre-Game',
      items: [
        {
          label: 'War Room',
          href: '/war-room',
          done: () => session.steps.warRoom,
          isCurrent: () => !session.steps.warRoom,
        },
        {
          label: 'Gameplan',
          href: '/gameplan',
          done: () => session.steps.gameplan,
          isCurrent: () =>
            session.steps.warRoom && !session.steps.gameplan,
        },
        {
          label: 'Kill Sheet',
          href: '/gameplan?tab=kill-sheet',
          done: () => session.steps.gameplan,
          isCurrent: () => false,
        },
      ],
    },
    {
      key: 'in',
      title: 'In Game',
      items: [
        {
          label: session.playing ? 'I\'m In Game ►' : 'I\'m In Game',
          href: '/dashboard',
          done: () => session.steps.playing && !session.playing,
          isCurrent: () => session.playing,
        },
        {
          label: 'Coaching Active',
          done: () => session.steps.playing && !session.playing,
          isCurrent: () => session.playing && !session.coachingPaused,
        },
        {
          label: 'TiltGuard On',
          done: () => session.steps.playing && !session.playing,
          isCurrent: () => session.playing,
        },
      ],
    },
    {
      key: 'post',
      title: 'Post-Game',
      items: [
        {
          label: 'Log Result',
          href: '/dashboard',
          done: () => session.steps.logged,
          isCurrent: () =>
            session.steps.playing && !session.playing && !session.steps.logged,
        },
        {
          label: 'LoopAI Update',
          done: () => session.steps.logged,
          isCurrent: () => false,
        },
        {
          label: 'Vault Entry',
          href: '/vault',
          done: () => false,
          isCurrent: () => session.steps.logged,
        },
      ],
    },
  ];

  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/60 p-5">
      <p className="mb-3 text-[10px] font-bold uppercase tracking-wider text-dark-400">
        Session Timeline
      </p>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {stages.map((stage, i) => (
          <div key={stage.key} className="relative">
            <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-forge-400">
              {stage.title}
            </p>
            <ul className="space-y-1.5">
              {stage.items.map((item, idx) => {
                const done = item.done();
                const current = !done && item.isCurrent();
                const clickable = !!item.href;
                const Wrap: React.ElementType = clickable ? 'button' : 'div';
                return (
                  <li key={idx}>
                    <Wrap
                      type={clickable ? 'button' : undefined}
                      onClick={
                        clickable && item.href
                          ? () => router.push(item.href as string)
                          : undefined
                      }
                      className={clsx(
                        'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs transition-colors',
                        clickable && 'hover:bg-dark-800/60',
                        done
                          ? 'text-forge-300'
                          : current
                          ? 'text-forge-200'
                          : 'text-dark-500'
                      )}
                    >
                      {done ? (
                        <Check className="h-3.5 w-3.5 text-forge-400" />
                      ) : current ? (
                        <ChevronRight className="h-3.5 w-3.5 animate-pulse text-forge-300" />
                      ) : (
                        <Circle className="h-3.5 w-3.5 text-dark-600" />
                      )}
                      <span>{item.label}</span>
                    </Wrap>
                  </li>
                );
              })}
            </ul>
            {i < stages.length - 1 && (
              <div className="pointer-events-none absolute right-0 top-1/2 hidden h-px w-4 -translate-y-1/2 bg-dark-700 md:block" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
