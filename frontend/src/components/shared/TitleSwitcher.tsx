"use client";

import { useState, useEffect, useRef } from 'react';
import { Lock, ChevronDown } from 'lucide-react';
import clsx from 'clsx';
import {
  FULL_TITLE_LIST,
  type FullTitle,
  type TitleCategory,
  CATEGORY_ORDER,
  CATEGORY_LABELS,
  TIER_REQUIRED,
} from '@/lib/titles';
import { useUIStore } from '@/lib/store';

/** Tier hierarchy for gating comparison. */
const TIER_RANK: Record<string, number> = {
  free: 0,
  competitive: 1,
  elite: 2,
  team: 3,
};

interface TitleSwitcherProps {
  collapsed: boolean;
}

export function TitleSwitcher({ collapsed }: TitleSwitcherProps) {
  const selectedTitle = useUIStore((s) => s.selectedTitle);
  const setTitle = useUIStore((s) => s.setTitle);
  const userTier = useUIStore((s) => s.userTier);

  const [open, setOpen] = useState(false);
  const [upgradePrompt, setUpgradePrompt] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  const current: FullTitle | undefined =
    FULL_TITLE_LIST.find((t) => t.id === selectedTitle) ?? FULL_TITLE_LIST[0];

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setUpgradePrompt(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Group titles by category following CATEGORY_ORDER
  const grouped = CATEGORY_ORDER.reduce<Record<TitleCategory, FullTitle[]>>((acc, cat) => {
    acc[cat] = FULL_TITLE_LIST.filter((t) => t.category === cat);
    return acc;
  }, {} as Record<TitleCategory, FullTitle[]>);

  function isLocked(title: FullTitle): boolean {
    const required = TIER_REQUIRED[title.requiredTier as keyof typeof TIER_REQUIRED] ?? title.requiredTier;
    return (TIER_RANK[userTier] ?? 0) < (TIER_RANK[required] ?? 0);
  }

  function handleTitleClick(title: FullTitle) {
    if (isLocked(title)) {
      setUpgradePrompt(title.id);
    } else {
      setTitle(title.id as Parameters<typeof setTitle>[0]);
      setOpen(false);
      setUpgradePrompt(null);
    }
  }

  // --- Collapsed state: icon + tooltip ---
  if (collapsed) {
    return (
      <div ref={containerRef} className="relative flex justify-center">
        <button
          onClick={() => setOpen(!open)}
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-dark-800/50 text-lg transition-colors hover:bg-dark-700"
          title={current?.name ?? 'Select title'}
        >
          {current?.icon}
        </button>

        {open && (
          <div className="absolute left-0 z-20 mt-1 w-60 max-h-[420px] overflow-y-auto rounded-lg border border-dark-700/50 bg-dark-800 shadow-xl top-full">
            {CATEGORY_ORDER.map((cat) => {
              const titles = grouped[cat];
              if (!titles || titles.length === 0) return null;
              return (
                <div key={cat}>
                  <div className="text-[11px] uppercase tracking-wider text-dark-500 px-3 pt-3 pb-1">
                    {CATEGORY_LABELS[cat]}
                  </div>
                  {titles.map((title) => (
                    <div key={title.id}>
                      <button
                        onClick={() => handleTitleClick(title)}
                        className="flex w-full items-center gap-2.5 px-3 py-2 text-sm transition-colors hover:bg-dark-700/50"
                      >
                        <span className="text-base">{title.icon}</span>
                        <span className={clsx('flex-1 text-left', isLocked(title) ? 'text-dark-500' : 'text-dark-200')}>
                          {title.name}
                        </span>
                        {title.id === selectedTitle && (
                          <div className="h-1.5 w-1.5 rounded-full bg-forge-400" />
                        )}
                        {isLocked(title) && (
                          <>
                            <Lock className="h-3 w-3 text-dark-500" />
                            <span className="text-[10px] px-1.5 rounded bg-amber-500/20 text-amber-400">
                              {title.requiredTier}
                            </span>
                          </>
                        )}
                      </button>
                      {upgradePrompt === title.id && isLocked(title) && (
                        <div className="text-xs text-forge-400 px-3 py-1">
                          Upgrade to {title.requiredTier} to unlock {title.name} &rarr;
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // --- Expanded state: full dropdown button ---
  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => {
          setOpen(!open);
          setUpgradePrompt(null);
        }}
        className="flex w-full items-center gap-2 rounded-lg bg-dark-800/50 px-3 py-2 text-sm text-dark-200 transition-colors hover:bg-dark-700"
      >
        <span className="text-lg">{current?.icon}</span>
        <span className="flex-1 text-left font-medium">{current?.shortName}</span>
        <ChevronDown
          className={clsx(
            'h-4 w-4 text-dark-400 transition-transform',
            open && 'rotate-180'
          )}
        />
      </button>

      {open && (
        <div className="absolute left-0 z-20 mt-1 w-60 max-h-[420px] overflow-y-auto rounded-lg border border-dark-700/50 bg-dark-800 shadow-xl">
          {CATEGORY_ORDER.map((cat) => {
            const titles = grouped[cat];
            if (!titles || titles.length === 0) return null;
            return (
              <div key={cat}>
                <div className="text-[11px] uppercase tracking-wider text-dark-500 px-3 pt-3 pb-1">
                  {CATEGORY_LABELS[cat]}
                </div>
                {titles.map((title) => (
                  <div key={title.id}>
                    <button
                      onClick={() => handleTitleClick(title)}
                      className="flex w-full items-center gap-2.5 px-3 py-2 text-sm transition-colors hover:bg-dark-700/50"
                    >
                      <span className="text-base">{title.icon}</span>
                      <span className={clsx('flex-1 text-left', isLocked(title) ? 'text-dark-500' : 'text-dark-200')}>
                        {title.name}
                      </span>
                      {title.id === selectedTitle && (
                        <div className="h-1.5 w-1.5 rounded-full bg-forge-400" />
                      )}
                      {isLocked(title) && (
                        <>
                          <Lock className="h-3 w-3 text-dark-500" />
                          <span className="text-[10px] px-1.5 rounded bg-amber-500/20 text-amber-400">
                            {title.requiredTier}
                          </span>
                        </>
                      )}
                    </button>
                    {upgradePrompt === title.id && isLocked(title) && (
                      <div className="text-xs text-forge-400 px-3 py-1">
                        Upgrade to {title.requiredTier} to unlock {title.name} &rarr;
                      </div>
                    )}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
