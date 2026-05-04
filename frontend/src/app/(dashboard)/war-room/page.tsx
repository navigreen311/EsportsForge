/**
 * War Room — Pre-Game preparation and briefing page.
 * Displays opponent intel, kill sheet, recommendations, and mental prep tools.
 */

'use client';

import { Shield } from 'lucide-react';
import PreGameWarRoom from '@/components/warroom/PreGameWarRoom';
import { WeaponSummaryCard } from '@/components/arsenal/WeaponSummaryCard';
import DefensiveSchemePanel from '@/components/warroom/DefensiveSchemePanel';

export default function WarRoomPage() {
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

      {/* Saved Arsenal weapons for this matchup */}
      <WeaponSummaryCard />

      {/* Defensive scheme — counters opponent's offensive tendencies */}
      <DefensiveSchemePanel />

      {/* War Room Content */}
      <PreGameWarRoom />
    </div>
  );
}
