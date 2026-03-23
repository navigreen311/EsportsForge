'use client';

import { useState, useCallback } from 'react';
import { DrillRecord } from '@/types/analytics';

export interface DrillSession {
  isActive: boolean;
  currentDrillIndex: number;
  timer: number;
  isTimerRunning: boolean;
  sessionComplete: boolean;
  completedDrills: DrillRecord[];
}

const mockDrills: DrillRecord[] = [
  {
    id: 'drill-1',
    name: 'Pre-Snap Read Mastery',
    instructions:
      'Identify the defensive formation and predict the blitz within 3 seconds. Focus on linebacker alignment and safety rotation. Call out the hot route before the play clock hits 10.',
    reps: 10,
    completedReps: 0,
    successRate: 0,
    impactRank: 9.2,
    difficulty: 'advanced',
    skillTargets: [
      { name: 'Read Speed', current: 62, target: 85 },
      { name: 'Game Knowledge', current: 71, target: 90 },
    ],
    isDynamicCalibration: true,
  },
  {
    id: 'drill-2',
    name: 'Clutch Drive Simulator',
    instructions:
      'Execute a 2-minute drill scenario down by 4 points. Must score a touchdown with no timeouts remaining. Focus on sideline throws and clock awareness.',
    reps: 5,
    completedReps: 0,
    successRate: 0,
    impactRank: 8.7,
    difficulty: 'elite',
    skillTargets: [
      { name: 'Clutch', current: 58, target: 80 },
      { name: 'Execution', current: 65, target: 82 },
    ],
    isDynamicCalibration: true,
  },
  {
    id: 'drill-3',
    name: 'Anti-Meta Coverage Beater',
    instructions:
      'Face the top 3 meta defensive schemes and find the soft spots. Run route combos that exploit Cover 3, Cover 2 Man, and Tampa 2 weaknesses. 3 successful completions per scheme required.',
    reps: 9,
    completedReps: 0,
    successRate: 0,
    impactRank: 7.5,
    difficulty: 'advanced',
    skillTargets: [
      { name: 'Anti-Meta', current: 45, target: 70 },
      { name: 'Game Knowledge', current: 71, target: 90 },
    ],
    isDynamicCalibration: false,
  },
  {
    id: 'drill-4',
    name: 'Pocket Pressure Response',
    instructions:
      'Practice escaping the pocket under pressure. Identify the rush lane, step up or roll out, and deliver an accurate throw to the check-down or scramble for positive yards.',
    reps: 8,
    completedReps: 0,
    successRate: 0,
    impactRank: 6.8,
    difficulty: 'intermediate',
    skillTargets: [
      { name: 'Execution', current: 65, target: 82 },
      { name: 'Mental', current: 60, target: 75 },
    ],
    isDynamicCalibration: false,
  },
  {
    id: 'drill-5',
    name: 'Red Zone Efficiency Lab',
    instructions:
      'Score from inside the 20-yard line using a variety of play types. Mix pass concepts with run plays. Goal: 70%+ touchdown conversion rate across all reps.',
    reps: 7,
    completedReps: 0,
    successRate: 0,
    impactRank: 6.1,
    difficulty: 'intermediate',
    skillTargets: [
      { name: 'Execution', current: 65, target: 82 },
      { name: 'Read Speed', current: 62, target: 85 },
    ],
    isDynamicCalibration: false,
  },
];

export interface DrillSkillProgress {
  name: string;
  current: number;
  target: number;
  baseline: number;
}

const initialSkillProgress: DrillSkillProgress[] = [
  { name: 'Read Speed', current: 62, target: 85, baseline: 55 },
  { name: 'Execution', current: 65, target: 82, baseline: 58 },
  { name: 'Clutch', current: 58, target: 80, baseline: 50 },
  { name: 'Anti-Meta', current: 45, target: 70, baseline: 38 },
  { name: 'Mental', current: 60, target: 75, baseline: 52 },
  { name: 'Game Knowledge', current: 71, target: 90, baseline: 64 },
];

