/**
 * AnimatedPlayDiagram — an inline, client-side, top-down football play diagram
 * where the player dots MOVE along their routes over a timeline (play / pause /
 * loop / scrub). Reuses the Madden-style field + route styling from the arsenal
 * PlayDiagram, but adds real temporal motion instead of the arsenal's looping
 * stroke-draw.
 *
 * Data comes from `resolvePlayDiagram(play)`: explicit route coordinates when
 * the play has them, otherwise a concept approximation, otherwise formation
 * only. Returns null (caller shows text) only if nothing renders.
 *
 * No AnimaForge / render service required — this is always available offline.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { Pause, Play as PlayIcon, Repeat } from 'lucide-react';
import { resolvePlayDiagram, type DiagramSource } from '@/lib/gameplan/playDiagram';
import type { Pt } from '@/lib/arsenal/playDiagram';
import type { Play } from '@/types/gameplan';

const CYCLE_MS = 2600; // one full route run-through
const HASH_ROWS = [6, 14, 22, 30, 38, 46, 54, 66, 74, 82, 90];

function pathD(points: Pt[]): string {
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`).join(' ');
}

/** Position along a polyline at normalized progress t∈[0,1] (arc-length). */
function pointAtProgress(points: Pt[], t: number): Pt {
  if (points.length === 0) return [50, 60];
  if (points.length === 1 || t <= 0) return points[0]!;
  if (t >= 1) return points[points.length - 1]!;

  const segLen: number[] = [];
  let total = 0;
  for (let i = 1; i < points.length; i++) {
    const dx = points[i]![0] - points[i - 1]![0];
    const dy = points[i]![1] - points[i - 1]![1];
    const len = Math.hypot(dx, dy);
    segLen.push(len);
    total += len;
  }
  if (total === 0) return points[0]!;

  let target = t * total;
  for (let i = 0; i < segLen.length; i++) {
    if (target <= segLen[i]!) {
      const f = segLen[i]! === 0 ? 0 : target / segLen[i]!;
      return [
        points[i]![0] + (points[i + 1]![0] - points[i]![0]) * f,
        points[i]![1] + (points[i + 1]![1] - points[i]![1]) * f,
      ];
    }
    target -= segLen[i]!;
  }
  return points[points.length - 1]!;
}

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(mq.matches);
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return reduced;
}

const SOURCE_LABEL: Record<DiagramSource, string> = {
  explicit: 'Play routes',
  template: 'Concept approximation',
  formation: 'Formation',
};

