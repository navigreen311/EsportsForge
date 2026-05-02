/**
 * Quick "log a match" modal — opponent, win/loss, score, mode.
 */

'use client';

import { useState } from 'react';
import { Trophy, X as XIcon } from 'lucide-react';
import { clsx } from 'clsx';
import { Modal } from '@/components/shared/Modal';
import type { GameMode } from '@/lib/store';

export interface MatchLogPayload {
  opponent: string;
  result: 'win' | 'loss';
  myScore: number;
  theirScore: number;
  mode: GameMode;
}

interface LogMatchModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: MatchLogPayload) => void;
}

const MODES: { value: GameMode; label: string }[] = [
  { value: 'ranked', label: 'Ranked' },
  { value: 'tournament', label: 'Tournament' },
  { value: 'training', label: 'Casual' },
];

export function LogMatchModal({ open, onClose, onSubmit }: LogMatchModalProps) {
  const [opponent, setOpponent] = useState('');
  const [result, setResult] = useState<'win' | 'loss'>('win');
  const [myScore, setMyScore] = useState('');
  const [theirScore, setTheirScore] = useState('');
  const [mode, setMode] = useState<GameMode>('ranked');

  const reset = () => {
    setOpponent('');
    setResult('win');
    setMyScore('');
    setTheirScore('');
    setMode('ranked');
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSave = () => {
    if (!opponent.trim()) return;
    onSubmit({
      opponent: opponent.trim(),
      result,
      myScore: Number(myScore) || 0,
      theirScore: Number(theirScore) || 0,
      mode,
    });
    reset();
  };

  return (
    <Modal open={open} onClose={handleClose} title="Log a Match Result" size="md">
      <div className="space-y-5">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-dark-300">
            Opponent
          </label>
          <input
            type="text"
            value={opponent}
            onChange={(e) => setOpponent(e.target.value)}
            placeholder="Gamertag or team"
            className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-dark-300">
            Result
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setResult('win')}
              className={clsx(
                'rounded-lg border px-3 py-2 text-sm font-semibold transition-all',
                result === 'win'
                  ? 'border-forge-500 bg-forge-500/15 text-forge-400'
                  : 'border-dark-700 bg-dark-800 text-dark-300 hover:border-dark-600'
              )}
            >
              <Trophy className="mr-1.5 inline h-3.5 w-3.5" />
              Win
            </button>
            <button
              type="button"
              onClick={() => setResult('loss')}
              className={clsx(
                'rounded-lg border px-3 py-2 text-sm font-semibold transition-all',
                result === 'loss'
                  ? 'border-red-500 bg-red-500/15 text-red-400'
                  : 'border-dark-700 bg-dark-800 text-dark-300 hover:border-dark-600'
              )}
            >
              <XIcon className="mr-1.5 inline h-3.5 w-3.5" />
              Loss
            </button>
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-dark-300">
            Score
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              inputMode="numeric"
              value={myScore}
              onChange={(e) => setMyScore(e.target.value)}
              placeholder="Me"
              className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
            />
            <span className="text-dark-500">—</span>
            <input
              type="number"
              inputMode="numeric"
              value={theirScore}
              onChange={(e) => setTheirScore(e.target.value)}
              placeholder="Them"
              className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-dark-300">
            Mode
          </label>
          <div className="grid grid-cols-3 gap-2">
            {MODES.map((m) => (
              <button
                key={m.value}
                type="button"
                onClick={() => setMode(m.value)}
                className={clsx(
                  'rounded-lg border px-3 py-2 text-xs font-semibold transition-all',
                  mode === m.value
                    ? 'border-forge-500 bg-forge-500/15 text-forge-400'
                    : 'border-dark-700 bg-dark-800 text-dark-300 hover:border-dark-600'
                )}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-dark-700/50 pt-4">
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-dark-300 transition-colors hover:bg-dark-800 hover:text-dark-100"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!opponent.trim()}
            className="rounded-lg bg-forge-500 px-4 py-2 text-sm font-semibold text-dark-950 transition-colors hover:bg-forge-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Save Match
          </button>
        </div>
      </div>
    </Modal>
  );
}
