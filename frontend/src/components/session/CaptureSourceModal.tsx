/**
 * One-time setup prompt — asks how the player's game is displayed so the
 * VisionAudioForge frame-capture path knows whether to read from an HDMI
 * capture card, the local screen, or a webcam (NHJ19 / coach view).
 *
 * Selection is persisted to localStorage AND best-effort posted to user
 * settings via VisionAudioForgeService.setCaptureSource.
 */

'use client';

import { Tv, Monitor, Camera, X } from 'lucide-react';
import {
  VisionAudioForgeService,
  type CaptureSource,
} from '@/lib/services/visionaudioforge';

interface Props {
  open: boolean;
  onClose: () => void;
  onSelected: (source: CaptureSource) => void;
}

const OPTIONS: {
  value: CaptureSource;
  label: string;
  hint: string;
  icon: typeof Tv;
}[] = [
  {
    value: 'capture-card',
    label: 'TV via Capture Card',
    hint: 'Console (PS5/Xbox) → HDMI capture card → CLX PC',
    icon: Tv,
  },
  {
    value: 'pc-monitor',
    label: 'PC Monitor',
    hint: 'Game runs natively on this PC — software screen capture',
    icon: Monitor,
  },
  {
    value: 'camera',
    label: 'Camera / NHJ19',
    hint: 'Physical camera pointed at the screen or coach view',
    icon: Camera,
  },
];

export function CaptureSourceModal({ open, onClose, onSelected }: Props) {
  if (!open) return null;

  const select = (source: CaptureSource) => {
    VisionAudioForgeService.setCaptureSource(source);
    onSelected(source);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark-950/70 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-dark-700 bg-dark-900 p-6 shadow-2xl">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold text-dark-50">
              How is your game displayed?
            </h2>
            <p className="mt-1 text-xs text-dark-400">
              VisionAudioForge needs to know where to find your game screen.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-dark-400 hover:bg-dark-800 hover:text-dark-100"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-2">
          {OPTIONS.map((opt) => {
            const Icon = opt.icon;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => select(opt.value)}
                className="flex w-full items-start gap-3 rounded-lg border border-dark-700 bg-dark-800/60 p-3 text-left transition-colors hover:border-forge-500/40 hover:bg-forge-500/5"
              >
                <Icon className="mt-0.5 h-5 w-5 flex-shrink-0 text-forge-400" />
                <div>
                  <p className="text-sm font-bold text-dark-100">{opt.label}</p>
                  <p className="text-[11px] text-dark-400">{opt.hint}</p>
                </div>
              </button>
            );
          })}
        </div>

        <p className="mt-4 text-[11px] text-dark-500">
          You can change this later from Settings.
        </p>
      </div>
    </div>
  );
}
