'use client';

import { X } from 'lucide-react';

interface ShortcutsCheatsheetProps {
  open: boolean;
  onClose: () => void;
}

interface ShortcutEntry {
  keys: string[];
  label: string;
}

const SHORTCUT_GROUPS: { title: string; shortcuts: ShortcutEntry[] }[] = [
  {
    title: 'Navigation',
    shortcuts: [
      { keys: ['G', 'D'], label: 'Dashboard' },
      { keys: ['G', 'G'], label: 'Gameplan' },
      { keys: ['G', 'O'], label: 'Opponents' },
      { keys: ['G', 'R'], label: 'Drills' },
      { keys: ['G', 'A'], label: 'Analytics' },
      { keys: ['G', 'S'], label: 'Settings' },
      { keys: ['G', 'T'], label: 'Tournament' },
      { keys: ['G', 'V'], label: 'Vault' },
    ],
  },
  {
    title: 'Actions',
    shortcuts: [
      { keys: ['Ctrl/⌘', 'K'], label: 'Search' },
      { keys: ['N'], label: 'New gameplan' },
      { keys: ['?'], label: 'Show shortcuts' },
    ],
  },
  {
    title: 'General',
    shortcuts: [
      { keys: ['Esc'], label: 'Close modal' },
    ],
  },
];

export function ShortcutsCheatsheet({ open, onClose }: ShortcutsCheatsheetProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-dark-900/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-dark-700/50 bg-dark-800 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-dark-700/50 px-5 py-4">
          <h2 className="text-base font-semibold text-dark-100">Keyboard Shortcuts</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-dark-500 hover:bg-dark-700 hover:text-dark-300 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Shortcuts grid */}
        <div className="p-5 space-y-6">
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.title}>
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-dark-500">
                {group.title}
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {group.shortcuts.map((shortcut) => (
                  <div
                    key={shortcut.label}
                    className="flex items-center justify-between rounded-lg bg-dark-900/50 px-3 py-2"
                  >
                    <span className="text-sm text-dark-300">{shortcut.label}</span>
                    <div className="flex items-center gap-1">
                      {shortcut.keys.map((key, i) => (
                        <span key={i}>
                          <kbd className="rounded bg-dark-700 px-1.5 py-0.5 text-xs font-mono text-dark-400">
                            {key}
                          </kbd>
                          {i < shortcut.keys.length - 1 && (
                            <span className="mx-0.5 text-dark-600">+</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
