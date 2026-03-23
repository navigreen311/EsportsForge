'use client';

interface SessionLoopAIDetailsProps {
  sessionId: string;
}

interface LoopAIData {
  rec: string;
  followed: 'Yes' | 'No' | 'Partially';
  loopUpdate: string;
  tiltStatus: 'Focused' | 'Tilted' | 'Fatigued';
  fatigue: 'Low' | 'Medium' | 'High';
}

const mockData: Record<string, LoopAIData> = {
  s1: {
    rec: 'Switch to Cover 3 Sky vs spread',
    followed: 'Yes',
    loopUpdate: 'Boosted Cover 3 confidence to 91%',
    tiltStatus: 'Focused',
    fatigue: 'Low',
  },
  s2: {
    rec: 'Stack the box on 3rd & short',
    followed: 'Partially',
    loopUpdate: 'Run defense threshold adjusted',
    tiltStatus: 'Fatigued',
    fatigue: 'Medium',
  },
  s3: {
    rec: 'Exploit weak CB2 with corner routes',
    followed: 'Yes',
    loopUpdate: 'Corner Strike added to kill sheet',
    tiltStatus: 'Focused',
    fatigue: 'Low',
  },
  s4: {
    rec: 'Use quick passes to beat pressure',
    followed: 'No',
    loopUpdate: 'Pocket escape patterns recalibrated',
    tiltStatus: 'Tilted',
    fatigue: 'High',
  },
  s5: {
    rec: 'Counter draw to punish aggressive rush',
    followed: 'Yes',
    loopUpdate: 'Draw play confidence raised to 78%',
    tiltStatus: 'Focused',
    fatigue: 'Low',
  },
};

const followedBadgeClasses: Record<string, string> = {
  Yes: 'bg-forge-500/20 text-forge-400',
  No: 'bg-red-500/20 text-red-400',
  Partially: 'bg-amber-500/20 text-amber-400',
};

const tiltBadgeClasses: Record<string, string> = {
  Focused: 'bg-forge-500/20 text-forge-400',
  Tilted: 'bg-red-500/20 text-red-400',
  Fatigued: 'bg-amber-500/20 text-amber-400',
};

const fatigueBadgeClasses: Record<string, string> = {
  Low: 'text-forge-400',
  Medium: 'text-amber-400',
  High: 'text-red-400',
};

export default function SessionLoopAIDetails({ sessionId }: SessionLoopAIDetailsProps) {
  const data = mockData[sessionId];

  if (!data) {
    return (
      <tr>
        <td colSpan={7} className="px-4 py-3 text-sm text-dark-400">
          No LoopAI data available for this session.
        </td>
      </tr>
    );
  }

  return (
    <tr>
      <td colSpan={7} className="px-4 py-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 rounded-lg border border-dark-700 bg-dark-900/40 p-4">
          {/* Recommendation */}
          <div>
            <span className="block text-[10px] uppercase text-dark-500 mb-1">
              Recommendation
            </span>
            <span className="text-sm text-dark-200">{data.rec}</span>
          </div>

          {/* Followed */}
          <div>
            <span className="block text-[10px] uppercase text-dark-500 mb-1">
              Followed
            </span>
            <span
              className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${followedBadgeClasses[data.followed]}`}
            >
              {data.followed}
            </span>
          </div>

          {/* LoopAI Update */}
          <div>
            <span className="block text-[10px] uppercase text-dark-500 mb-1">
              LoopAI Update
            </span>
            <span className="inline-block rounded-md bg-purple-500/10 px-2 py-0.5 text-xs text-purple-300">
              {data.loopUpdate}
            </span>
          </div>

          {/* TiltGuard Status */}
          <div>
            <span className="block text-[10px] uppercase text-dark-500 mb-1">
              TiltGuard Status
            </span>
            <span
              className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${tiltBadgeClasses[data.tiltStatus]}`}
            >
              {data.tiltStatus}
            </span>
          </div>

          {/* Fatigue Level */}
          <div>
            <span className="block text-[10px] uppercase text-dark-500 mb-1">
              Fatigue Level
            </span>
            <span className={`text-sm font-medium ${fatigueBadgeClasses[data.fatigue]}`}>
              {data.fatigue}
            </span>
          </div>
        </div>
      </td>
    </tr>
  );
}
