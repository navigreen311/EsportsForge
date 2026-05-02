/**
 * Right-side slide-over showing the full execution detail for a weapon.
 */

'use client';

import { useState } from 'react';
import {
  X,
  Star,
  Bookmark,
  BookmarkCheck,
  Target,
  Play,
  CheckSquare,
  ListChecks,
  AlertTriangle,
  PlayCircle,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useRouter } from 'next/navigation';
import {
  useWeapon,
  useSaveWeapon,
  useRemoveWeapon,
  useLogUsage,
  useRateWeapon,
  type Weapon,
} from '@/hooks/useArsenal';
import { TITLE_TRIGGER_KEYS } from '@/lib/arsenal/titleMeta';

const TRIGGER_KEY_LABEL: Record<string, string> = {
  down: 'Down',
  distance: 'Distance',
  fieldPosition: 'Field position',
  quarter: 'Quarter / time',
  scoreMargin: 'Score margin',
  opponentTendency: 'Opponent tendency',
  consecutiveRuns: 'Consecutive runs',
  shotClock: 'Shot clock',
  pointMargin: 'Point differential',
  defenderPosition: 'Defender positioning',
  stamina: 'Stamina',
  gameMode: 'Game mode',
  possession: 'Possession zone',
  half: 'Half',
  scoreline: 'Scoreline',
  opponentShape: 'Opponent shape',
  pressingIntensity: 'Pressing intensity',
  fieldZone: 'Field zone',
  count: 'Count',
  inning: 'Inning',
  runners: 'Runners',
  outs: 'Outs',
  batterTendency: 'Batter tendency',
  pitcherStamina: 'Pitcher stamina',
  circlePhase: 'Circle phase',
  squadCount: 'Squad count',
  height: 'Height advantage',
  loadout: 'Loadout',
  endgamePosition: 'Endgame position',
  storm: 'Storm',
  materials: 'Materials',
  playerCount: 'Player count',
  buildPhase: 'Build phase',
  round: 'Round',
  position: 'Position',
  healthBar: 'Health',
  distance_max: 'Max distance',
  style: 'Style',
  wind: 'Wind',
  lie: 'Lie',
  elevation: 'Elevation',
  green: 'Green',
  pressure: 'Pressure',
  guardHealth: 'Guard health',
  stance: 'Stance',
  momentum: 'Momentum',
  hand: 'Hand dealt',
  paytable: 'Paytable',
  credits: 'Credits',
  sessionLength: 'Session length',
};

function formatTriggerValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'object' && value !== null) return JSON.stringify(value);
  return String(value);
}

function StarPicker({
  current,
  onPick,
}: {
  current: number;
  onPick: (n: number) => void;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const display = hover ?? current;
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onMouseEnter={() => setHover(n)}
          onMouseLeave={() => setHover(null)}
          onClick={() => onPick(n)}
          className="text-amber-400 transition-transform hover:scale-110"
          aria-label={`Rate ${n} stars`}
        >
          <Star
            className={clsx(
              'h-4 w-4',
              n <= display ? 'fill-amber-400' : 'fill-transparent'
            )}
          />
        </button>
      ))}
    </div>
  );
}

interface WeaponDetailProps {
  weaponId: string | null;
  onClose: () => void;
}

