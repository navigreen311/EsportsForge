'use client';

import { useState } from 'react';
import { Film } from 'lucide-react';

const FORMAT_OPTIONS = ['MP4', 'GIF', 'WebM'] as const;

export default function AnalystMode() {
  const [overlay, setOverlay] = useState(false);
  const [format, setFormat] = useState<(typeof FORMAT_OPTIONS)[number]>('MP4');
  const [exporting, setExporting] = useState(false);
  const [clipReady, setClipReady] = useState(false);
  const [shareableUrl, setShareableUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  function handleExport() {
    setExporting(true);
    setClipReady(false);

    setTimeout(() => {
      setExporting(false);
      setClipReady(true);
    }, 2000);
  }

  function handleGenerateReport() {
    setShareableUrl('https://esportsforge.gg/share/report-a1b2c3d4');
  }

  function handleCopyLink(url: string) {
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Header */}
      <h2 className="text-sm font-bold text-dark-300 uppercase tracking-wider mb-1 flex items-center gap-2">
        <Film className="w-4 h-4 text-cyan-400" />
        Analyst Mode
      </h2>
      <p className="text-xs text-dark-500 mb-5">
        Create shareable clips and breakdowns
      </p>

      {/* ── CLIP EXPORT ── */}
      <section className="mb-6">
        <h3 className="text-[11px] font-semibold uppercase tracking-wide text-dark-500 mb-3">
          Clip Export
        </h3>

        {/* Upload zone */}
        <div className="flex items-center justify-center rounded-lg border border-dashed border-dark-600 bg-dark-800/30 px-4 py-6 mb-3">
          <span className="text-xs text-dark-400">
            Drag & drop video or click to upload
          </span>
        </div>

        {/* Overlay checkbox */}
        <label className="flex items-center gap-2 mb-3 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={overlay}
            onChange={(e) => setOverlay(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-dark-600 bg-dark-800 accent-forge-500"
          />
          <span className="text-xs text-dark-300">Add performance overlay</span>
        </label>

        {/* Format selector */}
        <div className="flex items-center gap-2 mb-4">
          {FORMAT_OPTIONS.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFormat(f)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                format === f
                  ? 'bg-forge-500 text-white'
                  : 'bg-dark-800 text-dark-400 hover:text-dark-300'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Export button */}
        <button
          type="button"
          onClick={handleExport}
          disabled={exporting}
          className="w-full rounded-lg bg-forge-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-forge-600 disabled:opacity-50"
        >
          {exporting ? 'Processing...' : 'Export Clip'}
        </button>

        {/* Clip ready state */}
        {clipReady && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-emerald-400 font-medium">Clip ready —</span>
            <button
              type="button"
              className="text-xs font-medium text-forge-400 hover:text-forge-300 underline"
            >
              Download
            </button>
            <button
              type="button"
              onClick={() => handleCopyLink('https://esportsforge.gg/clips/export-x9z8')}
              className="text-xs font-medium text-dark-400 hover:text-dark-300 underline"
            >
              {copied ? 'Copied!' : 'Copy Link'}
            </button>
          </div>
        )}
      </section>

      {/* ── POST-GAME BREAKDOWN ── */}
      <section>
        <h3 className="text-[11px] font-semibold uppercase tracking-wide text-dark-500 mb-3">
          Post-Game Breakdown
        </h3>

        <button
          type="button"
          onClick={handleGenerateReport}
          className="w-full rounded-lg bg-forge-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-forge-600"
        >
          Generate Shareable Report
        </button>

        {shareableUrl && (
          <div className="mt-3 space-y-2">
            <div className="flex items-center gap-2 rounded-lg bg-dark-800/40 px-3 py-2">
              <span className="truncate text-xs text-dark-300 font-mono">
                {shareableUrl}
              </span>
            </div>
            <button
              type="button"
              onClick={() => handleCopyLink(shareableUrl)}
              className="rounded-md bg-dark-800 px-3 py-1.5 text-xs font-medium text-dark-300 hover:text-dark-200 transition-colors"
            >
              {copied ? 'Copied!' : 'Copy shareable link'}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
