'use client';

import { useEffect, useRef, useState } from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { useVoiceForge } from '@/hooks/useVoiceForge';

interface DrillCoachVoiceProps {
  drillName: string;
  completedReps: number;
  totalReps: number;
  isActive: boolean;
  successRate: number;
}

export default function DrillCoachVoice({
  drillName,
  completedReps,
  totalReps,
  isActive,
  successRate,
}: DrillCoachVoiceProps) {
  const { isAvailable, isSpeaking, speak, stop } = useVoiceForge();
  const [muted, setMuted] = useState(false);
  const lastMilestone = useRef(0);
  const hasStarted = useRef(false);

  // Speak drill objective when isActive becomes true
  useEffect(() => {
    if (!isActive) {
      hasStarted.current = false;
      lastMilestone.current = 0;
      return;
    }

    if (hasStarted.current) return;
    hasStarted.current = true;

    if (!muted && isAvailable) {
      speak(`Starting ${drillName}. ${totalReps} reps ahead. Stay focused.`);
    }
  }, [isActive, drillName, totalReps, muted, isAvailable, speak]);

  // Milestone and completion tracking
  useEffect(() => {
    if (!isActive || !isAvailable || muted || completedReps === 0) return;

    // Drill complete
    if (completedReps === totalReps) {
      speak(
        `Drill complete. ${successRate}% success rate. Nice work.`
      );
      return;
    }

    // 5-rep milestones
    const currentMilestone = Math.floor(completedReps / 5) * 5;
    if (currentMilestone > 0 && currentMilestone > lastMilestone.current) {
      lastMilestone.current = currentMilestone;
      speak(
        `${completedReps} of ${totalReps} complete. ${successRate}% success rate.`
      );
    }
  }, [completedReps, totalReps, successRate, isActive, isAvailable, muted, speak]);

  if (!isActive || !isAvailable) return null;

  const handleMuteToggle = () => {
    if (isSpeaking) stop();
    setMuted((prev) => !prev);
  };

  return (
    <div className="fixed bottom-4 right-4 z-30 flex items-center gap-3 rounded-xl border border-dark-700 bg-dark-900/90 px-4 py-3 shadow-lg backdrop-blur-sm">
      {/* Coaching status */}
      <div className="flex flex-col">
        <span className="text-xs font-medium text-forge-400">
          {isSpeaking ? 'Coaching...' : 'Coach Active'}
        </span>
        <span className="text-[10px] text-dark-400">
          {completedReps}/{totalReps} reps
        </span>
      </div>

      {/* Mute toggle */}
      <button
        type="button"
        onClick={handleMuteToggle}
        className="rounded-lg p-1.5 hover:bg-dark-800 transition-colors"
        aria-label={muted ? 'Unmute coach' : 'Mute coach'}
      >
        {muted ? (
          <VolumeX className="h-4 w-4 text-dark-500" />
        ) : (
          <Volume2 className="h-4 w-4 text-forge-400" />
        )}
      </button>
    </div>
  );
}
