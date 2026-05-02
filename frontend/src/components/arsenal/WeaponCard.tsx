/**
 * Weapon card — shown in the library grid and the Discover results.
 * Saved-state shows a green left border + filled bookmark.
 */

'use client';

import {
  Bookmark,
  BookmarkCheck,
  Star,
  Users,
  TrendingUp,
  CheckCircle2,
  Globe,
  Upload,
} from 'lucide-react';
import { clsx } from 'clsx';
import {
  useSaveWeapon,
  useRemoveWeapon,
  type Weapon,
} from '@/hooks/useArsenal';

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
}

export function WeaponCard({ weapon, onView, onAddToGameplan }: WeaponCardProps) {
  const save = useSaveWeapon();
  const remove = useRemoveWeapon();

  const toggleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (weapon.saved) remove.mutate(weapon.id);
    else save.mutate(weapon.id);
  };

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
      {/* Top row: badges + bookmark */}
      <div className="mb-2 flex items-start gap-2">
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
