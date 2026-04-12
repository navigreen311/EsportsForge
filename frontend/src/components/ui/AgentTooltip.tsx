'use client';
import { useState, type ReactNode } from 'react';

const AGENT_DESCRIPTIONS: Record<string, string> = {
  ImpactRank: 'Ranks your weaknesses by actual win-rate damage',
  PlayerTwin: 'Your digital model — learns your real tendencies',
  LoopAI: 'Learns from every game — self-improving AI',
  ScoutBot: 'Analyzes opponent tendencies from match history',
  GameplanAI: 'Generates personalized gameplans vs. specific opponents',
  DrillBot: 'Creates targeted drills for your exact weaknesses',
  TiltGuard: 'Monitors mental performance and intervenes on tilt',
  ConfidenceAI: 'Scores every recommendation with certainty and risk',
  ForgeCore: 'Master orchestrator — one decisive answer from all agents',
  TransferAI: 'Measures if practice skills transfer to live play',
  MetaBot: 'Tracks what is broken in the current meta',
  FilmAI: 'Analyzes replays automatically via VisionAudioForge',
};

export default function AgentTooltip({ agentName, children }: { agentName: string; children: ReactNode }) {
  const [show, setShow] = useState(false);
  const desc = AGENT_DESCRIPTIONS[agentName] || agentName;
  return (
    <span className="relative inline-block" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {children}
      {show && (
        <span className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg bg-dark-700 border border-dark-600 text-xs text-dark-100 whitespace-nowrap shadow-lg">
          <span className="font-semibold text-forge-400">{agentName}</span>
          <br />
          {desc}
        </span>
      )}
    </span>
  );
}