export function useDrills() {
  const [drills, setDrills] = useState<DrillRecord[]>(mockDrills);
  const [session, setSession] = useState<DrillSession>({
    isActive: false,
    currentDrillIndex: 0,
    timer: 0,
    isTimerRunning: false,
    sessionComplete: false,
    completedDrills: [],
  });
  const [skillProgress, setSkillProgress] =
    useState<DrillSkillProgress[]>(initialSkillProgress);
  const [successCount, setSuccessCount] = useState(0);
  const [failCount, setFailCount] = useState(0);

  const currentDrill = drills[session.currentDrillIndex] ?? null;
  const queue = drills.slice(session.currentDrillIndex + 1);

  const startDrill = useCallback(() => {
    setSession((prev) => ({
      ...prev,
      isActive: true,
      isTimerRunning: true,
    }));
  }, []);

  const completeRep = useCallback(
    (success: boolean) => {
      if (!currentDrill) return;

      if (success) {
        setSuccessCount((c) => c + 1);
      } else {
        setFailCount((c) => c + 1);
      }

      setDrills((prev) =>
        prev.map((d) => {
          if (d.id !== currentDrill.id) return d;
          const newCompleted = d.completedReps + 1;
          const totalAttempts = successCount + failCount + 1;
          const totalSuccess = success ? successCount + 1 : successCount;
          return {
            ...d,
            completedReps: newCompleted,
            successRate: Math.round((totalSuccess / totalAttempts) * 100),
          };
        })
      );

      // Update skill progress slightly on success
      if (success) {
        setSkillProgress((prev) =>
          prev.map((sp) => ({
            ...sp,
            current: Math.min(sp.target, sp.current + Math.random() * 1.5),
          }))
        );
      }
    },
    [currentDrill, successCount, failCount]
  );

  const skipDrill = useCallback(() => {
    if (session.currentDrillIndex < drills.length - 1) {
      setSession((prev) => ({
        ...prev,
        currentDrillIndex: prev.currentDrillIndex + 1,
        completedDrills: currentDrill
          ? [...prev.completedDrills, currentDrill]
          : prev.completedDrills,
      }));
      setSuccessCount(0);
      setFailCount(0);
    }
  }, [session.currentDrillIndex, drills.length, currentDrill]);

  const endSession = useCallback(() => {
    setSession((prev) => ({
      ...prev,
      isActive: false,
      isTimerRunning: false,
      sessionComplete: true,
      completedDrills: currentDrill
        ? [...prev.completedDrills, currentDrill]
        : prev.completedDrills,
    }));
  }, [currentDrill]);

  const nextDrill = useCallback(() => {
    if (session.currentDrillIndex < drills.length - 1) {
      setSession((prev) => ({
        ...prev,
        currentDrillIndex: prev.currentDrillIndex + 1,
        completedDrills: currentDrill
          ? [...prev.completedDrills, currentDrill]
          : prev.completedDrills,
      }));
      setSuccessCount(0);
      setFailCount(0);
    } else {
      endSession();
    }
  }, [session.currentDrillIndex, drills.length, currentDrill, endSession]);

  const resetSession = useCallback(() => {
    setDrills(mockDrills);
    setSession({
      isActive: false,
      currentDrillIndex: 0,
      timer: 0,
      isTimerRunning: false,
      sessionComplete: false,
      completedDrills: [],
    });
    setSkillProgress(initialSkillProgress);
    setSuccessCount(0);
    setFailCount(0);
  }, []);

  const totalReps = drills.reduce((sum, d) => sum + d.completedReps, 0);
  const totalTargetReps = drills.reduce((sum, d) => sum + d.reps, 0);
  const overallSuccessRate =
    totalReps > 0
      ? Math.round(
          (drills.reduce(
            (sum, d) => sum + (d.completedReps * d.successRate) / 100,
            0
          ) /
            totalReps) *
            100
        )
      : 0;

  return {
    drills,
    currentDrill,
    queue,
    session,
    skillProgress,
    successCount,
    failCount,
    totalReps,
    totalTargetReps,
    overallSuccessRate,
    startDrill,
    completeRep,
    skipDrill,
    nextDrill,
    endSession,
    resetSession,
  };
}
