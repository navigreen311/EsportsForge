'use client';

import { useState } from 'react';
import { Eye, EyeOff, Download, Trash2, AlertTriangle } from 'lucide-react';
import type { PrivacySettings } from '@/types/settings';

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
        <button className="flex items-center gap-3 rounded-lg border border-dark-600 bg-dark-800 px-4 py-3 hover:border-forge-600 hover:bg-forge-500/5 transition-all group">
          <Download className="w-5 h-5 text-dark-400 group-hover:text-forge-400 transition-colors" />
          <div className="text-left">
            <p className="text-sm font-medium text-dark-200 group-hover:text-forge-400 transition-colors">
              Export My Data
            </p>
            <p className="text-xs text-dark-500">Download all your data as JSON</p>
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
              <p className="text-sm font-bold text-red-400">Are you sure?</p>
            </div>
            <p className="text-xs text-dark-400 mb-3">
              This will permanently delete all your data, including match history, gameplans,
              and AI training data. This action cannot be undone.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-3 py-1.5 text-xs font-medium rounded-md bg-dark-700 text-dark-300 hover:bg-dark-600 transition-colors"
              >
                Cancel
              </button>
              <button className="px-3 py-1.5 text-xs font-medium rounded-md bg-red-600 text-white hover:bg-red-500 transition-colors">
                Yes, Delete Everything
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
