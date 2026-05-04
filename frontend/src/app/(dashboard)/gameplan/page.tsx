'use client';

import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Eye, Gamepad2, ChevronDown, Sparkles, Loader2, Volume2 } from 'lucide-react';
import { clsx } from 'clsx';
import { useGameplan } from '@/hooks/useGameplan';
import { useUIStore } from '@/lib/store';
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
import {
  KillSheetSummary,
  PackageHealthCard,
  ScriptViewPanel,
  TwoMinDrillTable,
} from '@/components/gameplan/StructuredPackagePanel';
import SimulateModal from '@/components/gameplan/SimulateModal';
import ScoutOpponentModal from '@/components/gameplan/ScoutOpponentModal';
import ShareGameplanModal from '@/components/gameplan/ShareGameplanModal';
import { GameplanSessionBar } from '@/components/session/GameplanSessionBar';
import { ArsenalTabPanel } from '@/components/arsenal/ArsenalTabPanel';
import type { PackageTab, Play } from '@/types/gameplan';

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
  const {
    opponents,
    opponentsLoaded,
    selectedOpponentId,
    setSelectedOpponentId,
    opponent,
    gameplan,
    setActiveTab,
    filteredPlays,
    selectedPlay,
    selectPlay,
    isGenerating,
    generateError,
    loadingMessage,
    generateGameplan,
  } = useGameplan();

  const [viewTab, setViewTab] = useState<ViewTab>('all');
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [simulatePlay, setSimulatePlay] = useState<Play | null>(null);
  const [scoutOpen, setScoutOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const titleId = useUIStore((s) => s.selectedTitle);
  const visiblePlays = activeFilter
    ? filteredPlays.filter((p) =>
        (p.tags ?? p.conceptTags).some((t) => t.toLowerCase().includes(activeFilter)),
      )
    : filteredPlays;
  const session = useSessionStore((s) => s.session);
  const isSessionActive = !!session;
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
          <div className="relative">
            <select
              value={selectedOpponentId}
              onChange={(e) => setSelectedOpponentId(e.target.value)}
              disabled={opponents.length === 0}
              className="appearance-none rounded-lg border border-dark-700 bg-dark-800 py-2 pl-3 pr-9 text-sm font-medium text-dark-200 transition-colors hover:border-dark-500 focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500/30 disabled:opacity-50"
            >
              {opponents.length === 0 && <option value="">No opponents scouted</option>}
              {opponents.map((opp) => (
                <option key={opp.id} value={opp.id}>
                  {opp.gamertag}{opp.archetype ? ` · ${opp.archetype}` : ''}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
          </div>

          {selectedOpponentId && (
            <button
              onClick={() => setScoutOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-purple-500/40 bg-purple-500/10 px-3 py-2 text-xs font-medium text-purple-300 hover:bg-purple-500/20"
              title="Run ScoutBot to populate this opponent's tendency dossier"
            >
              <Eye className="h-3.5 w-3.5" />
              Scout
            </button>
          )}

          <button
            onClick={() => generateGameplan({ bypassCache: !!gameplan.generatedId })}
            disabled={isGenerating}
            title={opponents.length === 0 ? 'Generates a general plan — scout an opponent for tendency-specific picks' : ''}
            className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-sm font-semibold text-dark-950 transition-colors hover:bg-forge-400 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {isGenerating
              ? 'GameplanAI is building your plan…'
              : gameplan.generatedId
                ? 'Regenerate Gameplan'
                : 'Generate Gameplan'}
          </button>
        </div>
      </div>

      {/* Loading / error / source banner */}
      {isGenerating && (
        <div className="flex items-center gap-3 rounded-lg border border-forge-500/30 bg-forge-500/10 px-4 py-3 text-sm text-forge-300">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>{loadingMessage}</span>
        </div>
      )}
      {generateError && !isGenerating && (
        <div className="flex items-center justify-between rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <span>{generateError}</span>
          <button
            type="button"
            onClick={() => generateGameplan({ bypassCache: true })}
            className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-200 hover:bg-red-500/20"
          >
            Retry
          </button>
        </div>
      )}
      {gameplan.source && !isGenerating && (
        <p className="text-[11px] text-dark-500">
          {gameplan.source === 'mock' && 'GameplanAI ran in mock mode — set ANTHROPIC_API_KEY for opponent-specific picks. '}
          {gameplan.source === 'cache' && 'Loaded from cache (1h TTL). Regenerate to bypass. '}
          {gameplan.source === 'claude' && 'Live GameplanAI output. '}
          Patch {gameplan.metaVersion ?? 'unknown'} · {gameplan.plays.length} plays.
        </p>
      )}
      {opponentsLoaded && opponents.length === 0 && !gameplan.generatedId && !isGenerating && (
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6 text-center">
          <p className="text-sm font-semibold text-dark-200">No opponents scouted yet</p>
          <p className="mt-1 text-xs text-dark-400">
            You can still generate a general plan now, or scout an opponent for tendency-specific picks.
          </p>
        </div>
      )}

      {/* Opponent Tendency Header — pills, archetype, win rate (now clickable) */}
      <OpponentTendencyHeader
        opponentName={opponent.name}
        summary={gameplan.opponentSummary}
        archetype={opponent.archetype}
        activeFilter={activeFilter}
        onTagFilter={setActiveFilter}
      />
      {activeFilter && (
        <p className="text-[11px] text-forge-400">
          Showing {visiblePlays.length} of {filteredPlays.length} plays that beat {activeFilter}
        </p>
      )}

      {/* 7. Opponent Tendency Panel */}
      <OpponentTendencyPanel opponentName={opponent.name} />

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
          {gameplan.scriptView && gameplan.scriptView.length > 0 && (
            <ScriptViewPanel entries={gameplan.scriptView} />
          )}
          <First15ScriptView opponentName={opponent.name} />
          <FirstFifteenScript />
        </div>
      ) : (
        <>
          {/* Structured AI summary on relevant tabs */}
          {viewTab === 'kill-sheet' && gameplan.killSheetStructured && (
            <KillSheetSummary entries={gameplan.killSheetStructured} />
          )}
          {viewTab === 'anti-blitz' && (
            <>
              <PackageHealthCard
                title="Anti-Blitz"
                health={gameplan.antiBlitzPackageHealth}
              />
              <AntiBlitzHealthBanner plays={gameplan.antiBlitzPackage} />
            </>
          )}
          {viewTab === 'red-zone' && (
            <PackageHealthCard
              title="Red Zone"
              health={gameplan.redZonePackageHealth}
            />
          )}
          {viewTab === '2-min-drill' && gameplan.twoMinDrill && (
            <TwoMinDrillTable entries={gameplan.twoMinDrill} />
          )}

          {/* Two-Column Layout */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
            <div className="lg:col-span-5 xl:col-span-4">
              <GameplanList
                plays={visiblePlays}
                selectedPlayId={selectedPlay?.id ?? null}
                onSelectPlay={selectPlay}
              />
            </div>
            <div className="lg:col-span-7 xl:col-span-8">
              <PlayDetail
                play={selectedPlay}
                opponentName={opponent.name}
                onSimulate={(p) => setSimulatePlay(p)}
              />
            </div>
          </div>
        </>
      )}

      {/* Export Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <ExportControls
          gameplanName={gameplan.name}
          gameplan={gameplan}
          onShare={() => setShareOpen(true)}
        />
      </div>

      {/* Meta Status Bar */}
      <MetaStatusBar metaStatus={gameplan.metaStatus} />

      {/* Modals */}
      <SimulateModal
        open={simulatePlay !== null}
        play={simulatePlay}
        opponentTendency={gameplan.opponentSummary?.topCoverage ?? 'their top coverage'}
        opponentArchetype={opponent.archetype}
        titleId={titleId}
        onClose={() => setSimulatePlay(null)}
      />
      <ScoutOpponentModal
        open={scoutOpen}
        opponentId={selectedOpponentId}
        opponentName={opponent.name}
        onClose={() => setScoutOpen(false)}
        onScouted={() => generateGameplan({ bypassCache: true })}
      />
      <ShareGameplanModal
        open={shareOpen}
        gameplanId={gameplan.generatedId ?? null}
        onClose={() => setShareOpen(false)}
      />
    </div>
  );
}
