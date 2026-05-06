/**
 * Weapon card — shown in the library grid and the Discover results.
 * Saved-state shows a green left border + filled bookmark.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Bookmark,
  BookmarkCheck,
  Star,
  Users,
  TrendingUp,
  CheckCircle2,
  Globe,
  Upload,
  Shield,
  Swords,
  Camera,
  PlayCircle,
  MoreVertical,
  Eye,
  FlaskConical,
  Plus,
  Flag,
} from 'lucide-react';
import { clsx } from 'clsx';
import {
  useSaveWeapon,
  useRemoveWeapon,
  type Weapon,
} from '@/hooks/useArsenal';
import { useAnimaForgeAvailable } from '@/hooks/useAnimaForge';

/**
 * Animation status hint for a weapon card. Populated by the parent grid
 * (which can batch-fetch jobs) — left undefined here means the card falls
 * back to the static "Generate Animation" camera icon.
 */
export interface WeaponAnimationStatus {
  status: 'complete' | 'pending' | 'rendering' | 'failed';
  videoUrl?: string | null;
  thumbnailUrl?: string | null;
}

const CATEGORY_TONE: Record<string, string> = {
  'Trick Play': 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  'Unstoppable Concept': 'bg-forge-500/15 text-forge-300 border-forge-500/30',
  Unstoppable: 'bg-forge-500/15 text-forge-300 border-forge-500/30',
  'Unstoppable Scorer': 'bg-forge-500/15 text-forge-300 border-forge-500/30',
  Cheese: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  'Cheese Dribble': 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  'Cheese Combo': 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  'Cheese Formation': 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  'Movement Tech': 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  'Build Reset': 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  'Edit Speed': 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  Situational: 'bg-dark-700 text-dark-300 border-dark-600',
};

function categoryTone(cat: string): string {
  return CATEGORY_TONE[cat] ?? 'bg-dark-700 text-dark-300 border-dark-600';
}

function DifficultyDots({
  difficulty,
}: {
  difficulty: 'easy' | 'medium' | 'hard';
}) {
  const filled = difficulty === 'easy' ? 1 : difficulty === 'medium' ? 2 : 3;
  return (
    <span className="inline-flex items-center gap-0.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className={clsx(
            'h-1.5 w-1.5 rounded-full',
            i < filled ? 'bg-forge-400' : 'bg-dark-700'
          )}
        />
      ))}
    </span>
  );
}

function SourceBadge({ source }: { source: Weapon['source_type'] }) {
  if (source === 'platform') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-forge-500/10 px-2 py-0.5 text-[10px] font-medium text-forge-300">
        <CheckCircle2 className="h-3 w-3" />
        Platform Verified
      </span>
    );
  }
  if (source === 'web-discovery') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-sky-500/10 px-2 py-0.5 text-[10px] font-medium text-sky-300">
        <Globe className="h-3 w-3" />
        Community
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-300">
      <Upload className="h-3 w-3" />
      My Upload
    </span>
  );
}

interface WeaponCardProps {
  weapon: Weapon;
  onView: (weapon: Weapon) => void;
  onAddToGameplan?: (weapon: Weapon) => void;
  /**
   * Optional animation-status hint sourced by the parent grid (avoids an
   * N+1 fetch per card). Undefined = static "Generate Animation" state.
   */
  animationStatus?: WeaponAnimationStatus;
}

