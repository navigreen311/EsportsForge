/**
 * Onboarding wizard — 7-step flow for new users.
 */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { clsx } from "clsx";

const TITLES = [
  "Madden 26",
  "CFB 26",
  "NBA 2K26",
  "EA FC 26",
  "MLB 26",
  "Warzone",
  "Fortnite",
  "UFC 5",
  "PGA 2K25",
  "Undisputed",
  "Video Poker",
] as const;

const OFFENSIVE_STYLES = [
  { id: "explosive", label: "Explosive", desc: "Speed kills. Vertical threats and big plays." },
  { id: "clock-control", label: "Clock Control", desc: "Grind the clock. Dominate possession." },
  { id: "balanced", label: "Balanced", desc: "Mix run and pass. Keep defenses guessing." },
  { id: "meta-adaptive", label: "Meta-Adaptive", desc: "Whatever wins. Adapt to the current meta." },
] as const;

const DEFENSIVE_STYLES = [
  { id: "pressure", label: "Pressure", desc: "Blitz-heavy. Force quick decisions." },
  { id: "coverage-shell", label: "Coverage Shell", desc: "Lock down the field. Take away reads." },
  { id: "bend-dont-break", label: "Bend Don't Break", desc: "Limit big plays. Force long drives." },
] as const;

const INPUT_TYPES = [
  { id: "controller", label: "Controller", icon: "🎮" },
  { id: "keyboard-mouse", label: "Keyboard & Mouse", icon: "⌨️" },
  { id: "fight-stick", label: "Fight Stick", icon: "🕹️" },
] as const;

const TOUR_PANELS = [
  { title: "Dashboard", desc: "Your command center. See ImpactRank, streaks, and upcoming matches at a glance." },
  { title: "Gameplan", desc: "Build and manage your playbooks. AI-powered suggestions based on your style." },
  { title: "Opponents", desc: "Scout rivals. Track tendencies, weaknesses, and head-to-head history." },
  { title: "Drills", desc: "Sharpen your skills with targeted practice. Track improvement over time." },
  { title: "Chat", desc: "Connect with your squad. Strategize, share film, and coordinate." },
] as const;

