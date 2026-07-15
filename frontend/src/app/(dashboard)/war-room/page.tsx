/**
 * War Room — Pre-Game preparation and briefing page.
 * Displays opponent intel, kill sheet, recommendations, and mental prep tools.
 *
 * Phase 1c (1c.2): live coverage banner. When War Room live-vision is enabled
 * (warRoomVisionEnabled), the page provisions a broker session and subscribes to
 * COVERAGE_LOCKED; a detected coverage surfaces a "Cover N detected → adjustment"
 * banner (read-only, auto-dismissed after 30s) via the useCoverageGameState bridge.
 * Silent until a coverage fires — expected, not a bug (ADR 0010 soft-launch shape).
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { Eye, Shield } from 'lucide-react';
import api from '@/lib/api';
import { warRoomVisionEnabled } from '@/lib/vafFlags';
import { useVisionEvents } from '@/hooks/useVisionEvents';
import {
  useCoverageGameState,
  type CoverageGameState,
} from '@/hooks/useCoverageGameState';
import { coverageAdjustment } from '@/lib/warroom/coverageAdjustment';
import PreGameWarRoom from '@/components/warroom/PreGameWarRoom';
import { WeaponSummaryCard } from '@/components/arsenal/WeaponSummaryCard';
import DefensiveSchemePanel from '@/components/warroom/DefensiveSchemePanel';

const DOWN_ORDINAL = ['', '1st', '2nd', '3rd', '4th'];

export default function WarRoomPage() {
  // Phase 1c live-vision: provision a broker session while the flag is on, then
  // subscribe to COVERAGE_LOCKED. Mirrors the Drill Lab / Gameplan pattern.
  const vafFlagOn = warRoomVisionEnabled();
  const [vafSession, setVafSession] = useState<{ sessionId: string; token: string } | null>(null);
  useEffect(() => {
    if (!vafFlagOn) return;
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.post('/visionaudio/sessions/start');
        if (!cancelled) setVafSession({ sessionId: data.session_id, token: data.token });
      } catch {
        // Broker unavailable / disabled server-side — War Room stays static.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [vafFlagOn]);
  const { lastEvent: coverageEvent } = useVisionEvents({
    sessionId: vafSession?.sessionId ?? null,
    token: vafSession?.token ?? null,
    eventType: 'COVERAGE_LOCKED',
    enabled: vafFlagOn && !!vafSession,
  });

  // A detected coverage raises the banner + a 30s auto-dismiss timer (spec #03 —
  // War Room "Cover N detected"). The bridge dedupes by event_id; onCoverage fires
  // once per new coverage.
  const [banner, setBanner] = useState<CoverageGameState | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useCoverageGameState({
    lastEvent: coverageEvent,
    onCoverage: (s) => {
      setBanner(s);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setBanner(null), 30_000);
    },
  });
  useEffect(
    () => () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    },
    [],
  );
  const dismissBanner = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setBanner(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="flex items-center gap-3 text-3xl font-bold text-dark-50">
          <Shield className="h-8 w-8 text-forge-400" />
          Pre-Game War Room
        </h1>
        <p className="mt-1 text-dark-400">
          Intel briefing, kill sheet, and mental prep before you compete.
        </p>
      </div>

      {/* Phase 1c live coverage banner (read-only, 30s auto-dismiss) */}
      {banner && banner.coverage && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-forge-500/40 bg-forge-500/10 px-4 py-3">
          <div className="flex items-start gap-3">
            <Eye className="mt-0.5 h-5 w-5 flex-shrink-0 text-forge-400" />
            <div>
              <p className="text-sm font-semibold text-forge-300">
                {banner.coverage} detected
                {banner.down != null && banner.distance != null && (
                  <span className="ml-2 font-normal text-dark-400">
                    · {DOWN_ORDINAL[banner.down] ?? `${banner.down}`} &amp; {banner.distance}
                  </span>
                )}
              </p>
              <p className="mt-0.5 text-sm text-dark-100">{coverageAdjustment(banner.coverage)}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={dismissBanner}
            aria-label="Dismiss coverage banner"
            className="flex-shrink-0 text-lg leading-none text-forge-400 hover:text-forge-200"
          >
            ×
          </button>
        </div>
      )}

      {/* Saved Arsenal weapons for this matchup */}
      <WeaponSummaryCard />

      {/* Defensive scheme — counters opponent's offensive tendencies */}
      <DefensiveSchemePanel />

      {/* War Room Content */}
      <PreGameWarRoom />
    </div>
  );
}
