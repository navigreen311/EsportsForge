'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { Target, Lightbulb, Zap, AlertTriangle, Loader2 } from 'lucide-react';
import { Badge } from '@/components/shared/Badge';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
import { Card } from '@/components/shared/Card';
import { ImpactScore } from '@/components/gameplan/ImpactScore';
import SimLabButton from '@/components/gameplan/SimLabButton';
import EvidencePanel from '@/components/gameplan/EvidencePanel';
import ThreeLayerAudible from '@/components/gameplan/ThreeLayerAudible';
import PlayerTwinBadge, { PLAY_EXECUTION_PCT } from '@/components/gameplan/PlayerTwinBadge';
import ProofAIEvidence from '@/components/gameplan/ProofAIEvidence';
import MetaExpiryWarning from '@/components/gameplan/MetaExpiryWarning';
import { PLAY_META_RISK } from '@/components/gameplan/MetaVersionExpiry';
import { PLAY_MASTERY } from '@/components/gameplan/MasteryDot';
import AnimaPlayer from '@/components/animaforge/AnimaPlayer';
import AnimatedPlayDiagram from '@/components/gameplan/AnimatedPlayDiagram';
import { useAnimaForgeAvailable } from '@/hooks/useAnimaForge';
import {
  getPlayDiagramStatus,
  renderPlayDiagram,
} from '@/lib/animaforge/api';
import type { PlayDiagramRenderResult } from '@/lib/animaforge/types';
import type { Play } from '@/types/gameplan';
import { VoiceForgeService } from '@/lib/services/voiceforge';

// Coverage matrix — what a play beats vs what it gets killed by, plus the
// natural counter when an opponent rotates out of the soft coverage. Keyed by
// the value of `play.beats`. Falls through to a single-line render when no
// entry exists.
const COVERAGE_MATRIX: Record<
  string,
  { worksAgainst: string[]; vulnerableTo: string; counter: string }
> = {
  'Cover 3': {
    worksAgainst: ['Cover 3', 'Cover 3 Sky', 'Cover 3 Buzz'],
    vulnerableTo: 'Cover 2 Man with safety help over the top',
    counter: 'Inside Zone or Back Shoulder Fade',
  },
  'Cover 2': {
    worksAgainst: ['Cover 2', 'Cover 2 Zone', 'Tampa 2'],
    vulnerableTo: 'Cover 4 with the corners squeezing routes',
    counter: 'Mesh Concept or HB Wheel out of the backfield',
  },
  'Cover 1': {
    worksAgainst: ['Cover 1', 'Cover 1 Robber', 'Man-Free'],
    vulnerableTo: 'Cover 0 / all-out blitz with no safety',
    counter: 'Hot route Slant or quick Screen to the field',
  },
  'Cover 4': {
    worksAgainst: ['Cover 4', 'Quarters', 'Cover 4 Palms'],
    vulnerableTo: 'Cover 3 Sky with a robber dropping under',
    counter: 'PA Crossers or Stick Concept underneath',
  },
  'Cover 0': {
    worksAgainst: ['Cover 0', 'All-Out Blitz', 'Zero Pressure'],
    vulnerableTo: 'Soft Cover 2 dropping into space',
    counter: 'Inside Zone or RPO bubble to relieve pressure',
  },
  Man: {
    worksAgainst: ['Cover 1', 'Cover 0', 'Press Man'],
    vulnerableTo: 'Pattern-match zone with safety help',
    counter: 'Pick concepts or in-breaking routes from bunch',
  },
  Zone: {
    worksAgainst: ['Cover 2', 'Cover 3', 'Cover 4'],
    vulnerableTo: 'Disguised man-coverage rotations',
    counter: 'Iso routes vs the weakest man defender',
  },
};

interface PlayDetailProps {
  play: Play | null;
  opponentName?: string;
  /** Opponent's most likely coverage shell (drives per-coverage cache key). */
  opponentCoverage?: string | null;
}

const situationLabels: Record<string, string> = {
  'red-zone': 'Inside the 20',
  'goal-line': 'Goal line (1-3 yards)',
  '3rd-down': '3rd down conversions',
  '2-minute': '2-minute drill / hurry-up',
  'opening-drive': 'Opening drive / script',
  'anti-blitz': 'When opponent sends pressure',
  prevent: 'Prevent / clock kill',
  'hurry-up': 'No-huddle tempo',
};

