/**
 * Filter panel for the Arsenal library — title-aware (categories +
 * situations come from titleMeta).
 */

'use client';

import { clsx } from 'clsx';
import {
  TITLE_WEAPON_CATEGORIES,
  TITLE_SITUATIONS,
  type ArsenalTitleId,
} from '@/lib/arsenal/titleMeta';
import type { WeaponFilters as WF } from '@/hooks/useArsenal';

interface Props {
  titleId: ArsenalTitleId;
  filters: WF;
  onChange: (next: WF) => void;
}

function Radio<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T | undefined;
  options: { value: T | undefined; label: string }[];
  onChange: (v: T | undefined) => void;
}) {
  return (
    <div>
      <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-dark-500">
        {label}
      </p>
      <div className="space-y-1">
        {options.map((o) => (
          <button
            key={o.label}
            type="button"
            onClick={() => onChange(o.value)}
            className={clsx(
              'flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-xs transition-colors',
              value === o.value
                ? 'bg-forge-500/15 text-forge-300'
                : 'text-dark-300 hover:bg-dark-800'
            )}
          >
            <span
              className={clsx(
                'h-2 w-2 rounded-full',
                value === o.value ? 'bg-forge-400' : 'bg-dark-600'
              )}
            />
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function WeaponFilters({ titleId, filters, onChange }: Props) {
  const categories = TITLE_WEAPON_CATEGORIES[titleId] ?? [];
  const situations = TITLE_SITUATIONS[titleId] ?? [];

  const set = <K extends keyof WF>(key: K, value: WF[K] | undefined) =>
    onChange({ ...filters, [key]: value });

  return (
    <div className="space-y-5 rounded-xl border border-dark-700/50 bg-dark-900/60 p-4">
      <Radio
        label="Category"
        value={filters.category}
        onChange={(v) => set('category', v)}
        options={[
          { value: undefined, label: 'All Categories' },
          ...categories.map((c) => ({ value: c, label: c })),
        ]}
      />

      <Radio
        label="Difficulty"
        value={filters.difficulty}
        onChange={(v) => set('difficulty', v)}
        options={[
          { value: undefined, label: 'All' },
          { value: 'easy', label: 'Easy' },
          { value: 'medium', label: 'Medium' },
          { value: 'hard', label: 'Hard' },
        ]}
      />

      <Radio
        label="Source"
        value={filters.source}
        onChange={(v) => set('source', v)}
        options={[
          { value: undefined, label: 'All' },
          { value: 'platform', label: 'Platform Verified' },
          { value: 'community', label: 'Community' },
          { value: 'my-uploads', label: 'My Uploads' },
        ]}
      />

      {situations.length > 0 && (
        <Radio
          label="Situation"
          value={filters.situation}
          onChange={(v) => set('situation', v)}
          options={[
            { value: undefined, label: 'All' },
            ...situations.map((s) => ({ value: s, label: s })),
          ]}
        />
      )}

      <div>
        <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-dark-500">
          Sort
        </p>
        <select
          value={filters.sort ?? 'most-recent'}
          onChange={(e) => set('sort', e.target.value as WF['sort'])}
          className="w-full rounded-md border border-dark-700 bg-dark-800 px-2 py-1.5 text-xs text-dark-200 focus:border-forge-500 focus:outline-none"
        >
          <option value="most-recent">Most Recent</option>
          <option value="most-used">Most Used</option>
          <option value="highest-rated">Highest Rated</option>
          <option value="easiest">Easiest First</option>
        </select>
      </div>
    </div>
  );
}
