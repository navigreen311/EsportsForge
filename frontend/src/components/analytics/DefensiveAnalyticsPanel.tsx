/**
 * Defensive analytics panel.
 *
 * Renders title-aware defensive stat cards. Real metrics live behind a
 * server pipeline that doesn't exist yet — when it lands, swap the mock
 * cards for live data fetched from /analytics/defense?title_id=...
 */

'use client';

import {
  Shield,
  Target,
  AlertTriangle,
  Activity,
  TrendingDown,
} from 'lucide-react';
import { Card } from '@/components/shared/Card';
import { StatCard } from '@/components/shared/StatCard';

interface DefensiveStat {
  label: string;
  value: string;
  description?: string;
}

const DEFENSIVE_STATS_BY_TITLE: Record<string, DefensiveStat[]> = {
  'madden-26': [
    { label: 'Points Allowed/Game', value: '21.4', description: 'last 10 games' },
    { label: 'Sacks/Game', value: '2.3' },
    { label: '3rd Down Stop Rate', value: '58%' },
    { label: 'Turnovers Forced', value: '1.7/g' },
  ],
  'cfb-26': [
    { label: 'Points Allowed/Game', value: '24.1' },
    { label: '3rd Down Stop Rate', value: '54%' },
    { label: 'Red Zone Hold Rate', value: '47%' },
    { label: 'Turnovers Forced', value: '1.4/g' },
  ],
  'nba-2k26': [
    { label: 'Opponent FG%', value: '46.2%' },
    { label: 'Blocks/Game', value: '4.1' },
    { label: 'Steals/Game', value: '7.6' },
    { label: 'Defensive Rating', value: '109.4' },
  ],
  'eafc-26': [
    { label: 'Goals Conceded/Match', value: '1.8' },
    { label: 'Clean Sheets', value: '24%' },
    { label: 'Tackles Won %', value: '64%' },
    { label: 'Interceptions/Match', value: '12.3' },
  ],
  'mlb-26': [
    { label: 'ERA', value: '3.84' },
    { label: 'WHIP', value: '1.21' },
    { label: 'Strikeout Rate', value: '24.8%' },
    { label: 'Defensive Efficiency', value: '0.704' },
  ],
  'warzone': [
    { label: 'Deaths/Game', value: '6.2' },
    { label: 'Survival Rate', value: '38%' },
    { label: 'Defensive Kill %', value: '42%' },
    { label: 'Avg Placement', value: '14th' },
  ],
  'fortnite': [
    { label: 'Avg Placement', value: '11th' },
    { label: 'Box Defense Win %', value: '54%' },
    { label: 'High Ground Hold %', value: '46%' },
    { label: 'Storm Survival', value: '78%' },
  ],
  'ufc-5': [
    { label: 'Strikes Absorbed', value: '4.1/min' },
    { label: 'Takedown Defense', value: '68%' },
    { label: 'Submission Defense', value: '83%' },
    { label: 'Block Rate', value: '47%' },
  ],
  'pga-2k25': [
    { label: 'Bogey Avoidance', value: '74%' },
    { label: 'Hazard Avoidance', value: '81%' },
    { label: 'Lay-Up Decision Rate', value: '62%' },
    { label: 'Pressure Putt %', value: '54%' },
  ],
  'undisputed': [
    { label: 'Strikes Absorbed', value: '6.3/r' },
    { label: 'Block Rate', value: '52%' },
    { label: 'Parry Success', value: '34%' },
    { label: 'Cornered Win %', value: '41%' },
  ],
  'video-poker': [
    { label: 'Loss Limit Hit Rate', value: '12%', description: 'sessions' },
    { label: 'Avg Drawdown', value: '24%' },
    { label: 'Tilt Bet-Down Rate', value: '67%' },
    { label: 'Optimal Strategy %', value: '94%' },
  ],
};

const DEFENSIVE_BENCHMARKS_BY_TITLE: Record<string, string[]> = {
  'madden-26': [
    'Cover Recognition',
    'Blitz Timing',
    'User Coverage',
    'Zone Drop Discipline',
    'Red Zone Defense',
    'Pass Rush Efficiency',
  ],
  'cfb-26': [
    'Option Read',
    'RPO Defense',
    'Coverage Disguise',
    'Pass Rush',
  ],
  'nba-2k26': [
    'On-Ball IQ',
    'PNR Coverage',
    'Help Positioning',
    'Closeout Discipline',
    'Steal Timing',
    'Block Timing',
  ],
  'eafc-26': [
    'Tackle Timing',
    'Jockey Discipline',
    'Shape Hold',
    'Aerial Defending',
    'Set Piece Defense',
    'Counter Prevention',
  ],
  'ufc-5': [
    'Takedown Defense',
    'Submission Escape',
    'Head Movement',
    'Block Timing',
    'Counter Punch',
    'Distance Mgmt',
  ],
  'undisputed': [
    'Head Movement',
    'Parry Accuracy',
    'Block Efficiency',
    'Clinch Defense',
    'Counter Punch',
    'Footwork',
  ],
};

