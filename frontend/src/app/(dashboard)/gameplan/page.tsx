'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Gamepad2,
  ChevronDown,
  Sparkles,
  Loader2,
  Volume2,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useGameplan } from '@/hooks/useGameplan';
import { useSessionStore } from '@/lib/sessionStore';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import GameplanList from '@/components/gameplan/GameplanList';
import PlayDetail from '@/components/gameplan/PlayDetail';
import MetaStatusBar from '@/components/gameplan/MetaStatusBar';
import ExportControls from '@/components/gameplan/ExportControls';
import OpponentTendencyPanel from '@/components/gameplan/OpponentTendencyPanel';
import First15ScriptView from '@/components/gameplan/First15ScriptView';
import { AntiBlitzHealthBadge, AntiBlitzHealthBanner } from '@/components/gameplan/AntiBlitzHealth';
import OpponentTendencyHeader from '@/components/gameplan/OpponentTendencyHeader';
import FirstFifteenScript from '@/components/gameplan/FirstFifteenScript';
import { GameplanSessionBar } from '@/components/session/GameplanSessionBar';
import { ArsenalTabPanel } from '@/components/arsenal/ArsenalTabPanel';
import DefensiveGameplanView from '@/components/gameplan/DefensiveGameplanView';
import {
  SideToggle,
  DEFENSE_LABEL_BY_TITLE,
} from '@/components/shared/SideToggle';
import { useActiveArsenalTitle, type WeaponSide } from '@/hooks/useArsenal';
import type { PackageTab, Play } from '@/types/gameplan';
import { WatchingPageHint } from '@/components/global/WatchingPageHint';

type ViewTab = PackageTab | 'script' | 'arsenal';

const tabs: { key: ViewTab; label: string; count?: (gp: ReturnType<typeof useGameplan>['gameplan']) => number }[] = [
  { key: 'all', label: 'All Plays', count: (gp) => gp.plays.length },
  { key: 'kill-sheet', label: 'Kill Sheet', count: (gp) => gp.killSheet.length },
  { key: 'red-zone', label: 'Red Zone', count: (gp) => gp.redZonePackage.length },
  { key: 'anti-blitz', label: 'Anti-Blitz', count: (gp) => gp.antiBlitzPackage.length },
  { key: '2-min-drill', label: '2-Min Drill', count: (gp) => gp.twoMinDrillPackage.length },
  { key: 'script', label: 'Script View' },
  { key: 'arsenal', label: '⚡ Arsenal' },
];

export default function GameplanPage() {
  // useSearchParams() requires a Suspense boundary at build time. The body
  // of the page lives in GameplanPageBody so we can wrap it cleanly.
  return (
    <Suspense>
      <GameplanPageBody />
    </Suspense>
  );
}