export default function AnimatedPlayDiagram({ play }: { play: Play }) {
  const resolved = resolvePlayDiagram(play);
  const reduced = usePrefersReducedMotion();

  const [progress, setProgress] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [loop, setLoop] = useState(true);
  const rafRef = useRef<number | null>(null);
  const lastRef = useRef<number | null>(null);

  // Reduced motion: snap to the finished frame, don't animate.
  useEffect(() => {
    if (reduced) {
      setPlaying(false);
      setProgress(1);
    }
  }, [reduced]);

  useEffect(() => {
    if (!playing || reduced) return;
    const step = (ts: number) => {
      if (lastRef.current == null) lastRef.current = ts;
      const dt = ts - lastRef.current;
      lastRef.current = ts;
      setProgress((p) => {
        let n = p + dt / CYCLE_MS;
        if (n >= 1) n = loop ? n - 1 : 1;
        return n;
      });
      rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      lastRef.current = null;
    };
  }, [playing, loop, reduced]);

  // Auto-stop at the end when not looping.
  useEffect(() => {
    if (!loop && progress >= 1 && playing) setPlaying(false);
  }, [loop, progress, playing]);

  if (!resolved) return null;
  const { data, source } = resolved;
  const hasRoutes = data.routes.length > 0;

  const togglePlay = () => {
    if (!playing && progress >= 1 && !loop) setProgress(0);
    setPlaying((p) => !p);
  };

  // Current animated position for each routed skill player, keyed by player key.
  const routeByKey = new Map(data.routes.map((r) => [r.key, r]));

  return (
    <div className="overflow-hidden rounded-lg border border-dark-700 bg-black">
      <svg
        viewBox="0 0 100 100"
        className="block w-full"
        role="img"
        aria-label={`Animated play diagram: ${data.title}, ${data.concept}`}
      >
        <defs>
          <linearGradient id="apd-turf" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0c2f1d" />
            <stop offset="55%" stopColor="#0a2818" />
            <stop offset="100%" stopColor="#081f13" />
          </linearGradient>
          <filter id="apd-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="0.85" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Turf + yard lines + hashes + LOS */}
        <rect x="0" y="0" width="100" height="100" fill="url(#apd-turf)" />
        {[12, 24, 36, 48, 72, 84].map((y) => (
          <line key={y} x1="0" y1={y} x2="100" y2={y} stroke="#ffffff" strokeWidth="0.25" opacity="0.14" />
        ))}
        {[38, 62].map((x) =>
          HASH_ROWS.map((y) => (
            <line key={`${x}-${y}`} x1={x} y1={y - 0.9} x2={x} y2={y + 0.9}
                  stroke="#ffffff" strokeWidth="0.35" opacity="0.12" />
          )),
        )}
        <line x1="0" y1="60" x2="100" y2="60" stroke="#fde68a" strokeWidth="0.5" opacity="0.55" />

        {/* Routes — full path dimmed, plus a bright trail revealed up to progress */}
        <g filter="url(#apd-glow)">
          {data.routes.map((r) => (
            <g key={r.key}>
              <path d={pathD(r.points)} fill="none" stroke={r.color} strokeWidth="1"
                    strokeLinecap="round" strokeLinejoin="round" opacity="0.28" />
              <path
                d={pathD(r.points)}
                pathLength={1}
                fill="none"
                stroke={r.color}
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ strokeDasharray: 1, strokeDashoffset: 1 - progress }}
              />
            </g>
          ))}
        </g>

        {/* Players — skill players with a route ride it; others stay put */}
        {data.players.map((p) => {
          if (p.kind === 'ol') {
            return (
              <rect key={p.key} x={p.x - 1.5} y={p.y - 1.5} width="3" height="3" rx="0.6"
                    fill="#1e293b" stroke="#64748b" strokeWidth="0.3" />
            );
          }
          const isQb = p.kind === 'qb';
          const route = routeByKey.get(p.key);
          const [cx, cy] = route ? pointAtProgress(route.points, progress) : [p.x, p.y];
          return (
            <g key={p.key}>
              <circle cx={cx} cy={cy} r="2.8"
                      fill={isQb ? '#f8fafc' : '#0b1220'}
                      stroke={isQb ? '#0b1220' : '#f8fafc'} strokeWidth="0.5" />
              <text x={cx} y={cy + 1.1} textAnchor="middle" fontSize="3" fontWeight="800"
                    fill={isQb ? '#0b1220' : '#f8fafc'}>
                {p.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Controls */}
      <div className="flex items-center gap-3 border-t border-dark-800 bg-dark-950 px-3 py-2">
        {hasRoutes && !reduced && (
          <>
            <button
              type="button"
              onClick={togglePlay}
              className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md border border-forge-500/30 bg-forge-500/10 text-forge-300 transition-colors hover:bg-forge-500/20"
              aria-label={playing ? 'Pause play diagram' : 'Play play diagram'}
            >
              {playing ? <Pause className="h-3.5 w-3.5" /> : <PlayIcon className="h-3.5 w-3.5" />}
            </button>
            <button
              type="button"
              onClick={() => setLoop((l) => !l)}
              className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md border transition-colors ${
                loop
                  ? 'border-forge-500/40 bg-forge-500/20 text-forge-300'
                  : 'border-dark-700 bg-dark-800/60 text-dark-400 hover:bg-dark-700'
              }`}
              aria-label="Toggle loop"
              aria-pressed={loop}
            >
              <Repeat className="h-3.5 w-3.5" />
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.001}
              value={progress}
              onChange={(e) => {
                setPlaying(false);
                setProgress(parseFloat(e.target.value));
              }}
              className="h-1 flex-1 cursor-pointer accent-forge-400"
              aria-label="Scrub play timeline"
            />
          </>
        )}
        <div className={`flex items-center gap-2 ${hasRoutes && !reduced ? '' : 'flex-1 justify-between'}`}>
          <p className="whitespace-nowrap text-[10px] font-bold uppercase tracking-wider text-forge-300">
            {data.concept} · {data.formation}
          </p>
          <span
            className="whitespace-nowrap rounded border border-dark-700 bg-dark-900 px-1.5 py-0.5 text-[9px] font-medium text-dark-400"
            title={
              source === 'explicit'
                ? 'Rendered from this play’s route coordinates.'
                : 'A stylized approximation of the concept — not the exact Madden play.'
            }
          >
            {SOURCE_LABEL[source]}
          </span>
        </div>
      </div>
    </div>
  );
}
