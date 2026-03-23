'use client';

import { useState } from 'react';

export interface RadarDimension {
  dimension: string;
  value: number;
  fullMark: number;
}

export interface IdentityTrait {
  name: string;
  value: number;
  min: number;
  max: number;
  lowLabel: string;
  highLabel: string;
}

export interface ExecutionCeilingSkill {
  name: string;
  normal: number;
  pressure: number;
}

export interface BenchmarkEntry {
  skill: string;
  player: number;
  top5Percent: number;
}

export interface TransferRateEntry {
  context: string;
  rate: number;
  trend: 'up' | 'down' | 'stable';
}

export interface InputProfileData {
  controllerType: string;
  inputDelay: number;
  mechanicalLeakage: { name: string; severity: 'low' | 'medium' | 'high' }[];
}

export interface ImprovementMetric {
  name: string;
  data: { week: string; value: number }[];
}

export interface PlayerProfile {
  name: string;
  title: string;
  tier: string;
  memberSince: string;
  gamesPlayed: number;
  overallRating: number;
  radar: RadarDimension[];
  identity: IdentityTrait[];
  executionCeiling: ExecutionCeilingSkill[];
  benchmarks: BenchmarkEntry[];
  transferRates: TransferRateEntry[];
  inputProfile: InputProfileData;
  improvementVelocity: ImprovementMetric[];
}

const mockProfile: PlayerProfile = {
  name: 'ShadowForge',
  title: 'Adaptive Strategist',
  tier: 'Diamond',
  memberSince: 'Jan 2025',
  gamesPlayed: 342,
  overallRating: 78,
  radar: [
    { dimension: 'Read Speed', value: 72, fullMark: 100 },
    { dimension: 'Execution', value: 68, fullMark: 100 },
    { dimension: 'Clutch', value: 61, fullMark: 100 },
    { dimension: 'Anti-Meta', value: 55, fullMark: 100 },
    { dimension: 'Mental', value: 74, fullMark: 100 },
    { dimension: 'Game Knowledge', value: 82, fullMark: 100 },
  ],
  identity: [
    {
      name: 'Risk Tolerance',
      value: 65,
      min: 0,
      max: 100,
      lowLabel: 'Conservative',
      highLabel: 'Aggressive',
    },
    {
      name: 'Aggression',
      value: 72,
      min: 0,
      max: 100,
      lowLabel: 'Passive',
      highLabel: 'Hyper-Aggressive',
    },
    {
      name: 'Pace',
      value: 58,
      min: 0,
      max: 100,
      lowLabel: 'Methodical',
      highLabel: 'Up-Tempo',
    },
    {
      name: 'Play Style',
      value: 45,
      min: 0,
      max: 100,
      lowLabel: 'Run-Heavy',
      highLabel: 'Pass-Heavy',
    },
  ],
  executionCeiling: [
    { name: 'Pre-Snap Reads', normal: 82, pressure: 64 },
    { name: 'Route Timing', normal: 76, pressure: 58 },
    { name: 'Pocket Movement', normal: 71, pressure: 52 },
    { name: 'Play Calling', normal: 85, pressure: 72 },
    { name: 'Adjustments', normal: 68, pressure: 45 },
    { name: 'Clock Mgmt', normal: 79, pressure: 61 },
  ],
  benchmarks: [
    { skill: 'Read Speed', player: 72, top5Percent: 92 },
    { skill: 'Execution', player: 68, top5Percent: 89 },
    { skill: 'Clutch', player: 61, top5Percent: 85 },
    { skill: 'Anti-Meta', player: 55, top5Percent: 88 },
    { skill: 'Mental', player: 74, top5Percent: 91 },
    { skill: 'Game Knowledge', player: 82, top5Percent: 95 },
  ],
  transferRates: [
    { context: 'Lab', rate: 85, trend: 'up' },
    { context: 'Ranked', rate: 62, trend: 'stable' },
    { context: 'Tournament', rate: 48, trend: 'up' },
  ],
  inputProfile: {
    controllerType: 'Xbox Elite Series 2',
    inputDelay: 12,
    mechanicalLeakage: [
      { name: 'Late audible inputs', severity: 'medium' },
      { name: 'Inconsistent snap timing', severity: 'low' },
      { name: 'Hot route misfires under pressure', severity: 'high' },
    ],
  },
  improvementVelocity: [
    {
      name: 'Read Speed',
      data: [
        { week: 'W1', value: 58 },
        { week: 'W2', value: 61 },
        { week: 'W3', value: 63 },
        { week: 'W4', value: 66 },
        { week: 'W5', value: 68 },
        { week: 'W6', value: 70 },
        { week: 'W7', value: 72 },
        { week: 'W8', value: 72 },
      ],
    },
    {
      name: 'Execution',
      data: [
        { week: 'W1', value: 55 },
        { week: 'W2', value: 57 },
        { week: 'W3', value: 60 },
        { week: 'W4', value: 62 },
        { week: 'W5', value: 64 },
        { week: 'W6', value: 65 },
        { week: 'W7', value: 67 },
        { week: 'W8', value: 68 },
      ],
    },
    {
      name: 'Clutch',
      data: [
        { week: 'W1', value: 42 },
        { week: 'W2', value: 45 },
        { week: 'W3', value: 48 },
        { week: 'W4', value: 52 },
        { week: 'W5', value: 55 },
        { week: 'W6', value: 57 },
        { week: 'W7', value: 59 },
        { week: 'W8', value: 61 },
      ],
    },
    {
      name: 'Anti-Meta',
      data: [
        { week: 'W1', value: 35 },
        { week: 'W2', value: 38 },
        { week: 'W3', value: 40 },
        { week: 'W4', value: 42 },
        { week: 'W5', value: 46 },
        { week: 'W6', value: 49 },
        { week: 'W7', value: 52 },
        { week: 'W8', value: 55 },
      ],
    },
  ],
};

export function useProfile() {
  const [profile] = useState<PlayerProfile>(mockProfile);

  const tierColors: Record<string, string> = {
    Bronze: 'text-orange-600 bg-orange-500/10 border-orange-800/30',
    Silver: 'text-gray-300 bg-gray-500/10 border-gray-600/30',
    Gold: 'text-yellow-400 bg-yellow-500/10 border-yellow-800/30',
    Platinum: 'text-cyan-300 bg-cyan-500/10 border-cyan-800/30',
    Diamond: 'text-purple-400 bg-purple-500/10 border-purple-800/30',
    Champion: 'text-red-400 bg-red-500/10 border-red-800/30',
  };

  const tierColor = tierColors[profile.tier] ?? tierColors.Bronze;

  return {
    profile,
    tierColor,
  };
}
