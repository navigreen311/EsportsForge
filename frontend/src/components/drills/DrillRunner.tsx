'use client';

import { useState } from 'react';
import { DrillRecord } from '@/types/analytics';
import {
  Play,
  CheckCircle2,
  SkipForward,
  Flame,
  Target,
  Gauge,
  Sparkles,
  Volume2,
} from 'lucide-react';
import PressureModeToggle, { PressureContext } from '@/components/drills/PressureModeToggle';
import WhyThisDrill from '@/components/drills/WhyThisDrill';
import SimLabLaunchButton from '@/components/drills/SimLabLaunchButton';
import { DrillMasteryDot, DRILL_MASTERY } from '@/components/drills/DrillMasteryDot';
import { useVoiceForge } from '@/hooks/useVoiceForge';

interface DrillRunnerProps {
  drill: DrillRecord;
  onCompleteRep: () => void;
  onSkip: () => void;
  onStart: () => void;
  onEnd: () => void;
  onNext: () => void;
  isActive: boolean;
  successCount: number;
  failCount: number;
}

const difficultyConfig: Record<
  string,
  { color: string; label: string; dots: number }
> = {
  beginner: { color: 'text-green-400', label: 'Beginner', dots: 1 },
  intermediate: { color: 'text-yellow-400', label: 'Intermediate', dots: 2 },
  advanced: { color: 'text-orange-400', label: 'Advanced', dots: 3 },
  elite: { color: 'text-red-400', label: 'Elite', dots: 4 },
};

const masteryLabels: Record<string, string> = {
  mastered: 'Mastered',
  practicing: 'Practicing',
  learning: 'Learning',
  'not-started': 'Not Started',
};

const masteryColors: Record<string, string> = {
  mastered: 'text-forge-400',
  practicing: 'text-amber-400',
  learning: 'text-dark-300',
  'not-started': 'text-dark-500',
};