function GameplanPageBody() {
  const {
    opponents,
    selectedOpponentId,
    setSelectedOpponentId,
    opponent,
    gameplan,
    setActiveTab,
    filteredPlays,
    selectedPlay,
    selectPlay,
    isGenerating,
    generateGameplan,
  } = useGameplan();

  const [viewTab, setViewTab] = useState<ViewTab>('all');
  const [side, setSide] = useState<WeaponSide>('offense');
  const [tendencyFilter, setTendencyFilter] = useState<string | null>(null);
  const session = useSessionStore((s) => s.session);
  const isSessionActive = !!session;
  const titleId = useActiveArsenalTitle();
  const searchParams = useSearchParams();
  const requestedTab = searchParams?.get('tab') as ViewTab | null;
  const autoSwitchedRef = useRef(false);

  // Honour ?tab= deep-links (e.g. from CompetitionModeCard "Open Kill Sheet").
  useEffect(() => {
    if (requestedTab && tabs.some((t) => t.key === requestedTab)) {
      setViewTab(requestedTab);
      if (requestedTab !== 'script' && requestedTab !== 'arsenal')
        setActiveTab(requestedTab);
    }
  }, [requestedTab, setActiveTab]);

  // Auto-switch to Kill Sheet on first visit during an active session.
  useEffect(() => {
    if (autoSwitchedRef.current) return;
    if (!isSessionActive) return;
    if (requestedTab) return; // explicit tab takes precedence
    autoSwitchedRef.current = true;
    setViewTab('kill-sheet');
    setActiveTab('kill-sheet');
  }, [isSessionActive, requestedTab, setActiveTab]);

  const handleTabChange = (key: ViewTab) => {
    setViewTab(key);
    if (key !== 'script' && key !== 'arsenal') {
      setActiveTab(key as PackageTab);
    }
  };

  // FIX 5: tendency-pill filter — narrows the play list when the player
  // clicks a tendency pill in the OpponentTendencyPanel.
  const matchesTendency = (play: Play, pill: string): boolean => {
    const tags = play.conceptTags ?? [];
    if (pill === 'cover-2') return tags.includes('zone-beater');
    if (pill === 'blitzes')
      return tags.some((t) => t === 'quick-pass' || t === 'screen');
    if (pill === 'run-first-3rd')
      return tags.some((t) => t === 'run' || t === 'draw' || t === 'rpo');
    return true;
  };

  const tendencyFilteredPlays = tendencyFilter
    ? filteredPlays.filter((p) => matchesTendency(p, tendencyFilter))
    : filteredPlays;

  const handleFilterByTendency = (pill: string) => {
    setTendencyFilter((prev) => (prev === pill ? null : pill));
  };

  const tendencyDescriptions: Record<string, string> = {
    'cover-2': 'beat Cover 2',
    blitzes: 'beat the blitz',
    'run-first-3rd': 'attack run-first 3rd downs',
  };

  // FIX 4: stale-gameplan staleness check — compute days since metaStatus
  // was last updated. Warning surfaces above the export row when older than
  // 14 days; stronger amber message when older than 30 days.
  const daysSinceUpdate = (() => {
    const iso = gameplan.metaStatus?.lastUpdated;
    if (!iso) return 0;
    const ms = Date.now() - new Date(iso).getTime();
    return Math.max(0, Math.floor(ms / (1000 * 60 * 60 * 24)));
  })();
  const isVeryStale = daysSinceUpdate >= 30;
  const isStale = daysSinceUpdate >= 14;

  const openKillSheet = () => handleTabChange('kill-sheet');

  const readKillSheet = (plays: Play[]) => {
    if (plays.length === 0) {
      VoiceForgeService.speak('No kill-shot plays loaded yet.', { interruptCurrent: true });
      return;
    }
    const intro = `Reading your top ${plays.length} kill-shot ${plays.length === 1 ? 'play' : 'plays'} vs ${opponent.name}.`;
    VoiceForgeService.speak(intro, { interruptCurrent: true });
    plays.forEach((p, i) => {
      const beats = p.beats ? ` Beats ${p.beats}.` : '';
      VoiceForgeService.speak(
        `Play ${i + 1}: ${p.name}.${beats} ${p.description}`,
        { interruptCurrent: false }
      );
    });
  };

  return (
    <div className="space-y-5">
      {/* Session context bar (only during active session) */}
      <GameplanSessionBar onOpenKillSheet={openKillSheet} />

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
          <WatchingPageHint
            pageName="Gameplan"
            onHint="Watching Gameplan — pre-snap reads will highlight matching plays"
            offHint="Enable Watching for live play highlights"
          />
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

      {/* Side toggle — switches between offensive gameplan and defensive plan */}
      <div className="flex items-center justify-between gap-3">
        <SideToggle
          side={side}
          onChange={setSide}
          defenseLabel={DEFENSE_LABEL_BY_TITLE[titleId] ?? 'Defense'}
        />
        <p className="text-[11px] text-dark-500">
          {side === 'defense'
            ? 'Counter their offense — schemes, blitz packages, traps'
            : 'Attack their defense — kill plays, scripts, anti-blitz'}
        </p>
      </div>

      {/* Opponent Tendency Header — pills, archetype, win rate */}
      <OpponentTendencyHeader opponentName={opponent.name} />

      {/* 7. Opponent Tendency Panel */}
      <OpponentTendencyPanel
        opponentName={opponent.name}
        onFilterByTendency={handleFilterByTendency}
      />

      {side === 'defense' && (
        <DefensiveGameplanView
          opponentId={selectedOpponentId}
          opponentName={opponent.name}
        />
      )}

      {side === 'offense' && (
        <>
      {/* Tab Bar with 8. Anti-Blitz Health Badge */}
      <div className="flex gap-1 overflow-x-auto rounded-lg border border-dark-700/50 bg-dark-900/60 p-1">
        {tabs.map((tab) => {
          const count = tab.count?.(gameplan);
          const isActive = viewTab === tab.key;
          const isKillSheetActive = tab.key === 'kill-sheet' && isSessionActive;
          return (
            <button
              key={tab.key}
              onClick={() => handleTabChange(tab.key)}
              className={clsx(
                'flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-dark-700 text-dark-50 shadow-sm'
                  : 'text-dark-400 hover:text-dark-200',
                isKillSheetActive && !isActive && 'ring-1 ring-forge-500/40'
              )}
            >
              {isKillSheetActive && (
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-forge-500" />
                </span>
              )}
              {tab.label}
              {isKillSheetActive && (
                <span className="ml-0.5 text-[9px] font-bold uppercase tracking-wider text-forge-400">
                  Active
                </span>
              )}
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
              {/* Anti-Blitz health indicator */}
              {tab.key === 'anti-blitz' && (
                <AntiBlitzHealthBadge plays={gameplan.antiBlitzPackage} />
              )}
            </button>
          );
        })}
      </div>

      {/* Read Kill Sheet voice prompt — only on Kill Sheet during active session */}
      {viewTab === 'kill-sheet' && isSessionActive && (
        <div className="flex items-center justify-between rounded-lg border border-forge-500/30 bg-forge-500/5 px-4 py-3">
          <div>
            <p className="text-sm font-bold text-forge-300">Hear it before the match</p>
            <p className="text-[11px] text-dark-400">
              VoiceForge will read all {gameplan.killSheet.length} kill-shot plays aloud.
            </p>
          </div>
          <button
            type="button"
            onClick={() => readKillSheet(gameplan.killSheet)}
            className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950 transition-colors hover:bg-forge-400"
          >
            <Volume2 className="h-4 w-4" />
            Read My Kill Shot Plays
          </button>
        </div>
      )}

      {/* Content: Script View or Two-Column Layout */}
      {viewTab === 'arsenal' ? (
        <ArsenalTabPanel />
      ) : viewTab === 'script' ? (
        <div className="space-y-5">
          <First15ScriptView opponentName={opponent.name} />
          <FirstFifteenScript />
        </div>
      ) : (
        <>
          {/* Anti-Blitz Health Banner */}
          {viewTab === 'anti-blitz' && (
            <AntiBlitzHealthBanner plays={gameplan.antiBlitzPackage} />
          )}

          {/* Tendency-filter banner (FIX 5) */}
          {tendencyFilter && (
            <div className="flex items-center justify-between rounded-lg border border-forge-500/30 bg-forge-500/10 px-3 py-2">
              <p className="text-xs text-forge-300">
                Showing{' '}
                <span className="font-semibold">
                  {tendencyFilteredPlays.length}
                </span>{' '}
                plays that{' '}
                {tendencyDescriptions[tendencyFilter] ?? tendencyFilter}
              </p>
              <button
                type="button"
                onClick={() => setTendencyFilter(null)}
                className="rounded-md border border-forge-500/30 bg-forge-500/10 px-2 py-1 text-[11px] font-medium text-forge-300 transition-colors hover:bg-forge-500/20"
              >
                × clear
              </button>
            </div>
          )}

          {/* Two-Column Layout */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
            {/* Left: Play List */}
            <div className="lg:col-span-5 xl:col-span-4">
              <GameplanList
                plays={tendencyFilteredPlays}
                selectedPlayId={selectedPlay?.id ?? null}
                onSelectPlay={selectPlay}
              />
            </div>

            {/* Right: Detail Panel */}
            <div className="lg:col-span-7 xl:col-span-8">
              <PlayDetail play={selectedPlay} opponentName={opponent.name} />
            </div>
          </div>
        </>
      )}

      {/* Stale-gameplan warning (FIX 4) */}
      {isStale && (
        <div
          className={clsx(
            'flex flex-col gap-3 rounded-lg border px-4 py-3 sm:flex-row sm:items-center sm:justify-between',
            isVeryStale
              ? 'border-amber-500/40 bg-amber-500/10'
              : 'border-yellow-500/30 bg-yellow-500/10'
          )}
        >
          <div className="flex items-start gap-2">
            <AlertTriangle
              className={clsx(
                'mt-0.5 h-4 w-4 flex-shrink-0',
                isVeryStale ? 'text-amber-400' : 'text-yellow-400'
              )}
            />
            <p
              className={clsx(
                'text-sm',
                isVeryStale ? 'text-amber-200' : 'text-yellow-200/90'
              )}
            >
              {isVeryStale
                ? `This gameplan is ${daysSinceUpdate} days old. The meta may have changed since Patch ${gameplan.metaStatus.patchVersion}.`
                : `Updated ${daysSinceUpdate}d ago — meta may have shifted since.`}
            </p>
          </div>
          <button
            type="button"
            onClick={generateGameplan}
            disabled={isGenerating}
            className={clsx(
              'inline-flex items-center gap-1.5 self-start rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60 sm:self-auto',
              isVeryStale
                ? 'border-amber-500/40 bg-amber-500/15 text-amber-300 hover:bg-amber-500/25'
                : 'border-yellow-500/40 bg-yellow-500/15 text-yellow-300 hover:bg-yellow-500/25'
            )}
          >
            {isGenerating ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RotateCcw className="h-3.5 w-3.5" />
            )}
            Regenerate
          </button>
        </div>
      )}

      {/* Export Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <ExportControls gameplan={gameplan} opponent={opponent} />
      </div>

      {/* Meta Status Bar */}
      <MetaStatusBar metaStatus={gameplan.metaStatus} />
        </>
      )}
    </div>
  );
}
