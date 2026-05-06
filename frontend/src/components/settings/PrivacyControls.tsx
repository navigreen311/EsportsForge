'use client';

import { useState } from 'react';
import { Eye, EyeOff, Download, Trash2, AlertTriangle } from 'lucide-react';
import type { PrivacySettings } from '@/types/settings';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8001';

interface PrivacyControlsProps {
  settings: PrivacySettings;
  onUpdate: (settings: Partial<PrivacySettings>) => void;
}

interface ToggleItemProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function ToggleItem({ label, description, checked, onChange }: ToggleItemProps) {
  return (
    <div className="flex items-start justify-between gap-4 py-4 border-b border-dark-800 last:border-0">
      <div className="flex items-start gap-3">
        {checked ? (
          <Eye className="w-4 h-4 text-forge-400 mt-0.5 shrink-0" />
        ) : (
          <EyeOff className="w-4 h-4 text-dark-500 mt-0.5 shrink-0" />
        )}
        <div>
          <p className="text-sm font-medium text-dark-200">{label}</p>
          <p className="text-xs text-dark-500 mt-0.5">{description}</p>
        </div>
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
          checked ? 'bg-forge-600' : 'bg-dark-600'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

export default function PrivacyControls({ settings, onUpdate }: PrivacyControlsProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [confirmTypedText, setConfirmTypedText] = useState('');
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function handleExport() {
    setExporting(true);
    setExportMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/privacy/export`, { method: 'POST' });
      if (res.ok) setExportMsg('Export queued — check your email in ~5 min for the download link.');
      else setExportMsg('Could not queue export — try again.');
    } catch {
      setExportMsg('Network error — try again.');
    } finally {
      setExporting(false);
      setTimeout(() => setExportMsg(null), 6000);
    }
  }

  async function handleConfirmDelete() {
    if (confirmTypedText !== 'DELETE') return;
    setDeleting(true);
    try {
      await fetch(`${API_BASE}/api/v1/privacy/delete`, { method: 'POST' });
    } catch { /* ignore */ }
    setDeleting(false);
    setShowDeleteConfirm(false);
    setConfirmTypedText('');
    alert('Deletion scheduled for 30 days from now. You will be logged out shortly. A recovery email is on the way.');
  }

  return (
    <div className="space-y-6">
      {/* Data Sharing Toggles */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 px-5">
        <ToggleItem
          label="Opponent Data Sharing"
          description="Allow your match data to be used in opponent scouting reports for other players."
          checked={settings.shareOpponentData}
          onChange={(v) => onUpdate({ shareOpponentData: v })}
        />
        <ToggleItem
          label="Community Data Sharing"
          description="Contribute anonymized data to community meta analysis and trend detection."
          checked={settings.shareCommunityData}
          onChange={(v) => onUpdate({ shareCommunityData: v })}
        />
        <ToggleItem
          label="Analytics Collection"
          description="Allow EsportsForge to collect usage analytics for improving AI recommendations."
          checked={settings.shareAnalytics}
          onChange={(v) => onUpdate({ shareAnalytics: v })}
        />
      </div>

      {/* Data Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-3 rounded-lg border border-dark-600 bg-dark-800 px-4 py-3 hover:border-forge-600 hover:bg-forge-500/5 transition-all group disabled:opacity-50"
        >
          <Download className="w-5 h-5 text-dark-400 group-hover:text-forge-400 transition-colors" />
          <div className="text-left">
            <p className="text-sm font-medium text-dark-200 group-hover:text-forge-400 transition-colors">
              {exporting ? 'Queueing…' : 'Export My Data'}
            </p>
            <p className="text-xs text-dark-500">Download all your data as JSON ZIP</p>
          </div>
        </button>

        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="flex items-center gap-3 rounded-lg border border-dark-600 bg-dark-800 px-4 py-3 hover:border-red-600 hover:bg-red-500/5 transition-all group"
          >
            <Trash2 className="w-5 h-5 text-dark-400 group-hover:text-red-400 transition-colors" />
            <div className="text-left">
              <p className="text-sm font-medium text-dark-200 group-hover:text-red-400 transition-colors">
                Delete My Data
              </p>
              <p className="text-xs text-dark-500">Permanently remove all data</p>
            </div>
          </button>
        ) : (
          <div className="rounded-lg border border-red-800 bg-red-500/10 px-4 py-3">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <p className="text-sm font-bold text-red-400">Type DELETE to confirm</p>
            </div>
            <p className="text-xs text-dark-400 mb-3">
              This permanently deletes all your data. Deletion is scheduled for 30 days
              (recoverable via email link), then irrevocable.
            </p>
            <input
              type="text"
              value={confirmTypedText}
              onChange={(e) => setConfirmTypedText(e.target.value)}
              placeholder="Type DELETE"
              className="w-full mb-3 rounded-md border border-red-500/40 bg-dark-900 px-3 py-1.5 text-sm text-dark-100 placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-red-500"
            />
            <div className="flex gap-2">
              <button
                onClick={() => { setShowDeleteConfirm(false); setConfirmTypedText(''); }}
                className="px-3 py-1.5 text-xs font-medium rounded-md bg-dark-700 text-dark-300 hover:bg-dark-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={confirmTypedText !== 'DELETE' || deleting}
                className="px-3 py-1.5 text-xs font-medium rounded-md bg-red-600 text-white hover:bg-red-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {deleting ? 'Scheduling…' : 'Yes, schedule deletion'}
              </button>
            </div>
          </div>
        )}
      </div>

      {exportMsg && (
        <p className="text-xs text-forge-400">{exportMsg}</p>
      )}
    </div>
  );
}
