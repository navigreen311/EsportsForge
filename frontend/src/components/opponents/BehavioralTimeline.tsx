'use client';

import { Clock, AlertTriangle, TrendingDown, Zap } from 'lucide-react';

interface TimelineEvent {
  time: string;
  description: string;
  type: 'aggression' | 'abandon' | 'tilt' | 'adjustment';
}

interface BehavioralTimelineProps {
  opponentId: string;
}

const MOCK_TIMELINES: Record<string, TimelineEvent[]> = {
  'opp-1': [
    { time: 'Q1 — 12:00', description: 'Opens conservative, runs on 1st down 80% of time', type: 'adjustment' },
    { time: 'Q2 — 8:30', description: 'Switched aggressive after going down 7', type: 'aggression' },
    { time: 'Q3 — 5:00', description: 'Abandons run game in 2nd half when trailing', type: 'abandon' },
    { time: 'Q4 — 2:00', description: 'Panic-calls timeouts, tilts after 2 failed drives', type: 'tilt' },
  ],
  'opp-2': [
    { time: 'Q1 — 10:00', description: 'Heavy play-action early, testing deep coverage', type: 'adjustment' },
    { time: 'Q2 — 4:00', description: 'Switches to max-protect when pressure works', type: 'adjustment' },
    { time: 'Q3 — 7:00', description: 'Goes ultra-aggressive if down 2+ scores', type: 'aggression' },
  ],
  'opp-3': [
    { time: 'Q1 — 8:00', description: 'Always scripts first 5 plays, same every game', type: 'adjustment' },
    { time: 'Q2 — 2:00', description: 'Abandons zone when trailing at half', type: 'abandon' },
    { time: 'Q4 — 4:00', description: 'Tilts visibly after turnover — forces throws', type: 'tilt' },
  ],
  'opp-4': [
    { time: 'Q1 — 14:00', description: 'Balanced attack, mixes run/pass effectively', type: 'adjustment' },
    { time: 'Q2 — 6:00', description: 'Increases blitz frequency when ahead', type: 'aggression' },
    { time: 'Q3 — 3:00', description: 'Abandons run after falling behind 14+', type: 'abandon' },
    { time: 'Q4 — 1:00', description: 'Clock management breaks down under pressure', type: 'tilt' },
  ],
  'opp-5': [
    { time: 'Q1 — 10:00', description: 'Relies on same 3 plays early', type: 'adjustment' },
    { time: 'Q3 — 8:00', description: 'No adjustments at halftime — exploitable patterns', type: 'abandon' },
  ],
  'opp-6': [
    { time: 'Q1 — 12:00', description: 'Attacks with screen game on early downs', type: 'adjustment' },
    { time: 'Q2 — 5:00', description: 'Switches to prevent defense with any lead', type: 'adjustment' },
    { time: 'Q4 — 3:00', description: 'Aggressive on 4th down when desperate', type: 'aggression' },
  ],
};

const typeConfig: Record<TimelineEvent['type'], { icon: typeof Clock; color: string; dotColor: string }> = {
  aggression: { icon: Zap, color: 'text-red-400', dotColor: 'bg-red-400' },
  abandon: { icon: TrendingDown, color: 'text-amber-400', dotColor: 'bg-amber-400' },
  tilt: { icon: AlertTriangle, color: 'text-orange-400', dotColor: 'bg-orange-400' },
  adjustment: { icon: Clock, color: 'text-blue-400', dotColor: 'bg-blue-400' },
};

/**
 * Timeline of behavioral signals during a game.
 * Shows when the opponent changes strategy, tilts, or abandons schemes.
 */
export default function BehavioralTimeline({ opponentId }: BehavioralTimelineProps) {
  const events = MOCK_TIMELINES[opponentId] ?? [];

  if (events.length === 0) return null;

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center gap-3 mb-4">
        <Clock className="h-5 w-5 text-purple-400" />
        <div>
          <h2 className="text-lg font-semibold text-dark-50">Behavioral Timeline</h2>
          <p className="text-sm text-dark-400">In-game behavioral patterns and shifts</p>
        </div>
      </div>

      <div className="relative pl-6">
        {/* Vertical line */}
        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-dark-700" />

        <div className="space-y-4">
          {events.map((event, i) => {
            const config = typeConfig[event.type];
            const Icon = config.icon;

            return (
              <div key={i} className="relative flex items-start gap-4">
                {/* Dot on timeline */}
                <div
                  className={`absolute -left-6 top-1.5 h-3 w-3 rounded-full border-2 border-dark-900 ${config.dotColor}`}
                />

                {/* Content */}
                <div className="flex-1 rounded-lg bg-dark-800/50 border border-dark-700 p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className={`h-3.5 w-3.5 ${config.color}`} />
                    <span className="text-xs font-mono text-dark-400">{event.time}</span>
                    <span className={`text-[10px] uppercase font-bold ${config.color}`}>
                      {event.type}
                    </span>
                  </div>
                  <p className="text-sm text-dark-200">{event.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
