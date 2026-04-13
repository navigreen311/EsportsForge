"use client";

import { useState, useEffect, useRef } from "react";
import { Download, FileText, Table2, Link as LinkIcon, Film } from "lucide-react";

export default function ExportDropdown() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [filmFeedback, setFilmFeedback] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  function handlePDF() {
    setOpen(false);
    window.print();
  }

  function handleCSV() {
    setOpen(false);
    const headers = [
      "Date",
      "Mode",
      "Opponent",
      "Score",
      "WinRate",
      "Duration",
      "Recommendation",
      "Followed",
      "LoopAIOutcome",
      "TiltGuard",
      "Fatigue",
    ];
    const rows = [
      ["2026-04-10", "Ranked", "TeamAlpha", "3-1", "72%", "42m", "Aggressive", "Yes", "Win", "Low", "Medium"],
      ["2026-04-09", "Scrim", "TeamBeta", "2-2", "55%", "38m", "Balanced", "No", "Draw", "Medium", "High"],
      ["2026-04-08", "Ranked", "TeamGamma", "1-3", "41%", "45m", "Defensive", "Yes", "Loss", "High", "High"],
    ];
    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `esportsforge-sessions-${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function handleCopyLink() {
    const shareUrl =
      "https://esportsforge.gg/shared/analytics/" +
      crypto.randomUUID().slice(0, 8);
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setOpen(false);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleFilmRoom() {
    setOpen(false);
    window.dispatchEvent(new CustomEvent("switch-to-filmroom"));
    setFilmFeedback(true);
    setTimeout(() => setFilmFeedback(false), 2000);
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg border border-dark-600 bg-dark-800/50 text-sm font-medium text-dark-200 hover:border-dark-500 transition-colors"
      >
        <Download className="h-4 w-4" />
        {copied ? "Copied!" : filmFeedback ? "Opening Film Room..." : "Export"}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-56 rounded-lg border border-dark-700 bg-dark-900 shadow-xl z-20 py-1">
          <button
            onClick={handlePDF}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-dark-200 hover:bg-dark-700/50 transition-colors"
          >
            <FileText className="h-4 w-4" />
            Download PDF Report
          </button>
          <button
            onClick={handleCSV}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-dark-200 hover:bg-dark-700/50 transition-colors"
          >
            <Table2 className="h-4 w-4" />
            Export Session History CSV
          </button>
          <button
            onClick={handleCopyLink}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-dark-200 hover:bg-dark-700/50 transition-colors"
          >
            <LinkIcon className="h-4 w-4" />
            {copied ? "Copied!" : "Copy Shareable Report Link"}
          </button>
          <button
            onClick={handleFilmRoom}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-dark-200 hover:bg-dark-700/50 transition-colors"
          >
            <Film className="h-4 w-4" />
            Export Analyst Breakdown
          </button>
        </div>
      )}
    </div>
  );
}
