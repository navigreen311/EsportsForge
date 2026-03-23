'use client';

import { Gamepad2, ChevronDown, Sparkles, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { useGameplan } from '@/hooks/useGameplan';
import GameplanList from '@/components/gameplan/GameplanList';
import PlayDetail from '@/components/gameplan/PlayDetail';
import MetaStatusBar from '@/components/gameplan/MetaStatusBar';
import ExportControls from '@/components/gameplan/ExportControls';
import type { PackageTab } from '@/types/gameplan';

const tabs: { key: PackageTab; label: string; count?: (gp: ReturnType<typeof useGameplan>['gameplan']) => number }[] = [
  { key: 'all', label: 'All Plays', count: (gp) => gp.plays.length },
  { key: 'kill-sheet', label: 'Kill Sheet', count: (gp) => gp.killSheet.length },
  { key: 'red-zone', label: 'Red Zone', count: (gp) => gp.redZonePackage.length },
  { key: 'anti-blitz', label: 'Anti-Blitz', count: (gp) => gp.antiBlitzPackage.length },
  { key: '2-min-drill', label: '2-Min Drill', count: (gp) => gp.twoMinDrillPackage.length },
];

export default function GameplanPage() {
  const {
    opponents,
    selectedOpponentId,
    setSelectedOpponentId,
    opponent,
    gameplan,
    activeTab,
    setActiveTab,
    filteredPlays,
    selectedPlay,
    selectPlay,
    isGenerating,
    generateGameplan,
  } = useGameplan();

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-dark-50">
            <Gamepad2 className="h-8 w-8 text-forge-400" />
            Gameplan
          </h1>
          <p className="mt-1 text-dark-400">
            AI-generated strategy vs{' '}
            <span className="font-medium text-dark-200">{opponent.name}</span>
          </p>
        </div>

        {/* Opponent Selector + Generate */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <select
              value={selectedOpponentId}
              onChange={(e) => setSelectedOpponentId(e.target.value)}
              className="appearance-none rounded-lg border border-dark-700 bg-dark-800 py-2 pl-3 pr-9 text-sm font-medium text-dark-200 transition-colors hover:border-dark-500 focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500/30"
            >
              {opponents.map((opp) => (
                <option key={opp.id} value={opp.id}>
                  {opp.name}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
          </div>

          <button
            onClick={generateGameplan}
            disabled={isGenerating}
            className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-sm font-semibold text-dark-950 transition-colors hover:bg-forge-400 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {isGenerating ? 'Generating...' : 'Generate Gameplan'}
          </button>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 overflow-x-auto rounded-lg border border-dark-700/50 bg-dark-900/60 p-1">
        {tabs.map((tab) => {
          const count = tab.count?.(gameplan);
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={clsx(
                'flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-dark-700 text-dark-50 shadow-sm'
                  : 'text-dark-400 hover:text-dark-200'
              )}
            >
              {tab.label}
              {count !== undefined && (
                <span
                  className={clsx(
                    'rounded-full px-1.5 py-0.5 text-[10px] font-bold',
                    isActive
                      ? 'bg-forge-500/20 text-forge-400'
                      : 'bg-dark-800 text-dark-500'
                  )}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left: Play List */}
        <div className="lg:col-span-5 xl:col-span-4">
          <GameplanList
            plays={filteredPlays}
            selectedPlayId={selectedPlay?.id ?? null}
            onSelectPlay={selectPlay}
          />
        </div>

        {/* Right: Detail Panel */}
        <div className="lg:col-span-7 xl:col-span-8">
          <PlayDetail play={selectedPlay} />
        </div>
      </div>

      {/* Export Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <ExportControls gameplanName={gameplan.name} />
      </div>

      {/* Meta Status Bar */}
      <MetaStatusBar metaStatus={gameplan.metaStatus} />
    </div>
  );
}