export default function DrillRunner({
  drill,
  onCompleteRep,
  onSkip,
  onStart,
  onEnd,
  onNext,
  isActive,
  successCount,
  failCount,
}: DrillRunnerProps) {
  const [pressureMode, setPressureMode] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const progress = drill.reps > 0 ? (drill.completedReps / drill.reps) * 100 : 0;
  const diffConfig = difficultyConfig[drill.difficulty];
  const mastery = DRILL_MASTERY[drill.id] ?? 'not-started';
  const { speak, stop, isSpeaking, isAvailable: voiceAvailable } = useVoiceForge();

  const speakDrillStart = () => {
    if (!voiceEnabled) return;
    speak(`Starting ${drill.name}. ${drill.instructions} You have ${drill.reps} reps. Let's go.`, { interruptCurrent: true });
  };
  const speakHalfway = () => {
    if (!voiceEnabled) return;
    speak(`Halfway there. ${Math.floor(drill.reps / 2)} of ${drill.reps} complete. Stay focused.`);
  };
  const speakComplete = () => {
    if (!voiceEnabled) return;
    speak(`Drill complete. ${drill.successRate}% successful. LoopAI has updated your PlayerTwin.`);
  };

  return (
    <div
      className={`rounded-xl border p-6 transition-all duration-300 ${
        isActive
          ? pressureMode
            ? 'border-amber-500/50 bg-gradient-to-b from-amber-950/20 to-dark-900/80 shadow-lg shadow-amber-500/5'
            : 'border-forge-500/50 bg-gradient-to-b from-forge-950/30 to-dark-900/80 shadow-lg shadow-forge-500/5'
          : 'border-dark-700 bg-dark-900/50'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-xl font-bold text-dark-50">{drill.name}</h2>
            {drill.isDynamicCalibration && (
              <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold uppercase bg-purple-500/20 text-purple-400 border border-purple-800/30 rounded">
                <Sparkles className="w-3 h-3" />
                Dynamic Calibration
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1">
            <div className="flex items-center gap-1">
              <Gauge className={`w-4 h-4 ${diffConfig.color}`} />
              <span className={`text-sm font-medium ${diffConfig.color}`}>
                {diffConfig.label}
              </span>
            </div>
            <span className="text-dark-600">|</span>
            <div className="flex items-center gap-1">
              <Flame className="w-4 h-4 text-orange-400" />
              <span className="text-sm text-dark-400">
                IR: <span className="font-mono font-bold text-dark-200">{drill.impactRank}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Success Rate */}
        <div className="text-right">
          <p className="text-2xl font-bold font-mono text-forge-400">{drill.successRate}%</p>
          <p className="text-[10px] text-dark-500 uppercase tracking-wider">Success Rate</p>
        </div>
      </div>

      {/* Mastery / Pressure Mode / Voice row */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-dark-400">
          Mastery: <span className={`font-medium ${masteryColors[mastery]}`}>{masteryLabels[mastery]}</span>
        </span>
        <div className="flex items-center gap-2">
          {voiceAvailable && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (voiceEnabled) {
                    stop();
                    setVoiceEnabled(false);
                  } else {
                    setVoiceEnabled(true);
                  }
                }}
                className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                  voiceEnabled ? 'bg-forge-500/15 text-forge-400' : 'bg-dark-800 text-dark-500 hover:text-dark-300'
                }`}
              >
                <Volume2 className="h-3.5 w-3.5" />
                Voice: {voiceEnabled ? 'ON' : 'OFF'}
              </button>
            </div>
          )}
          <PressureModeToggle enabled={pressureMode} onToggle={() => setPressureMode(!pressureMode)} />
        </div>
      </div>

      {/* Pressure Mode Context */}
      <PressureContext enabled={pressureMode} />

      {/* Instructions */}
      <div className="p-4 rounded-lg bg-dark-800/60 border border-dark-700 mb-4">
        <p className="text-sm text-dark-200 leading-relaxed">{drill.instructions}</p>
      </div>

      {/* 5. Why This Drill */}
      <div className="mb-4">
        <WhyThisDrill drillId={drill.id} />
      </div>

      {/* Progress */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-dark-400">
            Reps: <span className="font-mono text-dark-200">{drill.completedReps}/{drill.reps}</span>
          </span>
          <span className="text-sm font-mono text-dark-400">{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-dark-800 rounded-full h-3">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-forge-600 to-forge-400 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Skill Targets */}
      {drill.skillTargets.length > 0 && (
        <div className="mb-5">
          <h3 className="text-sm font-medium text-dark-300 mb-2 flex items-center gap-1.5">
            <Target className="w-4 h-4" />
            Skill Targets
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {drill.skillTargets.map((target) => (
              <div key={target.name} className="flex items-center gap-2">
                <span className="text-xs text-dark-400 w-24 truncate">{target.name}</span>
                <div className="flex-1 bg-dark-800 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full bg-cyan-500"
                    style={{ width: `${(target.current / target.target) * 100}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-dark-500">
                  {target.current}/{target.target}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        {!isActive ? (
          <>
            <button
              onClick={() => { onStart(); speakDrillStart(); }}
              className="flex items-center gap-2 px-5 py-2.5 bg-forge-500 hover:bg-forge-600 text-dark-950 font-bold rounded-lg transition-colors"
            >
              <Play className="w-4 h-4" />
              Start Drill
            </button>
            {/* 8. SimLab Launch */}
            <SimLabLaunchButton drillId={drill.id} drillName={drill.name} variant="full" />
          </>
        ) : (
          <>
            <button
              onClick={() => {
                onCompleteRep();
                if (drill.completedReps + 1 === Math.floor(drill.reps / 2)) speakHalfway();
                if (drill.completedReps + 1 >= drill.reps) speakComplete();
              }}
              className="flex items-center gap-2 px-5 py-2.5 bg-forge-500 hover:bg-forge-600 text-dark-950 font-bold rounded-lg transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              Complete Rep
            </button>
            <button
              onClick={onSkip}
              className="flex items-center gap-2 px-4 py-2.5 bg-dark-800 hover:bg-dark-700 text-dark-300 font-medium rounded-lg border border-dark-600 transition-colors"
            >
              <SkipForward className="w-4 h-4" />
              Skip
            </button>
          </>
        )}
      </div>
    </div>
  );
}
