/**
 * Right-side slide-over showing the full execution detail for a weapon.
 * Supports three modes:
 *   - view     : default — read the page, click around
 *   - reading  : VoiceForge speaks the full weapon; the active step is
 *                highlighted in green as it is spoken
 *   - practice : Guided Practice — full-bleed step-by-step coach,
 *                player taps "Done — Next Step" to advance
 */

'use client';

import { useEffect, useRef, useState } from 'react';
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
  Volume2,
  StopCircle,
  Mic,
  ChevronLeft,
  ChevronRight,
  Film,
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
import api from '@/lib/api';
import { AnimaPlayer } from '@/components/animaforge/AnimaPlayer';
import { useAnimaForgeAvailable } from '@/hooks/useAnimaForge';
import { TITLE_TRIGGER_KEYS } from '@/lib/arsenal/titleMeta';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import {
  VisionAudioForgeService,
  type DrillMonitoringHandle,
  type FrameAnalysis,
} from '@/lib/services/visionaudioforge';
import { getSimLabDetectionConfig } from '@/lib/drills/drillDetectionConfigs';
import { WatchingIndicator } from '@/components/session/WatchingIndicator';
import { CaptureSourceModal } from '@/components/session/CaptureSourceModal';
import {
  useArsenalVoice,
  toneSpeed,
} from '@/lib/arsenal/voiceSettings';
import {
  buildFullReadScript,
  guidedCompletionLine,
  guidedIntroLine,
  guidedSetupToExecutionLine,
  type VoiceSegment,
} from '@/lib/arsenal/voiceScripts';

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

interface ActiveSegment {
  section: VoiceSegment['section'];
  stepIndex?: number;
}

// ---------------------------------------------------------------------------
// Top-level slide-over
// ---------------------------------------------------------------------------

interface WeaponDetailProps {
  weaponId: string | null;
  onClose: () => void;
  /** Optional — if set, enter Guided Practice on open. */
  startInPracticeMode?: boolean;
}

interface ArsenalAnimationState {
  jobId: string | null;
  videoUrl: string | null;
  thumbnailUrl: string | null;
  /** True once the user has explicitly opened/triggered the player. */
  open: boolean;
}

