'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Modal } from '@/components/shared/Modal';
import { Film, Download } from 'lucide-react';

interface ClipExportButtonProps {
  gameplanName: string;
}

type ExportFormat = 'mp4' | 'gif';
type ExportPhase = 'idle' | 'processing' | 'ready';

export default function ClipExportButton({ gameplanName }: ClipExportButtonProps) {
  const [open, setOpen] = useState(false);
  const [includeOverlay, setIncludeOverlay] = useState(true);
  const [format, setFormat] = useState<ExportFormat>('mp4');
  const [includeOpponent, setIncludeOpponent] = useState(true);
  const [phase, setPhase] = useState<ExportPhase>('idle');
  const [percent, setPercent] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const reset = useCallback(() => {
    setPhase('idle');
    setPercent(0);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const handleClose = useCallback(() => {
    setOpen(false);
    reset();
  }, [reset]);

  const handleGenerate = useCallback(() => {
    setPhase('processing');
    setPercent(0);

    const step = 100 / 30; // 30 ticks over 3 seconds (100ms interval)
    intervalRef.current = setInterval(() => {
      setPercent((prev) => {
        const next = prev + step;
        if (next >= 100) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          intervalRef.current = null;
          setPhase('ready');
          return 100;
        }
        return Math.round(next);
      });
    }, 100);
  }, []);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const handleCopyLink = useCallback(() => {
    const fakeLink = `https://clip.esportsforge.gg/${gameplanName.toLowerCase().replace(/\s+/g, '-')}.${format}`;
    navigator.clipboard?.writeText(fakeLink);
  }, [gameplanName, format]);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800/50 px-3 py-2 text-xs font-medium text-dark-300 transition-colors hover:border-forge-500/50 hover:text-forge-400"
      >
        <Film className="h-4 w-4" />
        Clip Export
      </button>

      <Modal
        open={open}
        onClose={handleClose}
        title="Export Gameplan as Video Clip"
        size="md"
      >
        <div className="space-y-5">
          {/* Option 1: Performance overlay toggle */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-dark-200">Include performance overlay</span>
            <button
              type="button"
              role="switch"
              aria-checked={includeOverlay}
              onClick={() => setIncludeOverlay((v) => !v)}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                includeOverlay ? 'bg-forge-500' : 'bg-dark-600'
              }`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
                  includeOverlay ? 'translate-x-[18px]' : 'translate-x-[3px]'
                }`}
              />
            </button>
          </div>

          {/* Option 2: Format radio */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-dark-200">Format</span>
            <div className="flex gap-3">
              {(['mp4', 'gif'] as const).map((f) => (
                <label key={f} className="flex cursor-pointer items-center gap-1.5">
                  <input
                    type="radio"
                    name="clip-format"
                    value={f}
                    checked={format === f}
                    onChange={() => setFormat(f)}
                    className="accent-forge-500"
                  />
                  <span className="text-sm uppercase text-dark-200">{f}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Option 3: Include opponent data toggle */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-dark-200">Include opponent data</span>
            <button
              type="button"
              role="switch"
              aria-checked={includeOpponent}
              onClick={() => setIncludeOpponent((v) => !v)}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                includeOpponent ? 'bg-forge-500' : 'bg-dark-600'
              }`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
                  includeOpponent ? 'translate-x-[18px]' : 'translate-x-[3px]'
                }`}
              />
            </button>
          </div>

          {/* Progress bar */}
          {phase === 'processing' && (
            <div className="space-y-1.5">
              <div className="h-2 w-full overflow-hidden rounded-full bg-dark-700">
                <div
                  className="h-full rounded-full bg-forge-500 transition-all duration-100"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          )}

          {/* Ready message */}
          {phase === 'ready' && (
            <p className="text-center text-sm font-medium text-forge-400">
              Clip ready!
            </p>
          )}

          {/* Action buttons */}
          {phase === 'idle' && (
            <button
              onClick={handleGenerate}
              className="w-full rounded-lg bg-forge-500 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-forge-600"
            >
              Generate Clip
            </button>
          )}

          {phase === 'processing' && (
            <button
              disabled
              className="w-full cursor-not-allowed rounded-lg bg-forge-500/70 px-4 py-2.5 text-sm font-semibold text-white"
            >
              Generating... {percent}%
            </button>
          )}

          {phase === 'ready' && (
            <div className="flex gap-2">
              <button
                onClick={() => {}}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-forge-500 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-forge-600"
              >
                <Download className="h-4 w-4" />
                Download Clip
              </button>
              <button
                onClick={handleCopyLink}
                className="flex-1 rounded-lg border border-dark-600 bg-dark-800/50 px-4 py-2.5 text-sm font-semibold text-dark-200 transition-colors hover:border-forge-500/50 hover:text-forge-400"
              >
                Copy Link
              </button>
            </div>
          )}

          {/* Footer */}
          <p className="text-center text-[10px] text-dark-500">
            Powered by VisionAudioForge
          </p>
        </div>
      </Modal>
    </>
  );
}
