'use client';

import { Flame, Calendar, Trophy, Target } from 'lucide-react';

/** Mock streak and session data. */
const MOCK_DATA = {
  currentStreak: 7,
  bestStreak: 14,
  totalSessions: 42,
  thisWeekSessions: 5,
  weeklyGoal: 6,
  lastDrilledDaysAgo: 0,
  weekDays: [true, true, true, false, true, true, false] as boolean[],
};

/**
 * Drill streak widget displayed at the top of the drills page.
 * Shows current streak, weekly progress, and best streak.
 */
export default function DrillStreakWidget() {
  const {
    currentStreak,
    bestStreak,
    totalSessions,
    thisWeekSessions,
    weeklyGoal,
    weekDays,
  } = MOCK_DATA;

  const weeklyProgress = Math.round((thisWeekSessions / weeklyGoal) * 100);
  const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-4">
      <div className="flex flex-wrap items-center gap-6">
        {/* Current Streak */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-orange-500/10 border border-orange-800/30">
            <Flame className="h-5 w-5 text-orange-400" />
          </div>
          <div>
            <p className="text-xs text-dark-500 uppercase tracking-wider">Streak</p>
            <p className="text-xl font-bold font-mono text-dark-50">
              {currentStreak}
              <span className="text-sm text-dark-400 font-normal ml-1">days</span>
            </p>
          </div>
        </div>

        {/* Week Calendar */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-dark-800 border border-dark-700">
            <Calendar className="h-5 w-5 text-dark-400" />
          </div>
          <div>
            <p className="text-xs text-dark-500 uppercase tracking-wider mb-1">This Week</p>
            <div className="flex items-center gap-1">
              {dayLabels.map((label, i) => (
                <div key={i} className="flex flex-col items-center gap-0.5">
                  <span className="text-[9px] text-dark-500">{label}</span>
                  <div
                    className={`h-3 w-3 rounded-sm ${
                      weekDays[i] ? 'bg-forge-400' : 'bg-dark-700'
                    }`}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Weekly Goal Progress */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-dark-800 border border-dark-700">
            <Target className="h-5 w-5 text-forge-400" />
          </div>
          <div>
            <p className="text-xs text-dark-500 uppercase tracking-wider">Weekly Goal</p>
            <div className="flex items-center gap-2 mt-0.5">
              <div className="w-16 h-1.5 rounded-full bg-dark-700">
                <div
                  className="h-1.5 rounded-full bg-forge-400 transition-all"
                  style={{ width: `${Math.min(100, weeklyProgress)}%` }}
                />
              </div>
              <span className="text-xs font-mono text-dark-300">
                {thisWeekSessions}/{weeklyGoal}
              </span>
            </div>
          </div>
        </div>

        {/* Best Streak */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-yellow-500/10 border border-yellow-800/30">
            <Trophy className="h-5 w-5 text-yellow-400" />
          </div>
          <div>
            <p className="text-xs text-dark-500 uppercase tracking-wider">Best Streak</p>
            <p className="text-sm font-bold font-mono text-dark-200">
              {bestStreak} days
            </p>
          </div>
        </div>

        {/* Total Sessions */}
        <div className="ml-auto text-right hidden md:block">
          <p className="text-xs text-dark-500 uppercase tracking-wider">Total Sessions</p>
          <p className="text-lg font-bold font-mono text-dark-200">{totalSessions}</p>
        </div>
      </div>
    </div>
  );
}
