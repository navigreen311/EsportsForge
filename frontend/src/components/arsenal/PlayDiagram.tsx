/**
 * PlayDiagram — client-side, top-down football play diagram styled after Madden's
 * play-art: dimmed turf + yard lines + hash marks, neon glowing routes that draw
 * in, and clean player chips. Renders from the weapon's concept (see
 * lib/arsenal/playDiagram) — no AnimaForge / render service needed.
 */

'use client';

import { weaponToPlay, type WeaponLike, type Pt } from '@/lib/arsenal/playDiagram';

function pathD(points: Pt[]): string {
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`).join(' ');
}

/** Triangle arrowhead at the route's end, oriented along the last segment. */
function arrowHead(points: Pt[], size = 3): string {
  const n = points.length;
  const last = points[n - 1];
  const prev = points[n - 2];
  if (!last || !prev) return '';
  const [x2, y2] = last;
  const [x1, y1] = prev;
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const a1 = ang + Math.PI * 0.82;
  const a2 = ang - Math.PI * 0.82;
  return [
    `${x2},${y2}`,
    `${x2 + size * Math.cos(a1)},${y2 + size * Math.sin(a1)}`,
    `${x2 + size * Math.cos(a2)},${y2 + size * Math.sin(a2)}`,
  ].join(' ');
}

// Hash-mark tick rows (Madden turf), short vertical ticks down each hash.
const HASH_ROWS = [6, 14, 22, 30, 38, 46, 54, 66, 74, 82, 90];

export function PlayDiagram({ weapon }: { weapon: WeaponLike }) {
  const play = weaponToPlay(weapon);

  return (
    <div className="overflow-hidden rounded-lg border border-dark-700 bg-black">
      <style>{`
        @keyframes pd-draw { 0% { stroke-dashoffset: 1; } 45% { stroke-dashoffset: 0; }
          90% { stroke-dashoffset: 0; } 100% { stroke-dashoffset: 1; } }
        @keyframes pd-tip { 0%, 40% { opacity: 0; } 50%, 90% { opacity: 1; } 100% { opacity: 0; } }
        .pd-route { animation: pd-draw 3.4s ease-in-out infinite; }
        .pd-tip { animation: pd-tip 3.4s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .pd-route, .pd-tip { animation: none; stroke-dashoffset: 0; opacity: 1; }
        }
      `}</style>

      <svg viewBox="0 0 100 100" className="block w-full" role="img"
           aria-label={`Play diagram: ${play.title}, ${play.concept}`}>
        <defs>
          <linearGradient id="pd-turf" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0c2f1d" />
            <stop offset="55%" stopColor="#0a2818" />
            <stop offset="100%" stopColor="#081f13" />
          </linearGradient>
          <filter id="pd-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="0.85" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Dimmed turf */}
        <rect x="0" y="0" width="100" height="100" fill="url(#pd-turf)" />

        {/* Yard lines */}
        {[12, 24, 36, 48, 72, 84].map((y) => (
          <line key={y} x1="0" y1={y} x2="100" y2={y} stroke="#ffffff" strokeWidth="0.25" opacity="0.14" />
        ))}
        {/* Hash marks (two interior columns) */}
        {[38, 62].map((x) =>
          HASH_ROWS.map((y) => (
            <line key={`${x}-${y}`} x1={x} y1={y - 0.9} x2={x} y2={y + 0.9}
                  stroke="#ffffff" strokeWidth="0.35" opacity="0.12" />
          )),
        )}
        {/* Line of scrimmage */}
        <line x1="0" y1="60" x2="100" y2="60" stroke="#fde68a" strokeWidth="0.5" opacity="0.55" />

        {/* Routes (neon, glowing, drawn-in) */}
        <g filter="url(#pd-glow)">
          {play.routes.map((r, i) => {
            const delay = `${i * 0.26}s`;
            return (
              <g key={r.key}>
                <path
                  className="pd-route"
                  d={pathD(r.points)}
                  pathLength={1}
                  fill="none"
                  stroke={r.color}
                  strokeWidth="1.3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ strokeDasharray: 1, animationDelay: delay }}
                />
                <polygon className="pd-tip" points={arrowHead(r.points)} fill={r.color}
                         style={{ animationDelay: delay }} />
              </g>
            );
          })}
        </g>

        {/* Players */}
        {play.players.map((p) => {
          if (p.kind === 'ol') {
            return (
              <rect key={p.key} x={p.x - 1.5} y={p.y - 1.5} width="3" height="3" rx="0.6"
                    fill="#1e293b" stroke="#64748b" strokeWidth="0.3" />
            );
          }
          const isQb = p.kind === 'qb';
          return (
            <g key={p.key}>
              <circle cx={p.x} cy={p.y} r="2.8"
                      fill={isQb ? '#f8fafc' : '#0b1220'}
                      stroke={isQb ? '#0b1220' : '#f8fafc'} strokeWidth="0.5" />
              <text x={p.x} y={p.y + 1.1} textAnchor="middle" fontSize="3" fontWeight="800"
                    fill={isQb ? '#0b1220' : '#f8fafc'}>
                {p.label}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="flex items-center justify-between gap-2 border-t border-dark-800 bg-dark-950 px-3 py-2">
        <p className="text-xs font-semibold text-dark-50">{play.title}</p>
        <p className="text-[10px] font-bold uppercase tracking-wider text-forge-300">
          {play.concept} · {play.formation}
        </p>
      </div>
    </div>
  );
}