export default function PlayDetail({
  play,
  opponentName = 'Opponent',
  opponentCoverage = null,
}: PlayDetailProps) {
  // useAnimaForgeAvailable returns `{ available, loading }`. Reading the
  // hook's whole return value as a boolean makes the gating condition always
  // truthy (objects are truthy) AND — far worse — produces a fresh object
  // reference on every render, which puts the variable in the
  // pre-fetch effect's deps array and causes the effect to fire on EVERY
  // render. That effect resets showPlayer/animJob/animLoading/animError, so
  // every Watch click was instantly stomped (visible as a brief
  // disabled-cursor flicker, no panel). Destructure the boolean.
  const { available: animaAvailable } = useAnimaForgeAvailable();
  const [animJob, setAnimJob] = useState<PlayDiagramRenderResult | null>(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const [animLoading, setAnimLoading] = useState(false);
  const [animError, setAnimError] = useState<string | null>(null);
  const [voiceAvailable, setVoiceAvailable] = useState(false);

  useEffect(() => {
    setVoiceAvailable(VoiceForgeService.isAvailable());
  }, []);

  const handleReadPlay = () => {
    if (!play) return;
    const audibleText = play.audibleOptions
      ?.map((a) => `${a.label} when ${a.trigger}`)
      .join('. ');
    const situationText = play.situationTags
      .map((t) => situationLabels[t] ?? t)
      .join(', ');
    const beatsText = play.beats ? `This play beats ${play.beats}.` : '';
    const script = [
      `${play.name} from ${play.formation}.`,
      play.description,
      situationText && `Call when: ${situationText}.`,
      `Confidence ${Math.round(play.confidenceScore)} percent.`,
      audibleText && `Audibles: ${audibleText}.`,
      beatsText,
    ]
      .filter(Boolean)
      .join(' ');
    VoiceForgeService.speak(script, { interruptCurrent: true });
  };

  // The backend returns snake_case (`job_id`, `video_url`, `thumbnail_url`)
  // but the type union also exposes the camelCase aliases. Normalize on read
  // so gating + AnimaPlayer props don't depend on which convention the wire
  // happens to use.
  const animJobId = animJob?.jobId ?? animJob?.job_id ?? undefined;
  const animVideoUrl = animJob?.videoUrl ?? animJob?.video_url ?? undefined;
  const animThumbnailUrl =
    animJob?.thumbnailUrl ?? animJob?.thumbnail_url ?? undefined;

  // Pre-request the play animation as soon as the panel mounts (or when the
  // selected play / coverage variant changes). This way the render is already
  // in flight by the time the user clicks Watch. The pre-fetch is best-effort:
  // if it fails (e.g. AnimaForge can probe healthy but the render submission
  // bombs because the service isn't really there), `animJob` stays null and
  // `handleWatch` will retry on demand and surface the failure.
  useEffect(() => {
    if (!play || !animaAvailable) return;
    let cancelled = false;
    const coverageKey = opponentCoverage ?? 'none';

    // Reset previous variant's state when the selection changes.
    setAnimJob(null);
    setShowPlayer(false);
    setAnimLoading(false);
    setAnimError(null);

    (async () => {
      try {
        const existing = await getPlayDiagramStatus(play.id, coverageKey);
        if (cancelled) return;
        const existingJobId = existing?.jobId ?? existing?.job_id;
        const existingVideoUrl = existing?.videoUrl ?? existing?.video_url;
        if (existingVideoUrl || existingJobId) {
          setAnimJob(existing);
          return;
        }
        const fresh = await renderPlayDiagram({
          play_id: play.id,
          opponent_coverage: coverageKey,
        });
        if (!cancelled) setAnimJob(fresh);
      } catch {
        // Pre-fetch failed silently — handleWatch will retry on click.
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [play?.id, opponentCoverage, animaAvailable]);

  // Click handler for the [Watch] button. Always gives feedback: if a job is
  // already in hand from the pre-fetch we just open the player; otherwise we
  // fire a fresh render with a loading state on the button and a graceful
  // inline error if AnimaForge is unreachable.
  const handleWatch = async () => {
    if (!play) return;
    setAnimError(null);

    if (animJobId || animVideoUrl) {
      setShowPlayer(true);
      return;
    }

    setAnimLoading(true);
    setShowPlayer(true);
    try {
      const coverageKey = opponentCoverage ?? 'none';
      const fresh = await renderPlayDiagram({
        play_id: play.id,
        opponent_coverage: coverageKey,
      });
      setAnimJob(fresh);
    } catch {
      // Keep the panel visible so the error renders in-place (otherwise the
      // panel flashes then disappears and the user thinks "nothing happened").
      setAnimError(
        'Animation service is offline right now — the play diagram can\'t render. Try again later.'
      );
    } finally {
      setAnimLoading(false);
    }
  };

  const handleRetryWatch = () => {
    setAnimError(null);
    void handleWatch();
  };

  if (!play) {
    return (
      <Card className="flex h-full items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Target className="mx-auto mb-3 h-10 w-10 text-dark-600" />
          <p className="text-dark-400 font-medium">Select a play</p>
          <p className="mt-1 text-sm text-dark-600">
            Click a play from the list to view its details
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card padding="lg" className="space-y-5">
      {/* Header + 3. SimLab Button */}
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-dark-500">
          {play.formation}
        </p>
        <div className="mt-1 flex items-center gap-3">
          <h2 className="text-2xl font-bold text-dark-50">{play.name}</h2>
          <SimLabButton
            play={play}
            opponentName={opponentName}
            opponentCoverage={opponentCoverage}
          />
          <a
            href={`/drills/simlab?play=${encodeURIComponent(play.name)}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-forge-500/30 bg-forge-500/10 px-3 py-1.5 text-xs font-medium text-forge-400 transition-colors hover:bg-forge-500/20 hover:border-forge-500/50"
          >
            Test in SimLab
          </a>
          {voiceAvailable && (
            <button
              type="button"
              onClick={handleReadPlay}
              className="inline-flex items-center gap-1.5 rounded-lg border border-forge-500/30 bg-forge-500/10 px-3 py-1.5 text-xs font-medium text-forge-400 transition-colors hover:bg-forge-500/20 hover:border-forge-500/50"
              aria-label="Read this play aloud"
            >
              <span aria-hidden="true">🔊</span> Read
            </button>
          )}
          {animaAvailable && (
            <button
              type="button"
              onClick={handleWatch}
              disabled={animLoading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-forge-500/30 bg-forge-500/10 px-3 py-1.5 text-xs font-medium text-forge-400 transition-colors hover:bg-forge-500/20 hover:border-forge-500/50 disabled:cursor-not-allowed disabled:opacity-60"
              aria-label="Watch animated play diagram"
            >
              {animLoading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Loading…</span>
                </>
              ) : (
                <>
                  <span aria-hidden="true">🎬</span> Watch
                </>
              )}
            </button>
          )}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {play.isKillSheetPlay && (
            <Badge variant="success" size="sm" dot>
              Kill Sheet Play
            </Badge>
          )}
          {/* PlayerTwin Execution Badge */}
          {PLAY_EXECUTION_PCT[play.id] !== undefined && (
            <PlayerTwinBadge executionPct={PLAY_EXECUTION_PCT[play.id]!} />
          )}
          {/* Meta Expiry Warning */}
          <MetaExpiryWarning playId={play.id} />
        </div>
      </div>

      {/* Trending-Countered meta note (FIX 9) — explains *what to do* with the
          warning badge, not just that it's there. */}
      {PLAY_META_RISK[play.id] === 'trending-countered' && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400" />
            <div className="text-sm text-amber-200">
              <p className="font-semibold text-amber-300">Meta Note</p>
              <p className="mt-1 text-amber-200/90">
                {play.name} is seeing increased defensive recognition this
                patch. If running it, pair with a complementary call (e.g.
                Fades or Back Shoulder) so the defender stays honest.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Practice CTA (FIX 10) — surfaces a Drill Lab link for plays the
          player hasn't mastered yet. */}
      {(PLAY_MASTERY[play.id] === 'practicing' ||
        PLAY_MASTERY[play.id] === 'learning') && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
          <p className="text-sm text-amber-200/90">
            You&apos;re still building reps on this play. Confidence will
            activate in ranked once you hit 80%+ in Drill Lab.
          </p>
          <Link
            href={`/drills?drill=${encodeURIComponent(play.id)}&playName=${encodeURIComponent(
              play.name
            )}`}
            className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-500/15 px-3 py-1.5 text-xs font-medium text-amber-300 transition-colors hover:bg-amber-500/25 hover:border-amber-500/60"
          >
            <span aria-hidden="true">▶</span>
            Practice {play.name} in Drill Lab
          </Link>
        </div>
      )}

      {/* Concept Breakdown */}
      <div>
        <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
          <Zap className="h-4 w-4 text-forge-400" />
          Concept Breakdown
        </h3>
        <p className="text-sm leading-relaxed text-dark-300">{play.description}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {play.conceptTags.map((tag) => (
            <Badge key={tag} variant="neutral" size="sm">
              {tag}
            </Badge>
          ))}
        </div>
      </div>

      {/* Inline animated play diagram — always available, client-side (no render
          service). Player dots ride their routes over a timeline. Complements
          the optional AnimaForge server-rendered video below. Self-degrades to
          formation / null, so it's safe to mount unconditionally. */}
      <div>
        <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
          <span aria-hidden="true">🏈</span>
          Play Diagram
        </h3>
        <AnimatedPlayDiagram play={play} />
      </div>

      {/* AnimaForge animated play diagram. Mounted any time [Watch] is open;
          renders pending / error / video states inline so the panel never just
          disappears on the user. */}
      {animaAvailable && showPlayer && (
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
            <span aria-hidden="true">🎬</span>
            Animated Play Diagram
            {opponentCoverage && (
              <Badge variant="neutral" size="sm">
                vs {opponentCoverage}
              </Badge>
            )}
          </h3>
          {animError ? (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-400" />
                <div className="flex-1 text-sm text-red-200">
                  <p className="font-semibold text-red-300">
                    Animation unavailable
                  </p>
                  <p className="mt-1 text-red-200/90">{animError}</p>
                  <div className="mt-3 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleRetryWatch}
                      disabled={animLoading}
                      className="inline-flex items-center gap-1.5 rounded-md border border-red-500/40 bg-red-500/15 px-3 py-1 text-xs font-semibold text-red-300 transition-colors hover:bg-red-500/25 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {animLoading ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : null}
                      Try again
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setAnimError(null);
                        setShowPlayer(false);
                      }}
                      className="rounded-md border border-dark-700 bg-dark-800/60 px-3 py-1 text-xs font-medium text-dark-300 transition-colors hover:bg-dark-700"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : animJobId || animVideoUrl ? (
            <AnimaPlayer
              jobId={animJobId}
              videoUrl={animVideoUrl}
              thumbnailUrl={animThumbnailUrl}
              type="play-diagram"
              onReady={(url) =>
                setAnimJob((prev) => ({
                  ...(prev ?? {}),
                  video_url: url,
                  videoUrl: url,
                }))
              }
            />
          ) : (
            <div className="rounded-lg border border-dark-700 bg-dark-900 p-6 text-center">
              <Loader2 className="mx-auto mb-2 h-6 w-6 animate-spin text-forge-400" />
              <p className="text-sm font-medium text-dark-200">
                Starting render…
              </p>
              <p className="mt-1 text-xs text-dark-400">
                AnimaForge usually returns a play diagram in 30–60 seconds.
              </p>
            </div>
          )}
        </div>
      )}

      {/* When to Call */}
      {play.situationTags.length > 0 && (
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
            <Target className="h-4 w-4 text-amber-400" />
            When to Call
          </h3>
          <ul className="space-y-1.5">
            {play.situationTags.map((tag) => (
              <li
                key={tag}
                className="flex items-center gap-2 text-sm text-dark-300"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-dark-500" />
                {situationLabels[tag] ?? tag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Expected Success Rate + 6. ImpactRank Score */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-dark-200">
          Expected Success Rate
        </h3>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <ConfidenceBar
              value={play.confidenceScore}
              label="Confidence"
              size="lg"
              showValue
            />
          </div>
          <ImpactScore playId={play.id} layout="detail" />
        </div>
      </div>

      {/* 2. ProofAI Evidence Panel */}
      <EvidencePanel playId={play.id} />

      {/* ProofAI Statistical Evidence */}
      <ProofAIEvidence playId={play.id} />

      {/* 5. Three-Layer Call Structure (replaces flat audible list) */}
      {play.audibleOptions && play.audibleOptions.length > 0 && (
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-dark-200">
            Call Structure
          </h3>
          <ThreeLayerAudible
            playName={play.name}
            audibles={play.audibleOptions}
          />
        </div>
      )}

      {/* Coverage Matrix (FIX 13) — what the play beats, what kills it, and
          the natural counter when an opponent rotates out. Falls back to the
          single-line beats when no matrix entry exists. */}
      {play.beats && (
        <div className="rounded-lg border border-forge-800/30 bg-forge-950/20 p-3">
          <div className="flex items-start gap-2">
            <Lightbulb className="mt-0.5 h-4 w-4 flex-shrink-0 text-forge-400" />
            <div className="space-y-1.5 text-sm">
              <p className="text-forge-300">
                This play beats{' '}
                <span className="font-semibold text-forge-400">
                  {play.beats}
                </span>
              </p>
              {COVERAGE_MATRIX[play.beats] && (
                <>
                  <p className="text-forge-300/90">
                    <span className="text-forge-400">✓ Works against:</span>{' '}
                    {COVERAGE_MATRIX[play.beats]!.worksAgainst.join(', ')}
                  </p>
                  <p className="text-forge-300/90">
                    <span className="text-red-400">✗ Vulnerable to:</span>{' '}
                    {COVERAGE_MATRIX[play.beats]!.vulnerableTo}
                  </p>
                  <p className="text-forge-300/90">
                    <span className="text-amber-400">→ Counter with:</span>{' '}
                    {COVERAGE_MATRIX[play.beats]!.counter}
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
