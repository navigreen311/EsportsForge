'use client';

import { useState } from 'react';
import { Opponent, DossierTab } from '@/types/opponent';
import {
  Swords,
  AlertTriangle,
  BarChart3,
  Brain,
  Shield,
  Zap,
  Target,
  Clock,
  Star,
  FileText,
  Crosshair,
  History,
  Eye,
} from 'lucide-react';
import TendencyChart from './TendencyChart';
import PlayFrequencyChart from './PlayFrequencyChart';
import EncounterHistory from './EncounterHistory';
import PredictionEngine from './PredictionEngine';
import BehavioralSignalFeed from './BehavioralSignalFeed';
import WinRateTrend from './WinRateTrend';
import DossierDepthIndicator from './DossierDepthIndicator';
import { ThreatLevelBadge } from './ThreatLevelBadge';
import RecencyDecayWarning from './RecencyDecayWarning';
import PrepNowButton from './PrepNowButton';

interface DossierViewProps {
  opponent: Opponent;
}

const severityColors: Record<string, string> = {
  low: 'bg-dark-700 text-dark-300',
  medium: 'bg-yellow-900/40 text-yellow-400',
  high: 'bg-orange-900/40 text-orange-400',
  critical: 'bg-red-900/40 text-red-400',
};

const frequencyDots: Record<string, number> = {
  rare: 1,
  occasional: 2,
  frequent: 3,
};

const signalIcons: Record<string, React.ReactNode> = {
  timeout: <Clock className="w-4 h-4" />,
  'pace-change': <Zap className="w-4 h-4" />,
  audible: <Brain className="w-4 h-4" />,
  'hot-route': <Target className="w-4 h-4" />,
  'formation-shift': <Shield className="w-4 h-4" />,
};

const tabs: { key: DossierTab; label: string; icon: React.ReactNode }[] = [
  { key: 'overview', label: 'Overview', icon: <Eye className="w-4 h-4" /> },
  { key: 'tendencies', label: 'Tendencies', icon: <BarChart3 className="w-4 h-4" /> },
  { key: 'plays', label: 'Plays', icon: <FileText className="w-4 h-4" /> },
  { key: 'killsheet', label: 'Kill Sheet', icon: <Crosshair className="w-4 h-4" /> },
  { key: 'history', label: 'History', icon: <History className="w-4 h-4" /> },
];

function getRivalDepth(encounterCount: number): string | null {
  if (encounterCount >= 8) return 'Nemesis';
  if (encounterCount >= 5) return 'Arch-Rival';
  if (encounterCount >= 2) return 'Rival';
  return null;
}

