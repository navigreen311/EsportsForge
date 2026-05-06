'use client';

import {
  FileText,
  BookOpen,
  FileJson,
  Copy,
  Check,
  Share2,
  X,
} from 'lucide-react';
import { useState, useCallback } from 'react';
import ClipExportButton from '@/components/gameplan/ClipExportButton';
import type { Gameplan } from '@/types/gameplan';

interface ExportControlsProps {
  gameplan: Gameplan;
  opponent: { id: string; name: string };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function slug(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '') || 'opponent';
}

function downloadBlob(content: string, mime: string, filename: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function buildGameplanText(gameplan: Gameplan, opponentName: string): string {
  const lines: string[] = [];
  lines.push(`ESPORTSFORGE GAMEPLAN — vs ${opponentName}`);
  lines.push(
    `Generated: ${new Date().toLocaleString()}  |  ${gameplan.metaStatus.patchVersion}`
  );
  lines.push('');

  if (gameplan.killSheet?.length) {
    lines.push('KILL PLAYS');
    lines.push('─'.repeat(40));
    gameplan.killSheet.forEach((p, i) => {
      lines.push(
        `${i + 1}. ${p.name} (${p.formation}) — ${Math.round(
          p.confidenceScore
        )}% confidence`
      );
      if (p.beats) lines.push(`   Beats: ${p.beats}`);
      if (p.situationTags?.length)
        lines.push(`   Call when: ${p.situationTags.join(', ')}`);
    });
    lines.push('');
  }

  if (gameplan.plays?.length) {
    lines.push('FULL PLAY LIST');
    lines.push('─'.repeat(40));
    gameplan.plays.forEach((p, i) => {
      lines.push(
        `${i + 1}. ${p.name} (${p.formation}) — ${Math.round(
          p.confidenceScore
        )}%`
      );
    });
    lines.push('');
  }

  if (gameplan.redZonePackage?.length) {
    lines.push('RED ZONE PACKAGE');
    lines.push('─'.repeat(40));
    gameplan.redZonePackage.forEach((p) => lines.push(`• ${p.name}`));
    lines.push('');
  }

  if (gameplan.antiBlitzPackage?.length) {
    lines.push('ANTI-BLITZ PACKAGE');
    lines.push('─'.repeat(40));
    gameplan.antiBlitzPackage.forEach((p) => lines.push(`• ${p.name}`));
    lines.push('');
  }

  if (gameplan.twoMinDrillPackage?.length) {
    lines.push('2-MIN DRILL PACKAGE');
    lines.push('─'.repeat(40));
    gameplan.twoMinDrillPackage.forEach((p) => lines.push(`• ${p.name}`));
    lines.push('');
  }

  return lines.join('\n');
}

function buildCallSheetHtml(gameplan: Gameplan, opponentName: string): string {
  const styles = `
    body { font-family: -apple-system, system-ui, sans-serif; padding: 24px; color: #111; }
    h1 { font-size: 20px; margin: 0 0 4px; }
    h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin: 16px 0 6px; color: #4ADE80; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }
    .meta { font-size: 11px; color: #555; margin-bottom: 16px; }
    table { width: 100%; border-collapse: collapse; font-size: 11px; }
    th { text-align: left; padding: 4px 8px; background: #f3f4f6; }
    td { padding: 4px 8px; border-bottom: 1px solid #f3f4f6; }
    .kill { font-weight: 600; }
  `;
  const killRows = (gameplan.killSheet ?? [])
    .map(
      (p, i) =>
        `<tr><td class="kill">${i + 1}</td><td>${p.formation}</td><td class="kill">${p.name}</td><td>${
          p.situationTags?.join(', ') ?? ''
        }</td><td>${Math.round(p.confidenceScore)}%</td></tr>`
    )
    .join('');
  const allRows = (gameplan.plays ?? [])
    .map(
      (p, i) =>
        `<tr><td>${i + 1}</td><td>${p.formation}</td><td>${p.name}</td><td>${
          p.situationTags?.join(', ') ?? ''
        }</td><td>${Math.round(p.confidenceScore)}%</td></tr>`
    )
    .join('');
  return `<!doctype html><html><head><meta charset="utf-8"><title>Call Sheet — vs ${opponentName}</title><style>${styles}</style></head><body>
    <h1>EsportsForge Call Sheet</h1>
    <div class="meta">vs ${opponentName} &middot; ${gameplan.metaStatus.patchVersion} &middot; ${new Date().toLocaleString()}</div>
    <h2>Kill Sheet (top ${(gameplan.killSheet ?? []).length})</h2>
    <table><thead><tr><th>#</th><th>Formation</th><th>Play</th><th>Call When</th><th>Conf</th></tr></thead><tbody>${killRows}</tbody></table>
    <h2>Full Play List</h2>
    <table><thead><tr><th>#</th><th>Formation</th><th>Play</th><th>Call When</th><th>Conf</th></tr></thead><tbody>${allRows}</tbody></table>
  </body></html>`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ExportControls({
  gameplan,
  opponent,
}: ExportControlsProps) {
  const [copied, setCopied] = useState(false);
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [shareCopied, setShareCopied] = useState(false);

  const handleCallSheet = useCallback(() => {
    const html = buildCallSheetHtml(gameplan, opponent.name);
    const win = window.open('', '_blank');
    if (!win) return;
    win.document.write(html);
    win.document.close();
    setTimeout(() => win.print(), 250);
  }, [gameplan, opponent.name]);

  const handleEbook = useCallback(() => {
    const text = buildGameplanText(gameplan, opponent.name);
    downloadBlob(
      text,
      'text/markdown',
      `gameplan-vs-${slug(opponent.name)}.md`
    );
  }, [gameplan, opponent.name]);

  const handleJson = useCallback(() => {
    const json = JSON.stringify(gameplan, null, 2);
    downloadBlob(
      json,
      'application/json',
      `gameplan-vs-${slug(opponent.name)}-${Date.now()}.json`
    );
  }, [gameplan, opponent.name]);

  const handleCopy = useCallback(async () => {
    const text = buildGameplanText(gameplan, opponent.name);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable — silently degrade. Could fall back to
      // a hidden textarea + execCommand, but that's deprecated.
    }
  }, [gameplan, opponent.name]);

  const handleShare = useCallback(() => {
    // Backend share endpoint is a follow-up. For now we generate a synthetic
    // 7-day token-style URL so the UX is testable end-to-end.
    const token = `${slug(opponent.name)}-${gameplan.id ?? 'g'}-${Date.now()}`;
    const url =
      typeof window !== 'undefined'
        ? `${window.location.origin}/share/gameplan/${token}`
        : `/share/gameplan/${token}`;
    setShareLink(url);
    setShareCopied(false);
  }, [gameplan, opponent.name]);

  const handleShareCopy = useCallback(async () => {
    if (!shareLink) return;
    try {
      await navigator.clipboard.writeText(shareLink);
      setShareCopied(true);
      setTimeout(() => setShareCopied(false), 2000);
    } catch {
      /* noop */
    }
  }, [shareLink]);

  const baseBtn =
    'inline-flex items-center gap-2 rounded-lg border border-dark-700 bg-dark-800/80 px-3 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-500 hover:bg-dark-700 hover:text-dark-50';

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <button onClick={handleCallSheet} className={baseBtn}>
          <FileText className="h-4 w-4" />
          Call Sheet
        </button>
        <button onClick={handleEbook} className={baseBtn}>
          <BookOpen className="h-4 w-4" />
          eBook
        </button>
        <button onClick={handleJson} className={baseBtn}>
          <FileJson className="h-4 w-4" />
          JSON
        </button>
        <button
          onClick={handleCopy}
          className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
            copied
              ? 'border-forge-500/30 bg-forge-500/10 text-forge-400'
              : 'border-dark-700 bg-dark-800/80 text-dark-200 hover:border-dark-500 hover:bg-dark-700 hover:text-dark-50'
          }`}
        >
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          {copied ? 'Copied!' : 'Copy to Clipboard'}
        </button>
        <ClipExportButton gameplanName={gameplan.name} />
        <button onClick={handleShare} className={baseBtn}>
          <Share2 className="h-4 w-4" />
          Share
        </button>
      </div>

      {shareLink && (
        <ShareLinkDialog
          url={shareLink}
          onCopy={handleShareCopy}
          copied={shareCopied}
          onClose={() => setShareLink(null)}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Inline share-link modal
// ---------------------------------------------------------------------------

function ShareLinkDialog({
  url,
  copied,
  onCopy,
  onClose,
}: {
  url: string;
  copied: boolean;
  onCopy: () => void;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-5 shadow-xl">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-base font-semibold text-dark-50">
              Share gameplan
            </h3>
            <p className="mt-1 text-xs text-dark-400">
              This link expires in 7 days. Anyone with the link can view the
              gameplan.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200"
            aria-label="Close share dialog"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-4 flex items-center gap-2">
          <input
            readOnly
            value={url}
            onFocus={(e) => e.currentTarget.select()}
            className="flex-1 rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-xs text-dark-200 focus:border-forge-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={onCopy}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
              copied
                ? 'border-forge-500/40 bg-forge-500/15 text-forge-300'
                : 'border-dark-700 bg-dark-800 text-dark-200 hover:border-dark-500 hover:bg-dark-700'
            }`}
          >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy Link'}
          </button>
        </div>
      </div>
    </div>
  );
}