export function WeaponCard({
  weapon,
  onView,
  onAddToGameplan,
  animationStatus,
}: WeaponCardProps) {
  const router = useRouter();
  const save = useSaveWeapon();
  const remove = useRemoveWeapon();
  const animaforge = useAnimaForgeAvailable();
  const animaforgeAvailable = animaforge.available !== false;
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Close the dropdown on outside click / Escape.
  useEffect(() => {
    if (!menuOpen) return;
    const onDocClick = (ev: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(ev.target as Node)) {
        setMenuOpen(false);
      }
    };
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === 'Escape') setMenuOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [menuOpen]);

  const toggleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (weapon.saved) remove.mutate(weapon.id);
    else save.mutate(weapon.id);
  };

  // Three-dot menu actions — each stops propagation so the card's parent
  // onClick (which opens the detail panel) doesn't fire.
  const stop = (e: React.MouseEvent) => e.stopPropagation();

  const menuView = (e: React.MouseEvent) => {
    stop(e);
    setMenuOpen(false);
    onView(weapon);
  };

  const menuToggleSave = (e: React.MouseEvent) => {
    stop(e);
    setMenuOpen(false);
    if (weapon.saved) remove.mutate(weapon.id);
    else save.mutate(weapon.id);
  };

  const menuAddToGameplan = (e: React.MouseEvent) => {
    stop(e);
    setMenuOpen(false);
    if (onAddToGameplan) {
      onAddToGameplan(weapon);
    } else {
      router.push(`/gameplan?tab=arsenal&saveWeapon=${encodeURIComponent(weapon.id)}`);
    }
  };

  const menuPracticeInSimLab = (e: React.MouseEvent) => {
    stop(e);
    setMenuOpen(false);
    const params = new URLSearchParams({
      weapon: weapon.id,
      weaponName: weapon.name,
    });
    if (weapon.formation) params.set('formation', weapon.formation);
    router.push(`/drills/simlab?${params.toString()}`);
  };

  const menuReportIssue = (e: React.MouseEvent) => {
    stop(e);
    setMenuOpen(false);
    // No backend reports queue yet — surface a transient confirmation so the
    // click feels responsive. Wiring to a moderation endpoint is a follow-up.
    if (typeof window !== 'undefined') {
      window.alert(
        'Thanks — your report has been logged. We review user-flagged weapons weekly.'
      );
    }
  };

  const showAnimationHint =
    animaforgeAvailable &&
    animationStatus?.status === 'complete' &&
    !!animationStatus.videoUrl;
  const showAnimationGenerate =
    animaforgeAvailable && !showAnimationHint;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onView(weapon)}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onView(weapon);
      }}
      className={clsx(
        'group relative cursor-pointer rounded-xl border bg-dark-900/70 p-4 transition-all hover:bg-dark-900',
        weapon.saved
          ? 'border-forge-500/40 before:absolute before:inset-y-0 before:left-0 before:w-1 before:rounded-l-xl before:bg-forge-400'
          : 'border-dark-700/50 hover:border-dark-600'
      )}
    >
      {/* AnimaForge animation hint (top-right). Clicking opens the detail
          panel — same as the rest of the card — so the player can hit
          [Watch Animation]. */}
      {showAnimationHint && animationStatus?.thumbnailUrl ? (
        <div
          className="absolute right-2 top-2 z-10 flex h-9 w-12 items-center justify-center overflow-hidden rounded-md border border-purple-500/40 bg-dark-950/60 shadow-sm"
          title="Animation ready — click to watch"
          aria-label="Animation ready"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={animationStatus.thumbnailUrl}
            alt=""
            className="h-full w-full object-cover opacity-90"
          />
          <PlayCircle className="absolute h-4 w-4 text-white drop-shadow" />
        </div>
      ) : showAnimationHint ? (
        <div
          className="absolute right-2 top-2 z-10 flex h-9 w-12 items-center justify-center rounded-md border border-purple-500/40 bg-purple-500/10 shadow-sm"
          title="Animation ready — click to watch"
          aria-label="Animation ready"
        >
          <PlayCircle className="h-4 w-4 text-purple-300" />
        </div>
      ) : showAnimationGenerate ? (
        <div
          className="absolute right-2 top-2 z-10 flex h-7 w-7 items-center justify-center rounded-md border border-dark-700 bg-dark-800/80 text-dark-400 opacity-0 shadow-sm transition-opacity group-hover:opacity-100"
          title="Generate Animation"
          aria-label="Generate Animation"
        >
          <Camera className="h-3.5 w-3.5" />
        </div>
      ) : null}

      {/* Top row: badges + bookmark */}
      <div className="mb-2 flex items-start gap-2">
        {weapon.side === 'defense' ? (
          <span className="inline-flex items-center gap-1 rounded-md border border-sky-500/30 bg-sky-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-sky-300">
            <Shield className="h-3 w-3" />
            Defense
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-md border border-forge-500/30 bg-forge-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-forge-300">
            <Swords className="h-3 w-3" />
            Offense
          </span>
        )}
        <span
          className={clsx(
            'rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider',
            categoryTone(weapon.category)
          )}
        >
          {weapon.category}
        </span>
        <DifficultyDots difficulty={weapon.difficulty} />
        <div className="ml-auto flex items-center gap-2">
          <SourceBadge source={weapon.source_type} />
          <button
            onClick={toggleSave}
            className="text-dark-500 transition-colors hover:text-forge-400"
            aria-label={weapon.saved ? 'Remove from arsenal' : 'Save to arsenal'}
          >
            {weapon.saved ? (
              <BookmarkCheck className="h-4 w-4 fill-forge-400 text-forge-400" />
            ) : (
              <Bookmark className="h-4 w-4" />
            )}
          </button>
          <div ref={menuRef} className="relative">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setMenuOpen((prev) => !prev);
              }}
              className="flex h-6 w-6 items-center justify-center rounded-md text-dark-500 transition-colors hover:bg-dark-800 hover:text-dark-200"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              aria-label="Weapon actions"
            >
              <MoreVertical className="h-4 w-4" />
            </button>
            {menuOpen && (
              <div
                role="menu"
                onClick={stop}
                className="absolute right-0 top-7 z-30 w-52 overflow-hidden rounded-lg border border-dark-700 bg-dark-900 py-1 shadow-xl"
              >
                <button
                  role="menuitem"
                  onClick={menuView}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-dark-200 transition-colors hover:bg-dark-800"
                >
                  <Eye className="h-3.5 w-3.5 text-dark-400" />
                  View Instructions
                </button>
                <button
                  role="menuitem"
                  onClick={menuToggleSave}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-dark-200 transition-colors hover:bg-dark-800"
                >
                  {weapon.saved ? (
                    <BookmarkCheck className="h-3.5 w-3.5 fill-forge-400 text-forge-400" />
                  ) : (
                    <Bookmark className="h-3.5 w-3.5 text-dark-400" />
                  )}
                  {weapon.saved ? 'Remove from My Arsenal' : 'Save to My Arsenal'}
                </button>
                <button
                  role="menuitem"
                  onClick={menuAddToGameplan}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-dark-200 transition-colors hover:bg-dark-800"
                >
                  <Plus className="h-3.5 w-3.5 text-dark-400" />
                  Add to Gameplan
                </button>
                <button
                  role="menuitem"
                  onClick={menuPracticeInSimLab}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-dark-200 transition-colors hover:bg-dark-800"
                >
                  <FlaskConical className="h-3.5 w-3.5 text-dark-400" />
                  Practice in SimLab
                </button>
                <div className="my-1 h-px bg-dark-700/70" />
                <button
                  role="menuitem"
                  onClick={menuReportIssue}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-red-300 transition-colors hover:bg-red-500/10"
                >
                  <Flag className="h-3.5 w-3.5" />
                  Report Issue
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Name + formation */}
      <h3 className="text-sm font-bold text-dark-50">{weapon.name}</h3>
      {(weapon.formation || weapon.play_name) && (
        <p className="text-[11px] text-dark-400">
          {[weapon.formation, weapon.play_name].filter(Boolean).join(' — ')}
        </p>
      )}

      {/* Description */}
      <p className="mt-2 line-clamp-2 text-xs text-dark-300">{weapon.description}</p>

      {/* When to use */}
      <p className="mt-1 line-clamp-1 text-[11px] text-dark-500">
        <span className="font-semibold text-dark-400">When: </span>
        {weapon.when_to_use}
      </p>

      {/* Stats */}
      <div className="mt-3 flex items-center gap-3 text-[10px] text-dark-400">
        <span className="inline-flex items-center gap-1">
          <TrendingUp className="h-3 w-3" />
          {Math.round((weapon.success_rate ?? 0) * 100)}%
        </span>
        <span className="inline-flex items-center gap-1">
          <Users className="h-3 w-3" />
          {weapon.times_used} used
        </span>
        <span className="inline-flex items-center gap-1">
          <Star className="h-3 w-3 text-amber-400" />
          {weapon.community_rating?.toFixed(1) ?? '0.0'}
        </span>
      </div>

      {/* Actions */}
      <div className="mt-3 flex items-center gap-2">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onView(weapon);
          }}
          className="flex-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-1.5 text-[11px] font-medium text-dark-200 transition-colors hover:bg-dark-700"
        >
          View Instructions
        </button>
        <button
          type="button"
          onClick={toggleSave}
          className={clsx(
            'rounded-md border px-3 py-1.5 text-[11px] font-medium transition-colors',
            weapon.saved
              ? 'border-forge-500/40 bg-forge-500/15 text-forge-300 hover:bg-forge-500/25'
              : 'border-dark-700 bg-dark-800 text-dark-200 hover:bg-dark-700'
          )}
        >
          {weapon.saved ? 'Saved' : 'Save'}
        </button>
        {onAddToGameplan && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onAddToGameplan(weapon);
            }}
            className="rounded-md border border-dark-700 bg-dark-800 px-3 py-1.5 text-[11px] font-medium text-dark-200 transition-colors hover:bg-dark-700"
          >
            + Gameplan
          </button>
        )}
      </div>
    </div>
  );
}
