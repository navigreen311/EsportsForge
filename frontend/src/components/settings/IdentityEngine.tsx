'use client';

import { useState } from 'react';

// --- Data Definitions ---

const offensiveStyles = [
  { id: 'explosive', title: 'Explosive', subtitle: 'Spread, deep shots, RPO' },
  { id: 'clock-control', title: 'Clock Control', subtitle: 'Run-heavy, possession' },
  { id: 'balanced', title: 'Balanced', subtitle: 'Multi-dimensional' },
  { id: 'meta-adaptive', title: 'Meta-Adaptive', subtitle: "I run what's broken" },
] as const;

const defensivePhilosophies = [
  { id: 'pressure', title: 'Pressure', subtitle: 'Aggressive pass rush, exotic blitzes' },
  { id: 'coverage-shell', title: 'Coverage Shell', subtitle: 'Lock down passing lanes' },
  { id: 'bend-dont-break', title: "Bend Don't Break", subtitle: 'Prevent big plays, force long drives' },
] as const;

const paceOptions = [
  { id: 'fast', label: 'Fast', description: 'No-huddle, high tempo' },
  { id: 'standard', label: 'Standard', description: 'Mix of tempos' },
  { id: 'deliberate', label: 'Deliberate', description: 'Slow, methodical drives' },
] as const;

const comfortZoneTags = [
  'Run Game',
  'Deep Ball',
  'RPO',
  'Screen Game',
  'Red Zone Specialist',
  'Clutch Closer',
  'Comeback King',
  'Conservative Leader',
] as const;

const directnessOptions = [
  { id: 'one-answer', label: 'Give me one answer', description: 'Just tell me what to do' },
  { id: 'recommendation', label: 'Recommendation + alternative', description: 'Best pick with a backup' },
  { id: 'full-analysis', label: 'Full analysis', description: 'Show me everything' },
] as const;

const frequencyOptions = [
  { id: 'low', label: 'Low', description: 'Only when critical' },
  { id: 'standard', label: 'Standard', description: 'Balanced suggestions' },
  { id: 'high', label: 'High', description: 'Proactive coaching' },
] as const;

// --- Helpers ---

function getRiskLabel(value: number): string {
  if (value <= 3) return 'Conservative';
  if (value <= 6) return 'Calculated';
  return 'Aggressive';
}

function getFourthDownLabel(value: number): string {
  if (value <= 3) return 'Always Kick';
  if (value <= 6) return 'Situational';
  return 'Always Go For It';
}

function getAggressionLabel(value: number): string {
  if (value <= 3) return 'Conservative Hold';
  if (value <= 6) return 'Balanced';
  return 'Keep Attacking';
}

// --- Component ---

