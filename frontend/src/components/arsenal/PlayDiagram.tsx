/**
 * PlayDiagram — client-side, top-down football play diagram with animated routes.
 * Renders from the weapon's concept (see lib/arsenal/playDiagram) — no AnimaForge
 * / render service needed. This is the offline "demonstrate the play" surface.
 */

'use client';

import { weaponToPlay, type WeaponLike, type Pt } from '@/lib/arsenal/playDiagram';

function pathD(points: Pt[]): string {
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`).join(' ');
}

/** Triangle arrowhead at the route's end, oriented along the last segment. */
function arrowHead(points: Pt[], size = 3.2): string {
  const n = points.length;
  const last = points[n - 1];
  const prev = points[n - 2];
  if (!last || !prev) return '';
  const [x2, y2] = last;
  const [x1, y1] = prev;
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const a1 = ang + Math.PI * 0.82;
  const a2 = ang - Math.PI * 0.82;
  const p1x = x2 + size * Math.cos(a1);
  const p1y = y2 + size * Math.sin(a1);
  const p2x = x2 + size * Math.cos(a2);
  const p2y = y2 + size * Math.sin(a2);
  return `${x2},${y2} ${p1x},${p1y} ${p2x},${p2y}`;
}

export function PlayDiagram({ weapon }: { weapon: WeaponLike }) {
  const play = weaponToPlay(weapon);

  return (
    <div className="overflow-hidden rounded-lg border border-dark-700 bg-dark-900">
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
        {/* Field */}
        <rect x="0" y="0" width="100" height="100" fill="#14532d" />
        <rect x="0" y="0" width="100" height="100" fill="url(#pd-stripes)" opacity="0.25" />
        <defs>
          <pattern id="pd-stripes" width="100" height="20" patternUnits="userSpaceOnUse">
            <rect x="0" y="0" width="100" height="10" fill="#166534" />
          </pattern>
        </defs>

        {/* Yard lines */}
        {[12, 24, 36, 48, 72, 84].map((y) => (
          <line key={y} x1="2" y1={y} x2="98" y2={y} stroke="#ffffff" strokeWidth="0.3" opacity="0.35" />
        ))}
        {/* Line of scrimmage */}
        <line x1="0" y1="60" x2="100" y2="60" stroke="#fde68a" strokeWidth="0.7" opacity="0.9" />

        {/* Routes + arrowheads */}
        {play.routes.map((r, i) => {
          const delay = `${i * 0.28}s`;
          return (
            <g key={r.key}>
              <path
                className="pd-route"
                d={pathD(r.points)}
                pathLength={1}
                fill="none"
                stroke={r.color}
                strokeWidth="1.1"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ strokeDasharray: 1, animationDelay: delay }}
              />
              <polygon
                className="pd-tip"
                points={arrowHead(r.points)}
                fill={r.color}
                style={{ animationDelay: delay }}
              />
            </g>
          );
        })}

        {/* Players */}
        {play.players.map((p) => {
          if (p.kind === 'ol') {
            return <rect key={p.key} x={p.x - 1.4} y={p.y - 1.4} width="2.8" height="2.8" rx="0.5" fill="#94a3b8" />;
          }
          const fill = p.kind === 'qb' ? '#e5e7eb' : '#0f172a';
          const stroke = p.kind === 'qb' ? '#0f172a' : '#e2e8f0';
          return (
            <g key={p.key}>
              <circle cx={p.x} cy={p.y} r="2.6" fill={fill} stroke={stroke} strokeWidth="0.4" />
              <text x={p.x} y={p.y + 1.1} textAnchor="middle" fontSize="3"
                    fontWeight="700" fill={p.kind === 'qb' ? '#0f172a' : '#e2e8f0'}>
                {p.label}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="flex items-center justify-between gap-2 border-t border-dark-700 px-3 py-2">
        <p className="text-xs font-semibold text-dark-100">{play.title}</p>
        <p className="text-[10px] uppercase tracking-wider text-forge-300">
          {play.concept} · {play.formation}
        </p>
      </div>
    </div>
  );
}