export default function DossierView({ opponent }: DossierViewProps) {
  const [activeTab, setActiveTab] = useState<DossierTab>('overview');
  const rivalDepth = opponent.isRival ? getRivalDepth(opponent.encounterCount) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-6 rounded-xl border border-dark-700 bg-dark-900/50">
        <div className="w-16 h-16 rounded-full bg-dark-800 border-2 border-dark-600 flex items-center justify-center text-2xl font-bold text-dark-200">
          {opponent.gamertag.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-dark-50">{opponent.gamertag}</h1>
            {opponent.isRival && (
              <span className="flex items-center gap-1 px-2 py-1 text-xs font-bold bg-red-500/20 text-red-400 border border-red-800/50 rounded">
                <Swords className="w-3.5 h-3.5" />
                RIVAL
              </span>
            )}
            {rivalDepth && opponent.encounterCount >= 2 && (
              <span className="flex items-center gap-1 px-2 py-1 text-xs font-bold bg-yellow-500/15 text-yellow-400 border border-yellow-800/40 rounded">
                <Star className="w-3.5 h-3.5 fill-yellow-400" />
                {rivalDepth}
              </span>
            )}
            <ThreatLevelBadge opponent={opponent} />
          </div>
          <div className="flex items-center gap-3 mt-1">
            <p className="text-dark-400">
              {opponent.archetype} &middot; {opponent.encounterCount} encounters &middot;{' '}
              {opponent.record.wins}W-{opponent.record.losses}L &middot; Last seen{' '}
              {opponent.lastSeen}
              <RecencyDecayWarning lastSeen={opponent.lastSeen} />
            </p>
          </div>
          <DossierDepthIndicator opponent={opponent} />
        </div>
        <div className="text-right">
          <WinRateTrend winRate={opponent.winRate} opponentId={opponent.id} />
          <p className="text-xs text-dark-500 mt-1">Win Rate vs</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-lg bg-dark-900/50 border border-dark-700 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium transition-all whitespace-nowrap ${
              activeTab === tab.key
                ? 'bg-dark-700 text-dark-50 shadow-sm'
                : 'text-dark-400 hover:text-dark-200 hover:bg-dark-800/50'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Archetype Description */}
          <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
            <h2 className="text-lg font-bold text-dark-100 mb-3">Archetype Profile</h2>
            <p className="text-sm text-dark-300 leading-relaxed">
              {opponent.archetypeDetail.description}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <h3 className="text-sm font-medium text-forge-400 mb-2">Strengths</h3>
                <ul className="space-y-1">
                  {opponent.archetypeDetail.strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-dark-300">
                      <span className="text-forge-400 mt-0.5">+</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-medium text-red-400 mb-2">Weaknesses</h3>
                <ul className="space-y-1">
                  {opponent.archetypeDetail.weaknesses.map((w, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-dark-300">
                      <span className="text-red-400 mt-0.5">-</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Weakness Map */}
          <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
            <h2 className="text-lg font-bold text-dark-100 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
              Weakness Map
            </h2>
            <div className="space-y-2">
              {opponent.weaknesses.map((w, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-lg bg-dark-800/50 border border-dark-700"
                >
                  <span
                    className={`flex-shrink-0 px-2 py-0.5 text-[10px] font-bold uppercase rounded ${severityColors[w.severity]}`}
                  >
                    {w.severity}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-dark-100">{w.area}</p>
                    <p className="text-xs text-dark-400 mt-0.5">{w.description}</p>
                    {w.exploitPlay && (
                      <p className="text-xs text-forge-400 mt-1">
                        Exploit: {w.exploitPlay}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Prediction Engine */}
          <PredictionEngine opponentId={opponent.id} gamesAnalyzed={opponent.encounterCount} />

          {/* Enhanced Behavioral Signals */}
          <BehavioralSignalFeed signals={opponent.behavioralSignals} />
        </div>
      )}

      {activeTab === 'tendencies' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
              <h2 className="text-lg font-bold text-dark-100 mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                Offense Tendencies
              </h2>
              <TendencyChart
                tendencies={opponent.tendencies}
                category="offense"
                label="Offensive Plays"
                barColor="#3b82f6"
              />
            </div>
            <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
              <h2 className="text-lg font-bold text-dark-100 mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-red-400" />
                Defense Tendencies
              </h2>
              <TendencyChart
                tendencies={opponent.tendencies}
                category="defense"
                label="Defensive Plays"
                barColor="#ef4444"
              />
            </div>
          </div>

          {/* Formation Frequency */}
          <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
            <h2 className="text-lg font-bold text-dark-100 mb-4">Formation Frequency</h2>
            <div className="space-y-2.5">
              {opponent.formationFrequencies.map((f) => (
                <div key={f.formation} className="flex items-center gap-3">
                  <span className="text-sm text-dark-300 w-36 truncate" title={f.formation}>
                    {f.formation}
                  </span>
                  <div className="flex-1 bg-dark-800 rounded-full h-2.5">
                    <div
                      className="h-2.5 rounded-full bg-purple-500 transition-all duration-500"
                      style={{ width: `${f.percentage}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-dark-400 w-10 text-right">
                    {f.percentage}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Blitz Frequency */}
          <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
            <h2 className="text-lg font-bold text-dark-100 mb-3">Blitz Frequency</h2>
            <div className="flex items-center gap-4">
              <div className="flex-1 bg-dark-800 rounded-full h-4">
                <div
                  className="h-4 rounded-full transition-all duration-500"
                  style={{
                    width: `${opponent.blitzFrequency}%`,
                    backgroundColor:
                      opponent.blitzFrequency >= 60
                        ? '#ef4444'
                        : opponent.blitzFrequency >= 35
                          ? '#eab308'
                          : '#22c55e',
                  }}
                />
              </div>
              <span className="text-lg font-bold font-mono text-dark-100">
                {opponent.blitzFrequency}%
              </span>
            </div>
            <p className="text-xs text-dark-500 mt-2">
              {opponent.blitzFrequency >= 60
                ? 'Very aggressive blitzer. Expect pressure on most passing downs.'
                : opponent.blitzFrequency >= 35
                  ? 'Moderate blitz frequency. Mixes pressure with coverage.'
                  : 'Conservative approach. Relies on coverage over pressure.'}
            </p>
          </div>
        </div>
      )}

      {activeTab === 'plays' && (
        <div className="space-y-6">
          <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
            <h2 className="text-lg font-bold text-dark-100 mb-4">Most Common Plays</h2>
            <PlayFrequencyChart data={opponent.playFrequencies} />
          </div>

          <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
            <h2 className="text-lg font-bold text-dark-100 mb-4">Play Details</h2>
            <div className="space-y-2">
              {opponent.playFrequencies.map((play, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50 border border-dark-700"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-dark-500 w-6">#{i + 1}</span>
                    <span className="text-sm font-medium text-dark-100">{play.playName}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-xs text-dark-500">Used </span>
                      <span className="text-sm font-mono font-bold text-dark-200">
                        {play.count}x
                      </span>
                    </div>
                    <div
                      className={`text-sm font-mono font-bold ${
                        play.successRate >= 60
                          ? 'text-forge-400'
                          : play.successRate >= 45
                            ? 'text-yellow-400'
                            : 'text-red-400'
                      }`}
                    >
                      {play.successRate}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'killsheet' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
            <h2 className="text-lg font-bold text-dark-100 mb-2 flex items-center gap-2">
              <Crosshair className="w-5 h-5 text-forge-400" />
              Kill Sheet
            </h2>
            <p className="text-sm text-dark-400 mb-6">
              Top 5 plays to beat {opponent.gamertag}, ranked by confidence.
            </p>
            <div className="space-y-3">
              {opponent.killSheet.map((play, i) => (
                <div
                  key={play.id}
                  className="p-4 rounded-lg bg-dark-800/50 border border-dark-700 hover:border-dark-600 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span
                        className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                          i === 0
                            ? 'bg-forge-500/20 text-forge-400 border border-forge-800/30'
                            : 'bg-dark-700 text-dark-300 border border-dark-600'
                        }`}
                      >
                        {i + 1}
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-dark-100">{play.playName}</h3>
                        <span className="text-xs text-dark-500">{play.formation}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="text-xs text-dark-500">Confidence</p>
                        <p
                          className={`text-lg font-bold font-mono ${
                            play.confidenceScore >= 85
                              ? 'text-forge-400'
                              : play.confidenceScore >= 70
                                ? 'text-yellow-400'
                                : 'text-dark-300'
                          }`}
                        >
                          {play.confidenceScore}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-dark-500">Success</p>
                        <p className="text-lg font-bold font-mono text-dark-200">
                          {play.successRate}%
                        </p>
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-dark-400 mt-2 pl-11">{play.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-dark-100 flex items-center gap-2">
                <History className="w-5 h-5 text-dark-400" />
                Encounter History
              </h2>
              <span className="text-sm text-dark-500">
                {opponent.record.wins}W - {opponent.record.losses}L
              </span>
            </div>
            <EncounterHistory encounters={opponent.encounters} />
          </div>
        </div>
      )}

      {/* Prep Now */}
      <div className="pt-4">
        <PrepNowButton opponent={opponent} variant="full" />
      </div>
    </div>
  );
}
