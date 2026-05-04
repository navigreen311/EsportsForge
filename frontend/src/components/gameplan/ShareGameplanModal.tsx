/**
 * Share modal — mints a 7-day public link for the current gameplan.
 */

'use client';

import { useState } from 'react';
import { Check, Copy, Loader2, Share2, X } from 'lucide-react';
import { shareGameplan, type ShareLinkResponse } from '@/lib/api/gameplan';

interface ShareGameplanModalProps {
  open: boolean;
  gameplanId: string | null;
  onClose: () => void;
}

export default function ShareGameplanModal({ open, gameplanId, onClose }: ShareGameplanModalProps) {
  const [loading, setLoading] = useState(false);
  const [link, setLink] = useState<ShareLinkResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open || !gameplanId) return null;

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await shareGameplan(gameplanId);
      setLink(res);
    } catch {
      setError('Could not create share link — try again.');
    } finally {
      setLoading(false);
    }
  };

  const copy = async () => {
    if (!link) return;
    const url = typeof window !== 'undefined' ? `${window.location.origin}${link.share_url_path}` : link.share_url_path;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore — clipboard may be unavailable in some browser contexts
    }
  };

  const fullUrl =
    link && typeof window !== 'undefined'
      ? `${window.location.origin}${link.share_url_path}`
      : link?.share_url_path ?? '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
      <div className="relative w-full max-w-md rounded-xl border border-forge-500/30 bg-dark-900 shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-3 top-3 text-dark-500 hover:text-dark-200"
        >
          <X className="h-5 w-5" />
        </button>
        <div className="border-b border-dark-700/50 px-6 py-4">
          <p className="text-xs uppercase tracking-wider text-forge-400">
            <Share2 className="mr-1 inline h-3.5 w-3.5" /> Share gameplan
          </p>
          <h2 className="mt-1 text-lg font-bold text-dark-50">Generate a 7-day public link</h2>
        </div>
        <div className="space-y-4 px-6 py-5">
          {error && <p className="text-sm text-red-400">{error}</p>}
          {!link && !loading && (
            <button
              type="button"
              onClick={run}
              className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950 hover:bg-forge-400"
            >
              <Share2 className="h-4 w-4" /> Create link
            </button>
          )}
          {loading && (
            <p className="flex items-center gap-2 text-sm text-dark-300">
              <Loader2 className="h-4 w-4 animate-spin" />
              Minting share token…
            </p>
          )}
          {link && (
            <div className="space-y-3">
              <div className="rounded-lg border border-dark-700/50 bg-dark-800/40 px-3 py-2">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-dark-400">
                  Public URL
                </p>
                <p className="mt-1 break-all text-xs text-dark-100">{fullUrl}</p>
              </div>
              <div className="flex items-center justify-between gap-2">
                <p className="text-[11px] text-dark-500">
                  Expires {new Date(link.expires_at).toLocaleString()}
                </p>
                <button
                  type="button"
                  onClick={copy}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-forge-500 px-3 py-1.5 text-xs font-bold text-dark-950 hover:bg-forge-400"
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? 'Copied' : 'Copy link'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
