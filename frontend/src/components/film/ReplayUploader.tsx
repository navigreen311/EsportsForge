"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Upload, Check, Loader2, Circle } from "lucide-react";
import { VisionAudioForgeService } from "@/lib/services/visionaudioforge";

type UploadState = "idle" | "processing" | "complete";

const ACCEPTED_FORMATS = ".mp4,.mov,.avi,.mkv";

interface ProcessingStep {
  label: string;
  status: "pending" | "active" | "done";
}

const INITIAL_STEPS: ProcessingStep[] = [
  { label: "Detecting formations", status: "pending" },
  { label: "Tagging play calls", status: "pending" },
  { label: "Identifying mistakes", status: "pending" },
  { label: "Building ImpactRank priority list", status: "pending" },
  { label: "Generating 3 priority fixes", status: "pending" },
];

const MOCK_ANALYSIS = {
  grade: "B+",
  topMistake: "Late reads on Cover 3 — 4 missed opportunities",
  topStrength: "Red zone execution — 3/4 touchdown conversions",
  totalPlaysTagged: 24,
  plays: [
    { timestamp: "2:14", playType: "PA Boot Over", result: "Incomplete", category: "Pre-snap" as const },
    { timestamp: "4:37", playType: "HB Dive", result: "2 yd gain", category: "Scheme" as const },
    { timestamp: "6:02", playType: "Mesh Spot", result: "Touchdown", category: "Post-snap" as const },
    { timestamp: "7:45", playType: "Cover 3 Drop", result: "INT thrown", category: "Mental" as const },
    { timestamp: "9:18", playType: "Slant Flat", result: "15 yd gain", category: "Mechanical" as const },
    { timestamp: "10:55", playType: "QB Draw", result: "8 yd gain", category: "Pre-snap" as const },
    { timestamp: "12:31", playType: "Verticals", result: "Incomplete", category: "Mechanical" as const },
    { timestamp: "14:09", playType: "HB Wheel", result: "22 yd gain", category: "Post-snap" as const },
    { timestamp: "15:42", playType: "Screen Pass", result: "Loss of 3", category: "Scheme" as const },
    { timestamp: "17:20", playType: "PA Crossers", result: "Sack", category: "Mental" as const },
    { timestamp: "18:58", playType: "Inside Zone", result: "5 yd gain", category: "Pre-snap" as const },
    { timestamp: "20:33", playType: "Corner Route", result: "Touchdown", category: "Post-snap" as const },
  ],
  fixes: [
    {
      description: "Speed up pre-snap reads — you're averaging 4.2s in the pocket before your first read progression, leaving easy checkdowns on the table.",
      winRateImpact: "+8.3%",
    },
    {
      description: "Check down earlier under pressure — when blitzed, you hold the ball 1.8s longer than optimal, leading to 3 sacks and 1 INT this game.",
      winRateImpact: "+5.1%",
    },
    {
      description: "Use hot routes vs blitz — you audibled on only 1 of 6 blitz looks; hot route adjustments would convert 2-3 of those into positive plays.",
      winRateImpact: "+3.7%",
    },
  ],
};

interface ReplayUploaderProps {
  onAnalysisComplete: (result: any) => void;
}

export default function ReplayUploader({
  onAnalysisComplete,
}: ReplayUploaderProps) {
  const [state, setState] = useState<UploadState>("idle");
  const [percent, setPercent] = useState(0);
  const [steps, setSteps] = useState<ProcessingStep[]>(INITIAL_STEPS);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<File | null>(null);

  const startProcessing = useCallback(() => {
    setState("processing");
    setPercent(0);
    setSteps(INITIAL_STEPS.map((s) => ({ ...s, status: "pending" })));
  }, []);

  // Simulated progress: 0% -> 100% over ~8 seconds with step transitions
  useEffect(() => {
    if (state !== "processing") return;

    // Step thresholds: each step completes at a percentage
    const stepThresholds = [15, 35, 60, 82, 100];
    let current = 0;

    const interval = setInterval(() => {
      current += Math.random() * 2.5 + 0.8;
      if (current > 100) current = 100;

      setPercent(Math.round(current));

      // Update step statuses based on current progress
      setSteps((prev) =>
        prev.map((step, i) => {
          const threshold = stepThresholds[i];
          const prevThreshold = i > 0 ? stepThresholds[i - 1] : 0;
          if (current >= threshold) return { ...step, status: "done" };
          if (current >= prevThreshold) return { ...step, status: "active" };
          return { ...step, status: "pending" };
        })
      );

      if (current >= 100) {
        clearInterval(interval);
        // Call the service, then deliver results
        const fakeFile = fileRef.current ?? new Blob(["mock"], { type: "video/mp4" });
        VisionAudioForgeService.analyzeReplay(fakeFile).then(() => {
          setState("complete");
          onAnalysisComplete(MOCK_ANALYSIS);
        });
      }
    }, 200);

    return () => clearInterval(interval);
  }, [state, onAnalysisComplete]);

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      fileRef.current = file;
      startProcessing();
    },
    [startProcessing]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragOver(false);
      handleFile(e.dataTransfer.files[0]);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFile(e.target.files?.[0]);
    },
    [handleFile]
  );

  // Processing state
  if (state === "processing") {
    return (
      <div className="w-full max-w-lg mx-auto rounded-xl border border-dark-700 bg-dark-800/60 p-8">
        <p className="text-lg font-semibold text-white mb-1 text-center">
          FilmAI is analyzing your replay
        </p>
        <p className="text-2xl font-bold text-forge-400 text-center mb-5">
          {percent}%
        </p>

        {/* Progress bar */}
        <div className="mx-auto h-2.5 w-full overflow-hidden rounded-full bg-dark-700 mb-6">
          <div
            className="h-full rounded-full bg-gradient-to-r from-forge-400 to-emerald-500 transition-all duration-200"
            style={{ width: `${percent}%` }}
          />
        </div>

        {/* Step checklist */}
        <div className="space-y-3">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-3">
              {step.status === "done" ? (
                <Check className="h-4 w-4 text-forge-400 shrink-0" />
              ) : step.status === "active" ? (
                <Loader2 className="h-4 w-4 text-forge-400 animate-spin shrink-0" />
              ) : (
                <Circle className="h-4 w-4 text-dark-600 shrink-0" />
              )}
              <span
                className={`text-sm ${
                  step.status === "done"
                    ? "text-dark-300"
                    : step.status === "active"
                    ? "text-white font-medium"
                    : "text-dark-500"
                }`}
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (state === "complete") {
    return null;
  }

  // Idle state — drag-and-drop zone
  return (
    <div className="w-full max-w-lg">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`rounded-xl border-2 border-dashed bg-dark-900/30 p-10 text-center transition-colors cursor-pointer ${
          isDragOver
            ? "border-forge-400/60 bg-forge-400/5"
            : "border-dark-600 hover:border-dark-400"
        }`}
      >
        <Upload className="mx-auto mb-4 h-10 w-10 text-dark-400" />
        <p className="text-dark-200 font-medium mb-1">
          Drag and drop your replay here or click to browse
        </p>
        <p className="text-xs text-dark-500">
          MP4, MOV, AVI, MKV — Max 500MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_FORMATS}
          onChange={handleInputChange}
          className="hidden"
        />
      </div>

      <div className="mt-4 text-center">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="rounded-lg bg-forge-400 px-6 py-2.5 text-sm font-semibold text-dark-900 transition-colors hover:bg-forge-300"
        >
          Upload Replay
        </button>
      </div>
    </div>
  );
}
