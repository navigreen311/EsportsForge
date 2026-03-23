"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Upload } from "lucide-react";

type UploadState = "idle" | "uploading" | "processing" | "complete";

const ACCEPTED_FORMATS = ".mp4,.mov,.avi,.mkv";

const PROCESSING_STAGES = [
  "Detecting formations...",
  "Tagging play calls...",
  "Identifying mistakes...",
  "Building breakdown...",
];

const MOCK_RESULT = {
  grade: "B+",
  topMistake: "Late reads on Cover 3 \u2014 4 missed opportunities",
  topStrength: "Red zone execution \u2014 3/4 touchdown conversions",
  playCount: 24,
  mistakeCount: 6,
  fixes: [
    "Speed up pre-snap reads",
    "Check down earlier under pressure",
    "Use hot routes vs blitz",
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
  const [stageIndex, setStageIndex] = useState(0);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const startUpload = useCallback(() => {
    setState("uploading");
    setPercent(0);

    // Fake upload progress: 0 -> 100 over 2s
    const interval = setInterval(() => {
      setPercent((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 5;
      });
    }, 100);

    // Transition to processing after 2s
    setTimeout(() => {
      clearInterval(interval);
      setPercent(100);
      setState("processing");
      setStageIndex(0);
    }, 2000);
  }, []);

  // Cycle through processing stages every 1.5s
  useEffect(() => {
    if (state !== "processing") return;

    const interval = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % PROCESSING_STAGES.length);
    }, 1500);

    // Complete after 2s of processing (4s total)
    const timeout = setTimeout(() => {
      clearInterval(interval);
      setState("complete");
      onAnalysisComplete(MOCK_RESULT);
    }, 2000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [state, onAnalysisComplete]);

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      startUpload();
    },
    [startUpload]
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

  if (state === "uploading") {
    return (
      <div className="rounded-xl border-2 border-dashed border-dark-600 bg-dark-900/30 p-8 text-center">
        <p className="text-lg font-semibold text-white mb-4">
          Uploading... {percent}%
        </p>
        <div className="mx-auto h-2 w-64 max-w-full overflow-hidden rounded-full bg-dark-700">
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-100"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>
    );
  }

  if (state === "processing") {
    return (
      <div className="rounded-xl border-2 border-dashed border-dark-600 bg-dark-900/30 p-8 text-center">
        <p className="text-lg font-semibold text-white mb-2">
          FilmAI is watching your replay...
        </p>
        <p className="text-dark-300 animate-pulse">
          {PROCESSING_STAGES[stageIndex]}
        </p>
      </div>
    );
  }

  if (state === "complete") {
    return null;
  }

  // idle state
  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => inputRef.current?.click()}
      className={`rounded-xl border-2 border-dashed bg-dark-900/30 p-8 text-center transition-colors cursor-pointer ${
        isDragOver
          ? "border-dark-400"
          : "border-dark-600 hover:border-dark-400"
      }`}
    >
      <Upload className="mx-auto mb-3 h-10 w-10 text-dark-400" />
      <p className="text-dark-300">
        Upload your game replay to activate FilmAI
      </p>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_FORMATS}
        onChange={handleInputChange}
        className="hidden"
      />
    </div>
  );
}