export function WeaponDetail({ weaponId, onClose }: WeaponDetailProps) {
  const { data: weapon, isLoading } = useWeapon(weaponId);
  const save = useSaveWeapon();
  const remove = useRemoveWeapon();
  const logUsage = useLogUsage();
  const rate = useRateWeapon();
  const router = useRouter();

  if (!weaponId) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-dark-950/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <aside
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[480px] flex-col overflow-hidden border-l border-dark-700 bg-dark-900 shadow-2xl"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between border-b border-dark-700/50 px-5 py-3">
          <h2 className="text-sm font-bold text-dark-100">Weapon Detail</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-dark-400 hover:bg-dark-800 hover:text-dark-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {isLoading || !weapon ? (
          <div className="p-6 text-sm text-dark-400">Loading…</div>
        ) : (
          <WeaponDetailBody
            weapon={weapon}
            onSave={() => save.mutate(weapon.id)}
            onRemove={() => remove.mutate(weapon.id)}
            onPracticed={() =>
              logUsage.mutate({
                weapon_id: weapon.id,
                title_id: weapon.title_id,
                deployed: false,
                notes: 'practiced',
              })
            }
            onPracticeInSimLab={() =>
              router.push(`/drills/simlab?weapon=${weapon.id}`)
            }
            onRate={(stars) => rate.mutate({ id: weapon.id, stars })}
          />
        )}
      </aside>
    </>
  );
}

