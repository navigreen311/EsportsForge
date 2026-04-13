'use client';

import { useState } from 'react';

interface SessionLoopAIDetailsProps {
  sessionId: string;
}

type FollowedStatus = 'Yes' | 'Partially' | 'No';

interface LoopAIData {
  rec: string;
  followed: FollowedStatus;
  outcome: string;
  loopLearned: string;
  tiltStatus: 'Focused' | 'Tilted' | 'Fatigued';
  fatiguePercent: number;
}

const mockData: Record<string, LoopAIData> = {
  s1: {
    rec: 'Switch to zone coverage on 3rd & long',
    followed: 'Yes',
    outcome: 'Won — zone held on 3/4 critical 3rds',
    loopLearned: 'Zone works best 3rd & 7+ — confidence raised from 74% to 82%',
    tiltStatus: 'Focused',
    fatiguePercent: 28,
  },
  s2: {
    rec: 'Stack the box on 3rd & short',
    followed: 'Partially',
    outcome: 'Lost — run defense improved but passing game collapsed',
    loopLearned: 'Run defense threshold adjusted — blitz package needs refinement',
    tiltStatus: 'Fatigued',
    fatiguePercent: 64,
  },
  s3: {
    rec: 'Exploit weak CB2 with corner routes',
    followed: 'Yes',
    outcome: 'Won — corner route scored 3 TDs vs CB2',
    loopLearned: 'Corner Strike added to kill sheet — 88% success rate confirmed',
    tiltStatus: 'Focused',
    fatiguePercent: 22,
  },
  s4: {
    rec: 'Use quick passes to beat pressure',
    followed: 'No',
    outcome: 'Lost — 6 sacks taken, pocket collapsed repeatedly',
    loopLearned: 'Pocket escape patterns recalibrated — quick pass confidence dropped to 41%',
    tiltStatus: 'Tilted',
    fatiguePercent: 89,
  },
  s5: {
    rec: 'Counter draw to punish aggressive rush',
    followed: 'Yes',
    outcome: 'Won — draw play averaged 7.2 YPC in 4th quarter',
    loopLearned: 'Draw play confidence raised from 64% to 78% vs aggressive fronts',
    tiltStatus: 'Focused',
    fatiguePercent: 35,
  },
};

const tiltDotColor: Record<string, string> = {
  Focused: 'bg-green-400',
  Tilted: 'bg-red-400',
  Fatigued: 'bg-amber-400',
};

const tiltTextColor: Record<string, string> = {
  Focused: 'text-green-400',
  Tilted: 'text-red-400',
  Fatigued: 'text-amber-400',
};

function fatigueColor(pct: number): string {
  if (pct <= 40) return 'text-green-400';
  if (pct <= 70) return 'text-amber-400';
  return 'text-red-400';
}

export default function SessionLoopAIDetails({ sessionId }: SessionLoopAIDetailsProps) {
  const data = mockData[sessionId];
  const [followed, setFollowed] = useState<FollowedStatus | null>(data?.followed ?? null);

  if (!data) {
    return (
      <div className="text-sm text-dark-400">
        No LoopAI data available for this session.
      </div>
    );
  }

  const options: FollowedStatus[] = ['Yes', 'Partially', 'No'];

  const activeStyles: Record<FollowedStatus, string> = {
    Yes: 'bg-green-600 text-white',
    Partially: 'bg-amber-600 text-white',
    No: 'bg-red-600 text-white',
  };

  return (
    <div className="rounded-lg border border-dark-700 bg-dark-900/40 p-4 space-y-3">
      {/* RECOMMENDED */}
      <div className="flex gap-3">
        <span className="text-[10px] uppercase text-dark-500 font-semibold w-32 shrink-0 pt-0.5 tracking-wider">
          Recommended
        </span>
        <span className="text-sm text-dark-200">{data.rec}</span>
      </div>

      {/* FOLLOWED — toggle buttons */}
      <div className="flex gap-3 items-center">
        <span className="text-[10px] uppercase text-dark-500 font-semibold w-32 shrink-0 tracking-wider">
          Followed
        </span>
        <div className="flex gap-1.5">
          {options.map((opt) => (
            <button
              key={opt}
              onClick={(e) => {
                e.stopPropagation();
                setFollowed(opt);
              }}
              className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                followed === opt
                  ? activeStyles[opt]
                  : 'bg-dark-700 text-dark-400 hover:text-dark-200'
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* OUTCOME */}
      <div className="flex gap-3">
        <span className="text-[10px] uppercase text-dark-500 font-semibold w-32 shrink-0 pt-0.5 tracking-wider">
          Outcome
        </span>
        <span className="text-sm text-dark-200">{data.outcome}</span>
      </div>

      {/* LOOPAI LEARNED */}
      <div className="flex gap-3">
        <span className="text-[10px] uppercase text-dark-500 font-semibold w-32 shrink-0 pt-0.5 tracking-wider">
          LoopAI Learned
        </span>
        <span className="inline-block rounded-md bg-purple-500/10 px-2 py-0.5 text-xs text-purple-300">
          {data.loopLearned}
        </span>
      </div>

      {/* TILTGUARD + FATIGUE — side by side */}
      <div className="flex gap-3 items-center">
        <span className="text-[10px] uppercase text-dark-500 font-semibold w-32 shrink-0 tracking-wider">
          TiltGuard
        </span>
        <span className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${tiltDotColor[data.tiltStatus]}`} />
          <span className={`text-sm font-medium ${tiltTextColor[data.tiltStatus]}`}>
            {data.tiltStatus}
          </span>
        </span>
        <span className="text-dark-600 mx-3">|</span>
        <span className="text-[10px] uppercase text-dark-500 font-semibold tracking-wider">
          Fatigue
        </span>
        <span className={`text-sm font-medium ${fatigueColor(data.fatiguePercent)}`}>
          {data.fatiguePercent <= 40 ? 'Low' : data.fatiguePercent <= 70 ? 'Medium' : 'High'} ({data.fatiguePercent}%)
        </span>
      </div>
    </div>
  );
}