export default function IdentityEngine() {
  // Section A
  const [offensiveIdentity, setOffensiveIdentity] = useState<string>('balanced');
  const [defensivePhilosophy, setDefensivePhilosophy] = useState<string>('coverage-shell');

  // Section B
  const [riskTolerance, setRiskTolerance] = useState(5);
  const [fourthDown, setFourthDown] = useState(5);
  const [aggressionAfterLead, setAggressionAfterLead] = useState(5);

  // Section C
  const [pace, setPace] = useState<string>('standard');
  const [comfortZones, setComfortZones] = useState<Set<string>>(new Set());

  // Section D
  const [directness, setDirectness] = useState<string>('recommendation');
  const [frequency, setFrequency] = useState<string>('standard');

  const toggleComfortZone = (tag: string) => {
    setComfortZones((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) {
        next.delete(tag);
      } else {
        next.add(tag);
      }
      return next;
    });
  };

  return (
    <div className="space-y-6">
      {/* Section A: Play Style */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-semibold text-dark-100 mb-4">Play Style</h2>

        {/* Offensive Identity */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Offensive Identity
          </label>
          <div className="grid grid-cols-2 gap-3">
            {offensiveStyles.map((style) => (
              <button
                key={style.id}
                onClick={() => setOffensiveIdentity(style.id)}
                className={`rounded-lg p-4 text-left border transition-all ${
                  offensiveIdentity === style.id
                    ? 'border-forge-500 bg-forge-500/5'
                    : 'border-dark-700 bg-dark-800/50 hover:border-dark-500'
                }`}
              >
                <p className="text-sm font-bold text-dark-100">{style.title}</p>
                <p className="text-xs text-dark-400 mt-0.5">{style.subtitle}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Defensive Philosophy */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Defensive Philosophy
          </label>
          <div className="grid grid-cols-3 gap-3">
            {defensivePhilosophies.map((phil) => (
              <button
                key={phil.id}
                onClick={() => setDefensivePhilosophy(phil.id)}
                className={`rounded-lg p-4 text-left border transition-all ${
                  defensivePhilosophy === phil.id
                    ? 'border-forge-500 bg-forge-500/5'
                    : 'border-dark-700 bg-dark-800/50 hover:border-dark-500'
                }`}
              >
                <p className="text-sm font-bold text-dark-100">{phil.title}</p>
                <p className="text-xs text-dark-400 mt-0.5">{phil.subtitle}</p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Section B: Risk Profile */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-semibold text-dark-100 mb-4">Risk Profile</h2>

        {/* Risk Tolerance */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-dark-300 mb-2">
            Risk Tolerance
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={riskTolerance}
            onChange={(e) => setRiskTolerance(Number(e.target.value))}
            className="w-full accent-forge-500 bg-dark-700"
          />
          <div className="flex items-center justify-between mt-1.5">
            <span className="text-sm font-medium text-forge-400">
              {riskTolerance} &mdash; {getRiskLabel(riskTolerance)}
            </span>
          </div>
          <p className="text-xs text-dark-500 mt-1">
            This affects: 4th down decisions, deep shot frequency, blitz usage
          </p>
        </div>

        {/* 4th Down Tendency */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-dark-300 mb-2">
            4th Down Tendency
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={fourthDown}
            onChange={(e) => setFourthDown(Number(e.target.value))}
            className="w-full accent-forge-500 bg-dark-700"
          />
          <div className="flex items-center justify-between mt-1.5">
            <span className="text-xs text-dark-500">Always Kick</span>
            <span className="text-sm font-medium text-forge-400">
              {fourthDown} &mdash; {getFourthDownLabel(fourthDown)}
            </span>
            <span className="text-xs text-dark-500">Always Go For It</span>
          </div>
        </div>

        {/* Aggression After Lead */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            Aggression After Lead
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={aggressionAfterLead}
            onChange={(e) => setAggressionAfterLead(Number(e.target.value))}
            className="w-full accent-forge-500 bg-dark-700"
          />
          <div className="flex items-center justify-between mt-1.5">
            <span className="text-xs text-dark-500">Conservative Hold</span>
            <span className="text-sm font-medium text-forge-400">
              {aggressionAfterLead} &mdash; {getAggressionLabel(aggressionAfterLead)}
            </span>
            <span className="text-xs text-dark-500">Keep Attacking</span>
          </div>
        </div>
      </div>

      {/* Section C: Pace & Style */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-semibold text-dark-100 mb-4">Pace & Style</h2>

        {/* Preferred Pace */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Preferred Pace
          </label>
          <div className="grid grid-cols-3 gap-3">
            {paceOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => setPace(option.id)}
                className={`rounded-lg p-4 text-left border transition-all ${
                  pace === option.id
                    ? 'border-forge-500 bg-forge-500/5'
                    : 'border-dark-700 bg-dark-800/50 hover:border-dark-500'
                }`}
              >
                <p className="text-sm font-bold text-dark-100">{option.label}</p>
                <p className="text-xs text-dark-400 mt-0.5">{option.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Comfort Zone */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Comfort Zone
          </label>
          <div className="flex flex-wrap gap-2">
            {comfortZoneTags.map((tag) => (
              <button
                key={tag}
                onClick={() => toggleComfortZone(tag)}
                className={`rounded-lg border px-3 py-1.5 text-sm transition-all ${
                  comfortZones.has(tag)
                    ? 'bg-forge-500/20 text-forge-400 border-forge-500/30'
                    : 'bg-dark-800 text-dark-400 border-dark-700'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Section D: Agent Personalization */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-semibold text-dark-100 mb-4">Agent Personalization</h2>

        {/* Directness */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-dark-300 mb-3">
            How direct should ForgeCore be?
          </label>
          <div className="grid grid-cols-3 gap-3">
            {directnessOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => setDirectness(option.id)}
                className={`rounded-lg p-4 text-left border transition-all ${
                  directness === option.id
                    ? 'border-forge-500 bg-forge-500/5'
                    : 'border-dark-700 bg-dark-800/50 hover:border-dark-500'
                }`}
              >
                <p className="text-sm font-bold text-dark-100">{option.label}</p>
                <p className="text-xs text-dark-400 mt-0.5">{option.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Recommendation Frequency */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-3">
            Recommendation frequency
          </label>
          <div className="grid grid-cols-3 gap-3">
            {frequencyOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => setFrequency(option.id)}
                className={`rounded-lg p-4 text-left border transition-all ${
                  frequency === option.id
                    ? 'border-forge-500 bg-forge-500/5'
                    : 'border-dark-700 bg-dark-800/50 hover:border-dark-500'
                }`}
              >
                <p className="text-sm font-bold text-dark-100">{option.label}</p>
                <p className="text-xs text-dark-400 mt-0.5">{option.description}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