const DEFENSIVE_WIN_CONDITIONS_BY_TITLE: Record<string, string[]> = {
  'madden-26': [
    'When leading entering Q4 and holding turnover margin > 0',
    '3rd & long stop rate ≥ 60%',
    'Red zone hold rate ≥ 50%',
    'Pass rush hits ≥ 4 per game',
  ],
  'nba-2k26': [
    'When defending PNR effectively (opp. PNR FG% < 38%)',
    'Steals per game ≥ 7',
    'Holding opponent under FG 45%',
    'Defensive rating < 105',
  ],
  'eafc-26': [
    'Conceding < 1 goal per match',
    'Tackle win rate ≥ 65%',
    'Cross defense win rate ≥ 60%',
    'Set piece concession < 1 per match',
  ],
  'warzone': [
    'Final 3 alive ≥ 40% of games',
    'Cover usage > 70% of engagements',
    'Squad wipe defense ≥ 30% when down 1',
  ],
};

interface Props {
  titleId: string;
}

export default function DefensiveAnalyticsPanel({ titleId }: Props) {
  const stats = DEFENSIVE_STATS_BY_TITLE[titleId] ?? [];
  const benchmarks = DEFENSIVE_BENCHMARKS_BY_TITLE[titleId] ?? [];
  const winConditions = DEFENSIVE_WIN_CONDITIONS_BY_TITLE[titleId] ?? [];

  return (
    <div className="space-y-6">
      {/* Top defensive stats */}
      <div>
        <div className="mb-2 flex items-center gap-2">
          <Shield className="h-4 w-4 text-sky-300" />
          <h3 className="text-sm font-bold text-sky-200">Defensive Performance</h3>
        </div>
        {stats.length > 0 ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {stats.map((s) => (
              <StatCard
                key={s.label}
                label={s.label}
                value={s.value}
              />
            ))}
          </div>
        ) : (
          <Card padding="md">
            <p className="text-xs text-dark-500">
              Defensive stats not configured for this title yet.
            </p>
          </Card>
        )}
      </div>

      {/* BenchmarkAI defensive metrics */}
      <Card padding="lg">
        <div className="mb-3 flex items-center gap-2">
          <Activity className="h-4 w-4 text-sky-300" />
          <h3 className="text-sm font-bold text-dark-100">
            BenchmarkAI — Defensive Skills
          </h3>
        </div>
        {benchmarks.length > 0 ? (
          <ul className="grid grid-cols-2 gap-2 md:grid-cols-3">
            {benchmarks.map((b) => (
              <li
                key={b}
                className="rounded-md border border-dark-700 bg-dark-800/60 px-3 py-2 text-xs text-dark-200"
              >
                {b}
                <span className="ml-1 text-[10px] text-dark-500">
                  · pending data
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-dark-500">
            BenchmarkAI defensive skills not configured for this title yet.
          </p>
        )}
        <p className="mt-3 text-[11px] text-dark-500">
          Live percentile scores activate once the defensive snap-tracking
          pipeline is collecting data.
        </p>
      </Card>

      {/* Defensive win conditions */}
      <Card padding="lg">
        <div className="mb-3 flex items-center gap-2">
          <Target className="h-4 w-4 text-sky-300" />
          <h3 className="text-sm font-bold text-dark-100">
            Defensive Win Conditions
          </h3>
        </div>
        {winConditions.length > 0 ? (
          <ul className="space-y-2">
            {winConditions.map((c) => (
              <li
                key={c}
                className="rounded-md border border-sky-500/20 bg-sky-500/5 p-2 text-xs text-dark-200"
              >
                {c}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-dark-500">
            Defensive win conditions for this title pending.
          </p>
        )}
      </Card>

      {/* Skill transfer stub — empty state */}
      <Card padding="lg">
        <div className="mb-3 flex items-center gap-2">
          <TrendingDown className="h-4 w-4 text-sky-300" />
          <h3 className="text-sm font-bold text-dark-100">
            Defensive Skill Transfer
          </h3>
        </div>
        <p className="text-xs text-dark-500">
          Lab-vs-live defensive transfer chart activates once defensive
          drills have been logged for this title. Run defensive drills in
          Drill Lab to populate.
        </p>
      </Card>

      {/* Honesty footer */}
      <div className="flex items-start gap-2 rounded-md border border-amber-500/20 bg-amber-500/5 p-3 text-[11px] text-amber-200">
        <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
        <p>
          Defensive analytics are illustrative — live numbers populate once
          the DefensivePriority data pipeline is in production.
        </p>
      </div>
    </div>
  );
}