function WeaponDetailBody({
  weapon,
  onSave,
  onRemove,
  onPracticed,
  onPracticeInSimLab,
  onRate,
}: {
  weapon: Weapon;
  onSave: () => void;
  onRemove: () => void;
  onPracticed: () => void;
  onPracticeInSimLab: () => void;
  onRate: (stars: number) => void;
}) {
  const triggerKeys = TITLE_TRIGGER_KEYS[weapon.title_id] ?? [];
  const triggers = weapon.trigger_conditions ?? {};
  const counter = (triggers as Record<string, unknown>).counter;
  const avoid = (triggers as Record<string, unknown>).avoid;

  const triggerRows = Object.entries(triggers)
    .filter(
      ([k]) =>
        k !== 'counter' &&
        k !== 'avoid' &&
        (triggerKeys.includes(k) || k.endsWith('_min') || k.endsWith('_max'))
    )
    .filter(([, v]) => v !== undefined && v !== null);

  return (
    <div className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-center gap-2 text-[10px] font-semibold uppercase tracking-wider">
          <span className="rounded-md border border-forge-500/30 bg-forge-500/10 px-1.5 py-0.5 text-forge-300">
            {weapon.category}
          </span>
          <span className="rounded-md border border-dark-700 bg-dark-800 px-1.5 py-0.5 text-dark-300">
            {weapon.difficulty}
          </span>
          <span className="text-dark-500">{weapon.source_type}</span>
        </div>
        <h3 className="mt-2 text-xl font-bold text-dark-50">{weapon.name}</h3>
        {(weapon.formation || weapon.play_name) && (
          <p className="text-xs text-dark-400">
            {[weapon.formation, weapon.play_name].filter(Boolean).join(' — ')}
          </p>
        )}
        <div className="mt-2 flex items-center gap-3 text-[11px] text-dark-400">
          <span className="inline-flex items-center gap-1">
            <Star className="h-3 w-3 text-amber-400" />
            {weapon.community_rating?.toFixed(1) ?? '0.0'}
            <span className="text-dark-600">({weapon.community_votes})</span>
          </span>
          <span>{Math.round((weapon.success_rate ?? 0) * 100)}% success</span>
          <span>{weapon.times_used} uses</span>
        </div>
      </div>

      {/* When to deploy */}
      <Section title="When to Deploy" icon={Target}>
        <p className="mb-2 text-xs text-dark-300">{weapon.when_to_use}</p>
        {triggerRows.length > 0 && (
          <ul className="space-y-1 text-xs">
            {triggerRows.map(([key, value]) => (
              <li key={key} className="flex items-start gap-2 text-dark-300">
                <CheckSquare className="mt-0.5 h-3 w-3 flex-shrink-0 text-forge-400" />
                <span className="font-semibold text-dark-200">
                  {TRIGGER_KEY_LABEL[key] ?? key}:
                </span>
                <span>{formatTriggerValue(value)}</span>
              </li>
            ))}
          </ul>
        )}
        {avoid !== undefined && avoid !== null && (
          <div className="mt-3 rounded-md border border-amber-500/30 bg-amber-500/10 p-2 text-[11px] text-amber-200">
            <p className="font-semibold">Avoid when</p>
            <p>{formatTriggerValue(avoid)}</p>
          </div>
        )}
      </Section>

      {/* Setup steps */}
      {weapon.setup_steps?.length > 0 && (
        <Section title="Pre-Execution Setup" icon={ListChecks}>
          <ol className="space-y-1 text-xs text-dark-200">
            {weapon.setup_steps.map((step, i) => (
              <li key={i} className="flex gap-2">
                <span className="font-bold text-forge-400">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {/* Execution */}
      {weapon.instructions?.length > 0 && (
        <Section title="Execution Steps" icon={Play}>
          <ol className="space-y-1 text-xs text-dark-200">
            {weapon.instructions.map((step, i) => (
              <li key={i} className="flex gap-2">
                <span className="font-bold text-forge-400">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {/* Why it works */}
      <Section title="Why It Works">
        <p className="text-xs leading-relaxed text-dark-300">{weapon.description}</p>
      </Section>

      {/* Counter */}
      {counter !== undefined && counter !== null && (
        <Section title="Counter (what opponent can do)" icon={AlertTriangle}>
          <p className="text-xs text-dark-300">{formatTriggerValue(counter)}</p>
        </Section>
      )}

      {/* Video */}
      {weapon.video_url && (
        <a
          href={weapon.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-md border border-dark-700 bg-dark-800 px-3 py-2 text-xs text-dark-200 hover:bg-dark-700"
        >
          <PlayCircle className="h-4 w-4 text-forge-400" />
          Watch Example
        </a>
      )}

      {/* Source URL */}
      {weapon.source_url && (
        <p className="break-all text-[10px] text-dark-500">
          Source:{' '}
          <a
            href={weapon.source_url}
            className="text-sky-400 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            {weapon.source_url}
          </a>
        </p>
      )}

      {/* Tags */}
      {weapon.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {weapon.tags.map((t) => (
            <span
              key={t}
              className="rounded-full border border-dark-700 bg-dark-800 px-2 py-0.5 text-[10px] text-dark-300"
            >
              #{t}
            </span>
          ))}
        </div>
      )}

      {/* Rate */}
      <div className="rounded-lg border border-dark-700/50 bg-dark-800/60 px-3 py-2">
        <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-dark-500">
          Rate this play
        </p>
        <StarPicker current={Math.round(weapon.community_rating ?? 0)} onPick={onRate} />
      </div>

      {/* Actions */}
      <div className="grid grid-cols-2 gap-2 pt-2">
        <button
          type="button"
          onClick={weapon.saved ? onRemove : onSave}
          className={clsx(
            'flex items-center justify-center gap-1 rounded-md px-3 py-2 text-xs font-semibold',
            weapon.saved
              ? 'bg-forge-500 text-dark-950 hover:bg-forge-400'
              : 'border border-forge-500/40 bg-forge-500/10 text-forge-300 hover:bg-forge-500/20'
          )}
        >
          {weapon.saved ? (
            <>
              <BookmarkCheck className="h-4 w-4" /> In My Arsenal
            </>
          ) : (
            <>
              <Bookmark className="h-4 w-4" /> Save to My Arsenal
            </>
          )}
        </button>
        <button
          type="button"
          onClick={onPracticeInSimLab}
          className="flex items-center justify-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-2 text-xs font-medium text-dark-200 hover:bg-dark-700"
        >
          <Play className="h-4 w-4" /> Practice in SimLab
        </button>
        <button
          type="button"
          onClick={onPracticed}
          className="col-span-2 flex items-center justify-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-2 text-xs font-medium text-dark-200 hover:bg-dark-700"
        >
          <CheckSquare className="h-4 w-4" /> I Practiced This
        </button>
      </div>
    </div>
  );
}

function Section({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon?: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h4 className="mb-2 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-dark-400">
        {Icon && <Icon className="h-3.5 w-3.5 text-forge-400" />}
        {title}
      </h4>
      {children}
    </section>
  );
}