export function WeaponDetail({
  weaponId,
  onClose,
  startInPracticeMode,
}: WeaponDetailProps) {
  const { data: weapon, isLoading } = useWeapon(weaponId);
  const save = useSaveWeapon();
  const remove = useRemoveWeapon();
  const logUsage = useLogUsage();
  const rate = useRateWeapon();
  const router = useRouter();
  const voice = useArsenalVoice();
  const animaforge = useAnimaForgeAvailable();
  const animaforgeAvailable = animaforge.available !== false;

  const [mode, setMode] = useState<'view' | 'reading' | 'practice'>('view');
  const [active, setActive] = useState<ActiveSegment | null>(null);
  const [animation, setAnimation] = useState<ArsenalAnimationState>({
    jobId: null,
    videoUrl: null,
    thumbnailUrl: null,
    open: false,
  });
  const cancelRef = useRef(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Reset animation state whenever the active weapon changes.
  useEffect(() => {
    setAnimation({
      jobId: null,
      videoUrl: null,
      thumbnailUrl: null,
      open: false,
    });
  }, [weaponId]);

  // On mount (per weapon) — check if a previous render already exists so
  // the player auto-shows. Silently ignore failures (AnimaForge offline,
  // unauthenticated, etc).
  useEffect(() => {
    if (!weaponId || !animaforgeAvailable) return;
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get('/animaforge/arsenal/status', {
          params: { weapon_id: weaponId },
        });
        if (cancelled || !data) return;
        const videoUrl: string | undefined = data.video_url;
        const jobId: string | undefined = data.job_id;
        const thumbnailUrl: string | undefined = data.thumbnail_url;
        if (videoUrl) {
          setAnimation({
            jobId: null,
            videoUrl,
            thumbnailUrl: thumbnailUrl ?? null,
            open: true,
          });
        } else if (jobId) {
          setAnimation({
            jobId,
            videoUrl: null,
            thumbnailUrl: thumbnailUrl ?? null,
            open: true,
          });
        }
      } catch {
        // best-effort — leave animation collapsed
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [weaponId, animaforgeAvailable]);

  const handleWatchAnimation = async () => {
    if (!weapon) return;
    if (animation.videoUrl || animation.jobId) {
      // Already loaded — just open the player.
      setAnimation((s) => ({ ...s, open: true }));
      return;
    }
    try {
      const { data } = await api.post('/animaforge/arsenal', {
        weapon_id: weapon.id,
      });
      if (data?.video_url) {
        setAnimation({
          jobId: null,
          videoUrl: data.video_url,
          thumbnailUrl: data.thumbnail_url ?? null,
          open: true,
        });
      } else if (data?.job_id) {
        setAnimation({
          jobId: data.job_id,
          videoUrl: null,
          thumbnailUrl: data.thumbnail_url ?? null,
          open: true,
        });
      }
    } catch {
      // Fail quietly — UI degrades gracefully (no error toast per contract §1).
    }
  };

  // Save to arsenal + fire-and-forget animation render. The toast text is
  // identical regardless of whether AnimaForge is online (it'll just no-op
  // on the server when unavailable) — players save weapons either way.
  const handleSaveAndGenerate = () => {
    if (!weapon) return;
    save.mutate(weapon.id);
    if (animaforgeAvailable) {
      // Fire-and-forget — do not await.
      api
        .post('/animaforge/arsenal', { weapon_id: weapon.id })
        .then(({ data }) => {
          if (data?.video_url) {
            setAnimation((s) => ({
              ...s,
              videoUrl: data.video_url,
              thumbnailUrl: data.thumbnail_url ?? s.thumbnailUrl,
            }));
          } else if (data?.job_id) {
            setAnimation((s) => ({
              ...s,
              jobId: data.job_id,
            }));
          }
        })
        .catch(() => {
          // Silent — graceful degradation.
        });
      showToast('Saved to My Arsenal — animation generating');
    } else {
      showToast('Saved to My Arsenal');
    }
  };

  useEffect(() => {
    if (startInPracticeMode && weapon) setMode('practice');
  }, [startInPracticeMode, weapon]);

  useEffect(() => {
    return () => {
      cancelRef.current = true;
      VoiceForgeService.stop();
    };
  }, []);

  const stopReading = () => {
    cancelRef.current = true;
    VoiceForgeService.stop();
    setMode('view');
    setActive(null);
  };

  const startReading = async (target: 'all' | 'setup' | 'execution' = 'all') => {
    if (!weapon || !voice.enabled) return;
    if (!VoiceForgeService.isAvailable()) return;

    setMode('reading');
    cancelRef.current = false;
    let segments = buildFullReadScript(weapon);
    if (target === 'setup') segments = segments.filter((s) => s.section === 'setup');
    if (target === 'execution')
      segments = segments.filter((s) => s.section === 'execution');

    const speed = toneSpeed(voice.tone);
    for (const seg of segments) {
      if (cancelRef.current) break;
      setActive({ section: seg.section, stepIndex: seg.stepIndex });
      // First call interrupts whatever was queued (e.g. previous read).
      await VoiceForgeService.speakAsync(seg.text, {
        speed,
        interruptCurrent: seg === segments[0],
      });
    }
    if (!cancelRef.current) {
      setActive(null);
      setMode('view');

      // Brief follow-up listen — let the player ask for a repeat without
      // having to click anything.
      try {
        const heard = (await VoiceForgeService.listen({ timeout: 5000 })).toLowerCase();
        if (cancelRef.current) return;
        if (heard.includes('repeat setup')) {
          startReading('setup');
        } else if (heard.includes('repeat execution')) {
          startReading('execution');
        } else if (heard.includes('repeat')) {
          startReading(target);
        }
        // "got it" / silence / anything else — just exit.
      } catch {
        // Ignore — listening is best-effort.
      }
    }
  };

  if (!weaponId) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-dark-950/60 backdrop-blur-sm"
        onClick={mode === 'practice' ? undefined : onClose}
        aria-hidden
      />
      <aside
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[480px] flex-col overflow-hidden border-l border-dark-700 bg-dark-900 shadow-2xl"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between border-b border-dark-700/50 px-5 py-3">
          <h2 className="text-sm font-bold text-dark-100">
            {mode === 'practice' ? 'Guided Practice' : 'Weapon Detail'}
          </h2>
          <div className="flex items-center gap-1.5">
            {mode === 'reading' ? (
              <button
                onClick={stopReading}
                className="inline-flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-2 py-1 text-[11px] font-bold text-red-300 hover:bg-red-500/20"
              >
                <StopCircle className="h-3.5 w-3.5" />
                Stop
              </button>
            ) : mode === 'view' ? (
              <>
                {voice.enabled && VoiceForgeService.isAvailable() && (
                  <>
                    <button
                      onClick={() => startReading('all')}
                      title="Read instructions aloud"
                      className="inline-flex items-center gap-1 rounded-md border border-forge-500/40 bg-forge-500/10 px-2 py-1 text-[11px] font-bold text-forge-300 hover:bg-forge-500/20"
                    >
                      <Volume2 className="h-3.5 w-3.5" />
                      Read
                    </button>
                    <button
                      onClick={() => setMode('practice')}
                      title="Step-by-step guided practice"
                      className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-2 py-1 text-[11px] font-bold text-dark-200 hover:bg-dark-700"
                    >
                      <Mic className="h-3.5 w-3.5" />
                      Practice
                    </button>
                  </>
                )}
                {animaforgeAvailable && (
                  <button
                    onClick={handleWatchAnimation}
                    title="Watch animated play diagram"
                    className="inline-flex items-center gap-1 rounded-md border border-purple-500/40 bg-purple-500/10 px-2 py-1 text-[11px] font-bold text-purple-300 hover:bg-purple-500/20"
                  >
                    <Film className="h-3.5 w-3.5" />
                    Watch Animation
                  </button>
                )}
              </>
            ) : null}
            <button
              onClick={mode === 'practice' ? () => setMode('view') : onClose}
              className="rounded-md p-1 text-dark-400 hover:bg-dark-800 hover:text-dark-100"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {isLoading || !weapon ? (
          <div className="p-6 text-sm text-dark-400">Loading…</div>
        ) : mode === 'practice' ? (
          <PracticeMode
            weapon={weapon}
            voiceEnabled={
              voice.enabled && voice.guidedPractice && VoiceForgeService.isAvailable()
            }
            speed={toneSpeed(voice.tone)}
            onExit={() => setMode('view')}
            onMarkPracticed={() => {
              logUsage.mutate({
                weapon_id: weapon.id,
                title_id: weapon.title_id,
                deployed: false,
                notes: 'guided-practice',
              });
              setMode('view');
            }}
          />
        ) : (
          <WeaponDetailBody
            weapon={weapon}
            active={active}
            animation={animation}
            onAnimationReady={(url) =>
              setAnimation((s) => ({ ...s, videoUrl: url }))
            }
            onSave={handleSaveAndGenerate}
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
            onReadSetup={() => startReading('setup')}
            onReadExecution={() => startReading('execution')}
          />
        )}

        {toastMessage && (
          <div
            role="status"
            aria-live="polite"
            className="pointer-events-none absolute bottom-4 left-1/2 z-50 -translate-x-1/2 rounded-md border border-forge-500/40 bg-dark-800/95 px-3 py-2 text-[12px] font-medium text-forge-200 shadow-lg"
          >
            {toastMessage}
          </div>
        )}
      </aside>
    </>
  );
}

// ---------------------------------------------------------------------------
// View body — reads and highlights the active section / step
// ---------------------------------------------------------------------------

function WeaponDetailBody({
  weapon,
  active,
  animation,
  onAnimationReady,
  onSave,
  onRemove,
  onPracticed,
  onPracticeInSimLab,
  onRate,
  onReadSetup,
  onReadExecution,
}: {
  weapon: Weapon;
  active: ActiveSegment | null;
  animation: ArsenalAnimationState;
  onAnimationReady: (videoUrl: string) => void;
  onSave: () => void;
  onRemove: () => void;
  onPracticed: () => void;
  onPracticeInSimLab: () => void;
  onRate: (stars: number) => void;
  onReadSetup: () => void;
  onReadExecution: () => void;
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

  const isActiveStep = (section: VoiceSegment['section'], idx: number) =>
    active?.section === section && active.stepIndex === idx;

  const stepClass = (section: VoiceSegment['section'], idx: number) =>
    clsx(
      'flex gap-2 rounded-md px-2 py-1 transition-colors',
      isActiveStep(section, idx) &&
        'border-l-2 border-forge-400 bg-forge-500/10 font-bold text-dark-50'
    );

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
      <Section
        title="When to Deploy"
        icon={Target}
        highlighted={active?.section === 'when'}
      >
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
        <Section
          title="Pre-Execution Setup"
          icon={ListChecks}
          highlighted={active?.section === 'setup'}
          action={
            <button
              type="button"
              onClick={onReadSetup}
              className="inline-flex items-center gap-1 rounded-md border border-forge-500/30 bg-forge-500/5 px-2 py-0.5 text-[10px] font-medium text-forge-300 hover:bg-forge-500/15"
            >
              <Volume2 className="h-3 w-3" />
              Read setup
            </button>
          }
        >
          <ol className="space-y-1 text-xs text-dark-200">
            {weapon.setup_steps.map((step, i) => (
              <li key={i} className={stepClass('setup', i)}>
                <span className="font-bold text-forge-400">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {/* Execution */}
      {weapon.instructions?.length > 0 && (
        <Section
          title="Execution Steps"
          icon={Play}
          highlighted={active?.section === 'execution'}
          action={
            <button
              type="button"
              onClick={onReadExecution}
              className="inline-flex items-center gap-1 rounded-md border border-forge-500/30 bg-forge-500/5 px-2 py-0.5 text-[10px] font-medium text-forge-300 hover:bg-forge-500/15"
            >
              <Volume2 className="h-3 w-3" />
              Read execution
            </button>
          }
        >
          <ol className="space-y-1 text-xs text-dark-200">
            {weapon.instructions.map((step, i) => (
              <li key={i} className={stepClass('execution', i)}>
                <span className="font-bold text-forge-400">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {/* AnimaForge animated play diagram — appears once user clicks
          [Watch Animation] in the header, or auto-shows if a previously
          rendered job exists for this weapon. */}
      {animation.open && (animation.videoUrl || animation.jobId) && (
        <Section title="Animated Play Diagram" icon={Film}>
          <AnimaPlayer
            jobId={animation.jobId ?? undefined}
            videoUrl={animation.videoUrl ?? undefined}
            thumbnailUrl={animation.thumbnailUrl ?? undefined}
            type="weapon-diagram"
            onReady={onAnimationReady}
          />
        </Section>
      )}

      {/* Why it works */}
      <Section title="Why It Works" highlighted={active?.section === 'why'}>
        <p className="text-xs leading-relaxed text-dark-300">{weapon.description}</p>
      </Section>

      {/* Counter */}
      {counter !== undefined && counter !== null && (
        <Section
          title="Counter (what opponent can do)"
          icon={AlertTriangle}
          highlighted={active?.section === 'counter'}
        >
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
  action,
  highlighted,
  children,
}: {
  title: string;
  icon?: React.ComponentType<{ className?: string }>;
  action?: React.ReactNode;
  highlighted?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      className={clsx(
        'rounded-md transition-colors',
        highlighted && 'bg-forge-500/5'
      )}
    >
      <div className="mb-2 flex items-center justify-between">
        <h4 className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-dark-400">
          {Icon && <Icon className="h-3.5 w-3.5 text-forge-400" />}
          {title}
        </h4>
        {action}
      </div>
      {children}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Practice mode
// ---------------------------------------------------------------------------

interface PracticeModeProps {
  weapon: Weapon;
  voiceEnabled: boolean;
  speed: number;
  onExit: () => void;
  onMarkPracticed: () => void;
}

interface PracticeStep {
  phase: 'setup' | 'execution' | 'transition' | 'intro' | 'done';
  text: string;
  index?: number;
  total?: number;
}

function buildPracticeSteps(weapon: Weapon): PracticeStep[] {
  const steps: PracticeStep[] = [
    { phase: 'intro', text: guidedIntroLine(weapon) },
  ];
  weapon.setup_steps?.forEach((s, i) =>
    steps.push({
      phase: 'setup',
      text: s,
      index: i,
      total: weapon.setup_steps.length,
    })
  );
  if (weapon.setup_steps?.length && weapon.instructions?.length) {
    steps.push({ phase: 'transition', text: guidedSetupToExecutionLine() });
  }
  weapon.instructions?.forEach((s, i) =>
    steps.push({
      phase: 'execution',
      text: s,
      index: i,
      total: weapon.instructions.length,
    })
  );
  steps.push({ phase: 'done', text: guidedCompletionLine(weapon) });
  return steps;
}

interface PracticeRep {
  id: number;
  success: boolean;
  confidence: number;
  reason: string;
  autoDetected: boolean;
}

function PracticeMode({
  weapon,
  voiceEnabled,
  speed,
  onExit,
  onMarkPracticed,
}: PracticeModeProps) {
  const steps = buildPracticeSteps(weapon);
  const [idx, setIdx] = useState(0);
  const [listening, setListening] = useState(false);
  const [watching, setWatching] = useState(false);
  const [practiceReps, setPracticeReps] = useState<PracticeRep[]>([]);
  const [showCaptureSourceModal, setShowCaptureSourceModal] = useState(false);
  const cancelRef = useRef(false);
  const idxRef = useRef(0);
  const watchHandleRef = useRef<DrillMonitoringHandle | null>(null);
  idxRef.current = idx;

  const cur = steps[idx]!;
  const inExecutionPhase = cur?.phase === 'execution';
  const successfulReps = practiceReps.filter((r) => r.success).length;
  const TARGET_SUCCESS_REPS = 3;

  // Auto-start watching when entering the execution phase, auto-stop when
  // leaving it (or on completion).
  useEffect(() => {
    if (!inExecutionPhase) {
      if (watching) {
        watchHandleRef.current?.stop();
        watchHandleRef.current = null;
        setWatching(false);
      }
      return;
    }
    if (watching) return;

    let cancelled = false;
    (async () => {
      if (!VisionAudioForgeService.getCaptureSource()) {
        setShowCaptureSourceModal(true);
        return;
      }
      const ok = await VisionAudioForgeService.isAvailable();
      if (cancelled || !ok) return;

      const config = getSimLabDetectionConfig(
        undefined,
        weapon.name,
        weapon.formation ?? undefined,
        weapon.play_name ?? undefined
      );
      watchHandleRef.current = VisionAudioForgeService.startDrillMonitoring({
        mode: 'arsenal-practice',
        titleId: weapon.title_id,
        weaponId: weapon.id,
        weaponName: weapon.name,
        formation: weapon.formation ?? undefined,
        playName: weapon.play_name ?? undefined,
        detectionConfig: config,
        onRepDetected: handleRepDetected,
      });
      setWatching(true);
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inExecutionPhase]);

  useEffect(() => {
    return () => watchHandleRef.current?.stop();
  }, []);

  const handleRepDetected = (analysis: FrameAnalysis) => {
    if (analysis.success === null) return;
    setPracticeReps((prev) => {
      const next: PracticeRep[] = [
        ...prev,
        {
          id: prev.length + 1,
          success: analysis.success === true,
          confidence: analysis.confidence,
          reason: analysis.reason || '',
          autoDetected: true,
        },
      ];
      const successCount = next.filter((r) => r.success).length;
      if (voiceEnabled) {
        if (analysis.success) {
          VoiceForgeService.speak(
            successCount >= TARGET_SUCCESS_REPS
              ? `Three clean reps detected. You have ${weapon.name} ready to deploy. ArsenalAI will signal the moment in your next game.`
              : `Detected. ${weapon.name} executed correctly. Rep ${next.length} complete. Practice it again to build consistency.`,
            { interruptCurrent: true, speed }
          );
        } else {
          VoiceForgeService.speak(
            `Missed. ${analysis.reason || 'Review the setup steps.'} Try it again.`,
            { interruptCurrent: true, speed }
          );
        }
      }
      return next;
    });
  };

  const overrideRep = (success: boolean) => {
    handleRepDetected({
      playInProgress: false,
      repCompleted: true,
      success,
      coverageDetected: null,
      playDetected: null,
      executionQuality: success ? 'clean' : 'poor',
      confidence: 100,
      reason: success ? 'Manually marked success' : 'Manually marked failed',
    });
  };

  useEffect(() => {
    cancelRef.current = false;
    return () => {
      cancelRef.current = true;
      VoiceForgeService.stop();
    };
  }, []);

  // Speak whenever the active step changes, then listen briefly for a voice
  // command so the player can advance hands-free.
  useEffect(() => {
    if (!voiceEnabled) return;
    const cur = steps[idx];
    if (!cur) return;
    let prefix = '';
    if (cur.phase === 'setup' && cur.index !== undefined) {
      prefix = `Setup step ${cur.index + 1} of ${cur.total}. `;
    } else if (cur.phase === 'execution' && cur.index !== undefined) {
      prefix = `Execution step ${cur.index + 1} of ${cur.total}. `;
    }

    let cancelled = false;
    (async () => {
      await VoiceForgeService.speakAsync(prefix + cur.text, {
        speed,
        interruptCurrent: true,
      });
      if (cancelled || cancelRef.current) return;
      if (cur.phase === 'done') return; // stay put on completion screen.

      setListening(true);
      try {
        const heard = (await VoiceForgeService.listen({ timeout: 8000 }))
          .toLowerCase()
          .trim();
        if (cancelled || cancelRef.current) return;
        // Only react if the index hasn't already moved (button press wins).
        if (idxRef.current !== idx) return;
        if (
          heard.includes('next') ||
          heard.includes('got it') ||
          heard.includes('ready') ||
          heard.includes('done')
        ) {
          setIdx((i) => Math.min(i + 1, steps.length - 1));
        } else if (heard.includes('back') || heard.includes('previous')) {
          setIdx((i) => Math.max(i - 1, 0));
        } else if (heard.includes('repeat') || heard.includes('say that again')) {
          // Re-trigger by toggling — bumping a state we already own would
          // be cleaner but this avoids an extra useState.
          setIdx((i) => i);
          // Force re-speak by quickly bouncing index; the speak effect re-runs
          // only when idx changes, so call directly.
          await VoiceForgeService.speakAsync(prefix + cur.text, {
            speed,
            interruptCurrent: true,
          });
        } else if (heard.includes('stop') || heard.includes('exit')) {
          onExit();
        }
      } catch {
        // Ignore — listening is best-effort.
      } finally {
        if (!cancelled) setListening(false);
      }
    })();

    return () => {
      cancelled = true;
      VoiceForgeService.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, voiceEnabled]);

  const next = () => {
    if (idx < steps.length - 1) setIdx(idx + 1);
  };
  const back = () => {
    if (idx > 0) setIdx(idx - 1);
  };
  const repeat = () => setIdx((i) => i);

  const isDone = cur.phase === 'done';
  const phaseLabel: Record<PracticeStep['phase'], string> = {
    intro: 'Welcome',
    setup: 'Setup',
    execution: 'Execution',
    transition: 'Transition',
    done: 'Complete',
  };

  // Progress dots — only count setup + execution steps.
  const realSteps = steps.filter(
    (s) => s.phase === 'setup' || s.phase === 'execution'
  );
  const realIdx = realSteps.findIndex((s) => s === cur);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <p className="text-[11px] font-bold uppercase tracking-wider text-forge-400">
          Guided Practice — {weapon.name}
        </p>
        <p className="text-[11px] text-dark-400">
          Coach will walk you through each step. Tap [Done — Next Step] to advance.
        </p>

        <div className="mt-5 rounded-xl border border-forge-500/30 bg-emerald-950/20 p-5">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-bold uppercase tracking-wider text-forge-300">
              {phaseLabel[cur.phase]}
              {cur.index !== undefined && cur.total
                ? ` — Step ${cur.index + 1} of ${cur.total}`
                : ''}
            </p>
            {realSteps.length > 0 && (
              <div className="flex items-center gap-1">
                {realSteps.map((_, i) => (
                  <span
                    key={i}
                    className={clsx(
                      'h-1.5 w-1.5 rounded-full',
                      i < realIdx
                        ? 'bg-forge-500'
                        : i === realIdx
                        ? 'bg-forge-300'
                        : 'bg-dark-600'
                    )}
                  />
                ))}
              </div>
            )}
          </div>

          <p className="text-lg font-semibold leading-relaxed text-dark-50">
            {cur.text}
          </p>
        </div>

        {/* Execution-phase watching panel */}
        {inExecutionPhase && (
          <div className="mt-4 space-y-2">
            <WatchingIndicator
              isWatching={watching}
              onStop={() => {
                watchHandleRef.current?.stop();
                watchHandleRef.current = null;
                setWatching(false);
              }}
              mode="arsenal"
              detail={weapon.name}
            />
            <p className="text-[11px] text-dark-400">
              Go to your game and run:{' '}
              <span className="text-dark-200">
                {weapon.name}
                {weapon.formation ? ` from ${weapon.formation}` : ''}
              </span>
            </p>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-dark-500">
                Reps
              </span>
              {Array.from({ length: TARGET_SUCCESS_REPS }).map((_, i) => {
                const rep = practiceReps.filter((r) => r.success)[i];
                return (
                  <span
                    key={i}
                    className={clsx(
                      'inline-flex h-5 w-5 items-center justify-center rounded-full border text-[10px] font-bold',
                      rep
                        ? 'border-forge-500 bg-forge-500/20 text-forge-300'
                        : 'border-dark-700 text-dark-600'
                    )}
                  >
                    {rep ? '✓' : i + 1}
                  </span>
                );
              })}
              <span className="text-[10px] text-dark-500">
                {successfulReps} of {TARGET_SUCCESS_REPS} clean
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-[10px]">
              <span className="text-dark-500">Override:</span>
              <button
                type="button"
                onClick={() => overrideRep(true)}
                className="rounded-md border border-forge-500/30 bg-forge-500/10 px-2 py-0.5 font-medium text-forge-300 hover:bg-forge-500/20"
              >
                ✓ It worked
              </button>
              <button
                type="button"
                onClick={() => overrideRep(false)}
                className="rounded-md border border-red-500/30 bg-red-500/10 px-2 py-0.5 font-medium text-red-300 hover:bg-red-500/20"
              >
                ✗ It failed
              </button>
              {successfulReps >= TARGET_SUCCESS_REPS && (
                <button
                  type="button"
                  onClick={onMarkPracticed}
                  className="ml-auto rounded-md bg-forge-500 px-3 py-1 text-[11px] font-bold text-dark-950 hover:bg-forge-400"
                >
                  ✓ I Practiced This
                </button>
              )}
            </div>
          </div>
        )}

        <CaptureSourceModal
          open={showCaptureSourceModal}
          onClose={() => setShowCaptureSourceModal(false)}
          onSelected={() => setShowCaptureSourceModal(false)}
        />

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={repeat}
            disabled={!voiceEnabled}
            className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-1.5 text-[11px] font-medium text-dark-200 hover:bg-dark-700 disabled:opacity-50"
          >
            <Volume2 className="h-3 w-3" /> Repeat
          </button>
          {listening && (
            <span className="inline-flex items-center gap-1 rounded-md border border-forge-500/30 bg-forge-500/10 px-2 py-1 text-[10px] font-medium text-forge-300">
              <Mic className="h-3 w-3 animate-pulse" />
              Say "next", "back", "repeat", or "stop"
            </span>
          )}
          <button
            type="button"
            onClick={onExit}
            className="ml-auto inline-flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-[11px] font-bold text-red-300 hover:bg-red-500/20"
          >
            <StopCircle className="h-3 w-3" /> Stop
          </button>
        </div>
      </div>

      <div className="border-t border-dark-700/50 bg-dark-900 px-5 py-3">
        {isDone ? (
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={back}
              className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-2 text-xs font-medium text-dark-200 hover:bg-dark-700"
            >
              <ChevronLeft className="h-3.5 w-3.5" /> Back
            </button>
            <button
              type="button"
              onClick={onMarkPracticed}
              className="rounded-md bg-forge-500 px-4 py-2 text-xs font-bold text-dark-950 hover:bg-forge-400"
            >
              ✓ Mark as Practiced
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={back}
              disabled={idx === 0}
              className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-2 text-xs font-medium text-dark-200 hover:bg-dark-700 disabled:opacity-40"
            >
              <ChevronLeft className="h-3.5 w-3.5" /> Back
            </button>
            <button
              type="button"
              onClick={next}
              className="inline-flex items-center gap-1 rounded-md bg-forge-500 px-4 py-2 text-xs font-bold text-dark-950 hover:bg-forge-400"
            >
              ✓ Done — Next Step
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
