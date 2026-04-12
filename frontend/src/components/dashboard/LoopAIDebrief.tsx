/**
 * LoopAI Debrief — "Last Session Debrief" with bullet points showing:
 * what was recommended, what happened, outcome, what LoopAI learned.
 */

'use client';

import { RefreshCw, Lightbulb, PlayCircle, Trophy, Brain } from 'lucide-react';
import { Card } from '@/components/shared/Card';

interface DebriefBullet {
  icon: React.ReactNode;
  label: string;
  text: string;
  color: string;
}

const mockDebrief: DebriefBullet[] = [
  {
    icon: <Lightbulb className="h-3.5 w-3.5" />,
    label: 'Recommended',
    text: 'Switch to zone coverage on 3rd-and-long vs spread formations',
    color: 'text-purple-400',
  },
  {
    icon: <PlayCircle className="h-3.5 w-3.5" />,
    label: 'What happened',
    text: 'You ran zone 4/6 times; man coverage on 2 blitz situations',
    color: 'text-sky-400',
  },
  {
    icon: <Trophy className="h-3.5 w-3.5" />,
    label: 'Outcome',
    text: 'Won 3 of 4 zone snaps; opponent completed 0/3 deep vs your zone shell',
    color: 'text-forge-400',
  },
  {
    icon: <Brain className="h-3.5 w-3.5" />,
    label: 'LoopAI learned',
    text: 'Zone works best in 3rd-and-7+ — increasing confidence from 74% to 82%',
    color: 'text-amber-400',
  },
];

export default function LoopAIDebrief() {
  return (
    <Card padding="md">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10">
            <RefreshCw className="h-4 w-4 text-purple-400" />
          </div>
          <div>
            <span className="text-sm font-bold text-dark-100">Last Session Debrief</span>
            <p className="text-[10px] text-dark-500">LoopAI feedback cycle</p>
          </div>
        </div>

        {/* Bullet points */}
        <div className="space-y-2.5">
          {mockDebrief.map((bullet, idx) => (
            <div key={idx} className="flex items-start gap-2.5">
              <div className={`mt-0.5 ${bullet.color}`}>
                {bullet.icon}
              </div>
              <div className="min-w-0 flex-1">
                <p className={`text-[10px] font-semibold uppercase tracking-wider ${bullet.color}`}>
                  {bullet.label}
                </p>
                <p className="text-xs text-dark-300 leading-relaxed">
                  {bullet.text}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