const TOTAL_STEPS = 7;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);

  // Step 2 state
  const [selectedTitles, setSelectedTitles] = useState<string[]>([]);

  // Step 3 state
  const [offensiveStyle, setOffensiveStyle] = useState<string>("");
  const [defensiveStyle, setDefensiveStyle] = useState<string>("");
  const [riskLevel, setRiskLevel] = useState(5);

  // Step 4 state
  const [inputType, setInputType] = useState<string>("");

  // Step 5 state
  const [gamertag, setGamertag] = useState("");

  // Step 6 state
  const [tourIndex, setTourIndex] = useState(0);

  const next = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  const skip = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS));

  const toggleTitle = (title: string) => {
    setSelectedTitles((prev) =>
      prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title]
    );
  };

  const finish = () => {
    localStorage.setItem("onboarding_complete", "true");
    router.push("/dashboard");
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-8">
      {/* Progress Bar */}
      <div className="fixed left-0 right-0 top-0 z-50 h-1 bg-dark-800">
        <div
          className="h-full bg-forge-500 transition-all duration-300"
          style={{ width: `${(step / TOTAL_STEPS) * 100}%` }}
        />
      </div>
      <div className="fixed left-0 right-0 top-1 z-50 text-center text-xs text-dark-500">
        Step {step} of {TOTAL_STEPS}
      </div>

      {/* STEP 1 — Welcome */}
      {step === 1 && (
        <div className="flex flex-col items-center gap-6 text-center">
          <h1 className="text-5xl font-bold text-forge-400 md:text-6xl">EsportsForge</h1>
          <p className="text-xl text-dark-300 md:text-2xl">Built to Win. Not to Coach.</p>
          <div className="mt-8 flex gap-4">
            <button
              onClick={next}
              className="rounded-lg bg-forge-500 px-8 py-3 font-semibold text-dark-950 transition-colors hover:bg-forge-400"
            >
              Get Started
            </button>
            <button
              onClick={skip}
              className="rounded-lg border border-dark-600 px-8 py-3 font-semibold text-dark-300 transition-colors hover:border-dark-500 hover:text-dark-100"
            >
              Skip
            </button>
          </div>
        </div>
      )}

      {/* STEP 2 — Pick Title */}
      {step === 2 && (
        <div className="w-full max-w-3xl space-y-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-dark-50">Pick Your Titles</h2>
            <p className="mt-2 text-dark-400">Select the games you compete in.</p>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {TITLES.map((title) => (
              <button
                key={title}
                onClick={() => toggleTitle(title)}
                className={clsx(
                  "rounded-xl border-2 px-4 py-4 text-sm font-medium transition-all",
                  selectedTitles.includes(title)
                    ? "border-forge-500 bg-forge-500/10 text-forge-300"
                    : "border-dark-700 bg-dark-900 text-dark-300 hover:border-dark-500"
                )}
              >
                {title}
              </button>
            ))}
          </div>
          <div className="flex justify-center gap-4 pt-4">
            <button
              onClick={next}
              className="rounded-lg bg-forge-500 px-8 py-3 font-semibold text-dark-950 transition-colors hover:bg-forge-400"
            >
              Continue
            </button>
            <button
              onClick={skip}
              className="rounded-lg border border-dark-600 px-6 py-3 text-sm text-dark-400 transition-colors hover:text-dark-200"
            >
              Skip
            </button>
          </div>
        </div>
      )}

      {/* STEP 3 — Identity */}
      {step === 3 && (
        <div className="w-full max-w-3xl space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-dark-50">Your Identity</h2>
            <p className="mt-2 text-dark-400">Define your playstyle DNA.</p>
          </div>

          {/* Offensive */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-dark-200">Offensive Style</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {OFFENSIVE_STYLES.map((style) => (
                <button
                  key={style.id}
                  onClick={() => setOffensiveStyle(style.id)}
                  className={clsx(
                    "rounded-xl border-2 p-4 text-left transition-all",
                    offensiveStyle === style.id
                      ? "border-forge-500 bg-forge-500/10"
                      : "border-dark-700 bg-dark-900 hover:border-dark-500"
                  )}
                >
                  <p className="font-semibold text-dark-100">{style.label}</p>
                  <p className="mt-1 text-xs text-dark-400">{style.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Defensive */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-dark-200">Defensive Style</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {DEFENSIVE_STYLES.map((style) => (
                <button
                  key={style.id}
                  onClick={() => setDefensiveStyle(style.id)}
                  className={clsx(
                    "rounded-xl border-2 p-4 text-left transition-all",
                    defensiveStyle === style.id
                      ? "border-forge-500 bg-forge-500/10"
                      : "border-dark-700 bg-dark-900 hover:border-dark-500"
                  )}
                >
                  <p className="font-semibold text-dark-100">{style.label}</p>
                  <p className="mt-1 text-xs text-dark-400">{style.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Risk Slider */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-dark-200">
              Risk Tolerance: <span className="text-forge-400">{riskLevel}</span>
            </h3>
            <input
              type="range"
              min={1}
              max={10}
              value={riskLevel}
              onChange={(e) => setRiskLevel(Number(e.target.value))}
              className="w-full accent-forge-500"
            />
            <div className="flex justify-between text-xs text-dark-500">
              <span>Conservative (1)</span>
              <span>Aggressive (10)</span>
            </div>
          </div>

          <div className="flex justify-center gap-4 pt-4">
            <button
              onClick={next}
              className="rounded-lg bg-forge-500 px-8 py-3 font-semibold text-dark-950 transition-colors hover:bg-forge-400"
            >
              Continue
            </button>
          </div>
        </div>
      )}

      {/* STEP 4 — Input Type */}
      {step === 4 && (
        <div className="w-full max-w-2xl space-y-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-dark-50">Input Type</h2>
            <p className="mt-2 text-dark-400">How do you play?</p>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {INPUT_TYPES.map((type) => (
              <button
                key={type.id}
                onClick={() => setInputType(type.id)}
                className={clsx(
                  "flex flex-col items-center gap-3 rounded-xl border-2 p-8 transition-all",
                  inputType === type.id
                    ? "border-forge-500 bg-forge-500/10"
                    : "border-dark-700 bg-dark-900 hover:border-dark-500"
                )}
              >
                <span className="text-4xl">{type.icon}</span>
                <span className="font-semibold text-dark-100">{type.label}</span>
              </button>
            ))}
          </div>
          <div className="flex justify-center pt-4">
            <button
              onClick={next}
              className="rounded-lg bg-forge-500 px-8 py-3 font-semibold text-dark-950 transition-colors hover:bg-forge-400"
            >
              Continue
            </button>
          </div>
        </div>
      )}

      {/* STEP 5 — First Opponent */}
      {step === 5 && (
        <div className="w-full max-w-md space-y-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-dark-50">First Opponent</h2>
            <p className="mt-2 text-dark-400">Add a rival to scout. You can always add more later.</p>
          </div>
          <input
            type="text"
            value={gamertag}
            onChange={(e) => setGamertag(e.target.value)}
            placeholder="Enter gamertag..."
            className="w-full rounded-lg border border-dark-600 bg-dark-800 px-4 py-3 text-dark-50 placeholder-dark-500 transition-colors focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500"
          />
          <div className="flex justify-center gap-4">
            <button
              onClick={next}
              className="rounded-lg bg-forge-500 px-8 py-3 font-semibold text-dark-950 transition-colors hover:bg-forge-400"
            >
              {gamertag.trim() ? "Add & Continue" : "Continue"}
            </button>
            <button
              onClick={skip}
              className="rounded-lg border border-dark-600 px-6 py-3 text-sm text-dark-400 transition-colors hover:text-dark-200"
            >
              Skip
            </button>
          </div>
        </div>
      )}

      {/* STEP 6 — Tour */}
      {step === 6 && (
        <div className="w-full max-w-lg space-y-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-dark-50">Quick Tour</h2>
            <p className="mt-2 text-dark-400">Here is what EsportsForge can do for you.</p>
          </div>
          <div className="rounded-xl border border-dark-700 bg-dark-900 p-8">
            <h3 className="text-xl font-bold text-forge-400">{TOUR_PANELS[tourIndex]!.title}</h3>
            <p className="mt-3 text-dark-300">{TOUR_PANELS[tourIndex]!.desc}</p>
          </div>
          {/* Progress dots */}
          <div className="flex justify-center gap-2">
            {TOUR_PANELS.map((_, i) => (
              <button
                key={i}
                onClick={() => setTourIndex(i)}
                className={clsx(
                  "h-2.5 w-2.5 rounded-full transition-colors",
                  i === tourIndex ? "bg-forge-500" : "bg-dark-600"
                )}
              />
            ))}
          </div>
          <div className="flex justify-center gap-4 pt-2">
            {tourIndex < TOUR_PANELS.length - 1 ? (
              <button
                onClick={() => setTourIndex((i) => i + 1)}
                className="rounded-lg bg-forge-500 px-8 py-3 font-semibold text-dark-950 transition-colors hover:bg-forge-400"
              >
                Next
              </button>
            ) : (
              <button
                onClick={next}
                className="rounded-lg bg-forge-500 px-8 py-3 font-semibold text-dark-950 transition-colors hover:bg-forge-400"
              >
                Finish Tour
              </button>
            )}
            <button
              onClick={next}
              className="rounded-lg border border-dark-600 px-6 py-3 text-sm text-dark-400 transition-colors hover:text-dark-200"
            >
              Skip
            </button>
          </div>
        </div>
      )}

      {/* STEP 7 — Launch */}
      {step === 7 && (
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-forge-500/20">
            <div className="h-10 w-10 animate-pulse rounded-full bg-forge-500" />
          </div>
          <h2 className="text-3xl font-bold text-dark-50">Your PlayerTwin is being built.</h2>
          <p className="max-w-md text-dark-400">
            We are analyzing your playstyle, building your digital twin, and preparing your dashboard.
          </p>
          <button
            onClick={finish}
            className="mt-4 rounded-lg bg-forge-500 px-8 py-3 font-semibold text-dark-950 transition-colors hover:bg-forge-400"
          >
            Go to Dashboard
          </button>
        </div>
      )}
    </main>
  );
}
