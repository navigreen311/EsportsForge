'use client';

import { useState, useEffect, useCallback } from 'react';
import { Save, Loader2, CheckCircle, Info } from 'lucide-react';
import { useSession } from 'next-auth/react';
import InfoTooltip from '@/components/global/InfoTooltip';

const DIRECTNESS_TOOLTIPS: Record<string, string> = {
  'one-answer':
    "ForgeCore tells you exactly what to do, no debate. 'Run PA Crossers.' No alternatives, no explanation unless you ask. Best for tournament play when you need decisions fast.",
  'recommendation':
    "ForgeCore gives you the best play AND a backup. 'Run PA Crossers. If they show Cover 0, audible to Quick Slants.' Gives you flexibility without slowing you down.",
  'full-analysis':
    'ForgeCore explains the why behind every recommendation — defensive read, evidence, confidence %, risk factors, alternative options. Best for learning and offline lab study. Slower in live play.',
};

const FREQUENCY_TOOLTIPS: Record<string, string> = {
  'low':
    'ForgeCore only speaks up for critical moments — 4th down decisions, red zone calls, late-game clutch situations. The rest of the time it stays silent and lets you play.',
  'standard':
    'ForgeCore offers balanced suggestions throughout the game — pre-snap reads, situational adjustments, mid-drive corrections. Recommended default.',
  'high':
    'ForgeCore is proactive coaching — every drive, every red zone trip, every defensive series. Best for skill development. Can feel chatty in tournament play.',
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8001';

function sliderColor(v: number): string {
  if (v <= 3) return 'text-red-400';
  if (v <= 7) return 'text-amber-300';
  return 'text-green-400';
}

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

// --- localStorage Key ---
const STORAGE_KEY = 'esportsforge_identity_engine';

// --- Component ---

export default function IdentityEngine() {
  const { data: session } = useSession();
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

  // Save flow
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [toastState, setToastState] = useState<'hidden' | 'recalibrating' | 'complete'>('hidden');
  const [showToast, setShowToast] = useState(false);

  // Load from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        if (data.offensiveIdentity) setOffensiveIdentity(data.offensiveIdentity);
        if (data.defensivePhilosophy) setDefensivePhilosophy(data.defensivePhilosophy);
        if (data.riskTolerance) setRiskTolerance(data.riskTolerance);
        if (data.fourthDown) setFourthDown(data.fourthDown);
        if (data.aggressionAfterLead) setAggressionAfterLead(data.aggressionAfterLead);
        if (data.pace) setPace(data.pace);
        if (data.comfortZones) setComfortZones(new Set(data.comfortZones));
        if (data.directness) setDirectness(data.directness);
        if (data.frequency) setFrequency(data.frequency);
      }
    } catch {}
  }, []);

  const handleSave = useCallback(() => {
    if (isSaving) return;

    const data = {
      offensiveIdentity,
      defensivePhilosophy,
      riskTolerance,
      fourthDownTendency: fourthDown,
      aggressionAfterLead,
      pace,
      comfortZones: Array.from(comfortZones),
      agentDirectness: directness,
      recFrequency: frequency,
    };

    // Step 1: Button loading
    setIsSaving(true);
    setSaveSuccess(false);

    // Simulate save delay
    setTimeout(() => {
      // Persist to localStorage
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));

      // Step 2: Show recalibrating toast
      setToastState('recalibrating');
      setShowToast(true);

      // Step 3: Dispatch recalibrating signal
      window.dispatchEvent(
        new CustomEvent('playertwin-recalibrating', { detail: { active: true } })
      );

      // Step 5: Fire-and-forget API persist + PlayerTwin recalibrate trigger
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (session?.accessToken) headers.Authorization = `Bearer ${session.accessToken}`;
      fetch(`${API_BASE}/api/v1/identity/save`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      }).catch(() => {});
      fetch(`${API_BASE}/api/v1/player-twin/recalibrate`, {
        method: 'POST',
        headers,
      }).catch(() => {});

      // Button success flash
      setIsSaving(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 500);

      // Step 4: Recalibration complete after 2s
      setTimeout(() => {
        setToastState('complete');
        window.dispatchEvent(
          new CustomEvent('playertwin-recalibrating', { detail: { active: false } })
        );

        // Auto-dismiss toast 3s after completion
        setTimeout(() => {
          setShowToast(false);
          setToastState('hidden');
        }, 3000);
      }, 2000);
    }, 500);
  }, [
    isSaving,
    offensiveIdentity,
    defensivePhilosophy,
    riskTolerance,
    fourthDown,
    aggressionAfterLead,
    pace,
    comfortZones,
    directness,
    frequency,
    session?.accessToken,
  ]);

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
            <span className={`text-sm font-medium ${sliderColor(riskTolerance)}`}>
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
            <span className={`text-sm font-medium ${sliderColor(fourthDown)}`}>
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
            <span className={`text-sm font-medium ${sliderColor(aggressionAfterLead)}`}>
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
              <InfoTooltip
                key={option.id}
                content={DIRECTNESS_TOOLTIPS[option.id]}
                mobileTitle={option.label}
              >
                <button
                  onClick={() => setDirectness(option.id)}
                  className={`relative rounded-lg p-4 text-left border transition-all cursor-help hover:bg-dark-800/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-forge-500/40 ${
                    directness === option.id
                      ? 'border-forge-500 bg-forge-500/5'
                      : 'border-dark-700 bg-dark-800/50 hover:border-dark-500'
                  }`}
                >
                  <Info className="absolute top-2 right-2 h-3 w-3 text-dark-500 hover:text-dark-300 transition-colors" />
                  <p className="text-sm font-bold text-dark-100 pr-4">{option.label}</p>
                  <p className="text-xs text-dark-400 mt-0.5">{option.description}</p>
                </button>
              </InfoTooltip>
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
              <InfoTooltip
                key={option.id}
                content={FREQUENCY_TOOLTIPS[option.id]}
                mobileTitle={option.label}
              >
                <button
                  onClick={() => setFrequency(option.id)}
                  className={`relative rounded-lg p-4 text-left border transition-all cursor-help hover:bg-dark-800/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-forge-500/40 ${
                    frequency === option.id
                      ? 'border-forge-500 bg-forge-500/5'
                      : 'border-dark-700 bg-dark-800/50 hover:border-dark-500'
                  }`}
                >
                  <Info className="absolute top-2 right-2 h-3 w-3 text-dark-500 hover:text-dark-300 transition-colors" />
                  <p className="text-sm font-bold text-dark-100 pr-4">{option.label}</p>
                  <p className="text-xs text-dark-400 mt-0.5">{option.description}</p>
                </button>
              </InfoTooltip>
            ))}
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={`flex items-center gap-2 rounded-lg px-6 py-3 text-sm font-medium text-white transition-all duration-300 ${
            saveSuccess
              ? 'bg-forge-400/20 border border-forge-400/30'
              : 'bg-forge-600 hover:bg-forge-500'
          } ${isSaving ? 'opacity-80 cursor-not-allowed' : ''}`}
        >
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Identity
            </>
          )}
        </button>
      </div>

      {/* Toast Notification */}
      {showToast && (
        <div
          className="fixed top-4 right-4 z-50 rounded-lg border border-forge-400/30 bg-dark-800 p-4 shadow-lg transition-all duration-300"
          style={{
            animation: 'slideInRight 0.3s ease-out',
          }}
        >
          <div className="flex items-center gap-3">
            <CheckCircle className={`h-5 w-5 flex-shrink-0 ${
              toastState === 'complete' ? 'text-green-400' : 'text-forge-400'
            }`} />
            <p className="text-sm font-medium text-white">
              {toastState === 'complete'
                ? 'PlayerTwin updated \u2713'
                : 'Identity saved \u2014 PlayerTwin recalibrating...'}
            </p>
          </div>
        </div>
      )}

      {/* Inline keyframes for toast slide-in */}
      <style>{`
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(100%);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  );
}
