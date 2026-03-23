'use client';

import { useState } from 'react';
import { Shield, Database, Eye, EyeOff, Download, Trash2, AlertTriangle } from 'lucide-react';

// ---------------------------------------------------------------------------
// Toggle (matches existing PrivacyControls style)
// ---------------------------------------------------------------------------

interface ToggleRowProps {
  label: string;
  badge?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}

function ToggleRow({ label, badge, checked, onChange }: ToggleRowProps) {
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div className="flex items-start gap-3">
        {checked ? (
          <Eye className="w-4 h-4 text-forge-400 mt-0.5 shrink-0" />
        ) : (
          <EyeOff className="w-4 h-4 text-dark-500 mt-0.5 shrink-0" />
        )}
        <div>
          <p className="text-sm text-dark-200">{label}</p>
          {badge && (
            <span className="mt-1 inline-block rounded bg-dark-700 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-dark-400">
              {badge}
            </span>
          )}
        </div>
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
          checked ? 'bg-forge-500' : 'bg-dark-600'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow ring-0 transition-transform ${
            checked ? 'translate-x-[18px]' : 'translate-x-[3px]'
          }`}
        />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Radio helpers
// ---------------------------------------------------------------------------

interface RadioOption<T extends string> {
  value: T;
  label: string;
}

interface RadioGroupProps<T extends string> {
  label: string;
  options: RadioOption<T>[];
  selected: T;
  onChange: (v: T) => void;
}

function RadioGroup<T extends string>({ label, options, selected, onChange }: RadioGroupProps<T>) {
  return (
    <div className="py-3">
      <p className="text-sm text-dark-200 mb-2">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
              selected === opt.value
                ? 'border-forge-500 bg-forge-500/10 text-forge-400'
                : 'border-dark-700 bg-dark-800 text-dark-400 hover:border-dark-600'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type SessionRetention = '30d' | '90d' | '1y' | 'forever';
type OpponentRetention = 'manual' | 'auto90';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function PrivacyTrustLayer() {
  // Section A – Community Intelligence
  const [contributePerformance, setContributePerformance] = useState(true);
  const [includeReplays, setIncludeReplays] = useState(false);
  const [shareScoutingTeam, setShareScoutingTeam] = useState(false);

  // Section B – Data Retention
  const [sessionRetention, setSessionRetention] = useState<SessionRetention>('1y');
  const [opponentRetention, setOpponentRetention] = useState<OpponentRetention>('manual');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Section C – Opponent Visibility
  const [allowViewNotification, setAllowViewNotification] = useState(false);
  const [showInLeaderboards, setShowInLeaderboards] = useState(true);

  return (
    <div className="space-y-6">
      {/* ── Section A: Community Intelligence ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-4 h-4 text-forge-400" />
          <h3 className="text-sm font-semibold text-dark-100">Community Intelligence</h3>
        </div>

        <div className="divide-y divide-dark-800">
          <ToggleRow
            label="Contribute anonymized performance data to improve MetaBot and ArchetypeAI"
            checked={contributePerformance}
            onChange={setContributePerformance}
          />
          <ToggleRow
            label="Include my replay patterns in community tendency database"
            checked={includeReplays}
            onChange={setIncludeReplays}
          />
          <ToggleRow
            label="Share my scouting reports with my team"
            badge="Team tier only"
            checked={shareScoutingTeam}
            onChange={setShareScoutingTeam}
          />
        </div>
      </div>

      {/* ── Section B: Data Retention ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Database className="w-4 h-4 text-forge-400" />
          <h3 className="text-sm font-semibold text-dark-100">Data Retention</h3>
        </div>

        <div className="divide-y divide-dark-800">
          <RadioGroup<SessionRetention>
            label="Keep session history for:"
            options={[
              { value: '30d', label: '30 days' },
              { value: '90d', label: '90 days' },
              { value: '1y', label: '1 year' },
              { value: 'forever', label: 'Forever' },
            ]}
            selected={sessionRetention}
            onChange={setSessionRetention}
          />

          <RadioGroup<OpponentRetention>
            label="Opponent data retention:"
            options={[
              { value: 'manual', label: 'Keep until I delete' },
              { value: 'auto90', label: 'Auto-expire after 90 days' },
            ]}
            selected={opponentRetention}
            onChange={setOpponentRetention}
          />
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button className="flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800 px-4 py-2 text-sm font-medium text-dark-300 hover:border-dark-500 hover:text-dark-200 transition-colors">
            <Download className="w-4 h-4" />
            Download My Data
          </button>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="flex items-center gap-2 rounded-lg bg-red-500/20 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/30 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Delete My Account
            </button>
          ) : (
            <div className="w-full rounded-lg border border-red-800 bg-red-500/10 px-4 py-3 mt-2">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <p className="text-sm font-bold text-red-400">Are you sure?</p>
              </div>
              <p className="text-xs text-dark-400 mb-3">
                This will permanently delete your account, all match history, gameplans, and AI
                training data. This action cannot be undone.
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

      {/* ── Section C: Opponent Visibility ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Eye className="w-4 h-4 text-forge-400" />
          <h3 className="text-sm font-semibold text-dark-100">Opponent Visibility</h3>
        </div>

        <div className="divide-y divide-dark-800">
          <ToggleRow
            label="Allow opponents I've scouted to see that I viewed their profile"
            checked={allowViewNotification}
            onChange={setAllowViewNotification}
          />
          <ToggleRow
            label="Show my gamertag in community leaderboards"
            checked={showInLeaderboards}
            onChange={setShowInLeaderboards}
          />
        </div>
      </div>
    </div>
  );
}
