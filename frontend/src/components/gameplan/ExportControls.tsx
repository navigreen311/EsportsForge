'use client';

import { FileText, BookOpen, FileJson, Copy, Check, Share2 } from 'lucide-react';
import { useCallback, useState } from 'react';
import ClipExportButton from '@/components/gameplan/ClipExportButton';
import type { Gameplan } from '@/types/gameplan';

interface ExportControlsProps {
  gameplanName: string;
  gameplan?: Gameplan;
  onShare?: () => void;
}

function gameplanToText(gp?: Gameplan): string {
  if (!gp) return '';
  const lines: string[] = [];
  lines.push(`# ${gp.name}`);
  if (gp.opponentSummary) {
    lines.push(
      `Opponent: ${gp.opponentName} | Top coverage: ${gp.opponentSummary.topCoverage} (${gp.opponentSummary.topCoveragePercent}%) | Blitz: ${gp.opponentSummary.blitzRate}%`,
    );
  }
  if (gp.overallStrategy) {
    lines.push('');
    lines.push(`Strategy: ${gp.overallStrategy}`);
  }
  lines.push('', '## Plays');
  gp.plays.forEach((p, i) => {
    lines.push(
      `${(p.rank ?? i + 1).toString().padStart(2, ' ')}. ${p.name} (${p.formation}) — confidence ${p.confidenceScore}%${p.isKillSheetPlay ? ' [KILL SHEET]' : ''}`,
    );
    if (p.whenToCall) lines.push(`     When: ${p.whenToCall}`);
  });
  if (gp.killSheetStructured?.length) {
    lines.push('', '## Kill Sheet');
    gp.killSheetStructured.forEach((k) =>
      lines.push(`#${k.rank}: ${k.name} (${k.formation}) — ${k.confidence}% — ${k.whenToCall}`),
    );
  }
  if (gp.scriptView?.length) {
    lines.push('', '## Script');
    gp.scriptView.forEach((s) => lines.push(`#${s.order} ${s.playName} (${s.formation}) — ${s.callWhen}`));
  }
  if (gp.twoMinDrill?.length) {
    lines.push('', '## 2-Min Drill');
    gp.twoMinDrill.forEach((d) => lines.push(`${d.time} ${d.situation}: ${d.call}`));
  }
  return lines.join('\n');
}

export default function ExportControls({ gameplanName, gameplan, onShare }: ExportControlsProps) {
  const [copied, setCopied] = useState(false);

  const handleCallSheet = useCallback(() => {
    // Browser-print path — the page has a print stylesheet that hides
    // chrome and renders the gameplan section in print-friendly form.
    if (typeof window !== 'undefined') window.print();
  }, []);

  const handleJson = useCallback(() => {
    if (!gameplan) return;
    const blob = new Blob([JSON.stringify(gameplan, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${gameplanName.replace(/\s+/g, '-').toLowerCase()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [gameplan, gameplanName]);

  const handleEbook = useCallback(() => {
    // eBook = same browser-print path with the print stylesheet.
    // (A real .epub would need a server-side renderer.)
    if (typeof window !== 'undefined') window.print();
  }, []);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(gameplanToText(gameplan));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  }, [gameplan]);

  const buttons = [
    { label: 'Call Sheet', icon: FileText, onClick: handleCallSheet },
    { label: 'eBook', icon: BookOpen, onClick: handleEbook },
    { label: 'JSON', icon: FileJson, onClick: handleJson, disabled: !gameplan },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2 print:hidden">
      {buttons.map((btn) => {
        const Icon = btn.icon;
        return (
          <button
            key={btn.label}
            onClick={btn.onClick}
            disabled={btn.disabled}
            className="inline-flex items-center gap-2 rounded-lg border border-dark-700 bg-dark-800/80 px-3 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-500 hover:bg-dark-700 hover:text-dark-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Icon className="h-4 w-4" />
            {btn.label}
          </button>
        );
      })}

      <button
        onClick={handleCopy}
        disabled={!gameplan}
        className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
          copied
            ? 'border-forge-500/30 bg-forge-500/10 text-forge-400'
            : 'border-dark-700 bg-dark-800/80 text-dark-200 hover:border-dark-500 hover:bg-dark-700 hover:text-dark-50'
        }`}
      >
        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        {copied ? 'Copied ✓' : 'Copy to Clipboard'}
      </button>

      {onShare && (
        <button
          onClick={onShare}
          disabled={!gameplan?.generatedId}
          className="inline-flex items-center gap-2 rounded-lg border border-forge-500/40 bg-forge-500/10 px-3 py-2 text-sm font-medium text-forge-300 transition-colors hover:bg-forge-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Share2 className="h-4 w-4" />
          Share
        </button>
      )}

      <ClipExportButton gameplanName={gameplanName} />
    </div>
  );
}
