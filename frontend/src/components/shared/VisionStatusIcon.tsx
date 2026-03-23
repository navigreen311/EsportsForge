'use client';

import { useState, useEffect, useRef } from 'react';
import { Eye, EyeOff, Lock, Check, X } from 'lucide-react';
import Link from 'next/link';
import { useUIStore } from '@/lib/store';

type VisionStatus = 'active' | 'processing' | 'offline' | 'restricted';

const STATUS_CONFIG: Record<VisionStatus, { tooltip: string }> = {
  active: { tooltip: 'VisionAudioForge — Ready' },
  processing: { tooltip: 'FilmAI is analyzing...' },
  offline: { tooltip: 'VisionAudioForge offline' },
  restricted: { tooltip: 'Screen capture disabled in Ranked mode (anti-cheat)' },
};

export default function VisionStatusIcon() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const currentMode = useUIStore((s) => s.currentMode);

  // Determine status based on integrity / game mode
  const status: VisionStatus =
    currentMode === 'ranked' || currentMode === 'tournament'
      ? 'restricted'
      : 'active';

  const isRestricted = status === 'restricted';

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const features = [
    { label: 'Film Analysis', available: true },
    { label: 'Replay Upload', available: true },
    { label: 'Screen Capture', available: !isRestricted },
    { label: 'Input Telemetry', available: true },
    { label: 'Clip Export', available: true },
  ];

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Icon Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="rounded-lg p-2 text-dark-400 hover:bg-dark-800 hover:text-dark-200 transition-colors relative"
        title={STATUS_CONFIG[status].tooltip}
        aria-label={STATUS_CONFIG[status].tooltip}
      >
        {status === 'offline' ? (
          <EyeOff className="h-5 w-5 text-dark-500" />
        ) : status === 'restricted' ? (
          <span className="relative inline-flex">
            <Eye className="h-5 w-5" />
            <Lock className="absolute -bottom-0.5 -right-0.5 h-3 w-3 text-amber-400" />
          </span>
        ) : (
          <Eye className="h-5 w-5" />
        )}

        {/* Status dot overlay */}
        {status === 'active' && (
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-forge-400" />
        )}
        {status === 'processing' && (
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-72 z-20 rounded-lg border border-dark-700/50 bg-dark-900 shadow-xl p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-dark-100">VisionAudioForge</h3>
            <span
              className={`inline-flex items-center gap-1 text-xs font-medium ${
                isRestricted ? 'text-amber-400' : 'text-forge-400'
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isRestricted ? 'bg-amber-400' : 'bg-forge-400'
                }`}
              />
              {isRestricted ? 'Restricted' : 'Active'}
            </span>
          </div>

          {/* Source */}
          <p className="text-[10px] text-dark-500 mb-3">navigreen311/visionaudioforge</p>

          {/* Feature List */}
          <div className="space-y-1.5 mb-4">
            {features.map((feat) => (
              <div key={feat.label} className="flex items-center justify-between text-xs">
                <span className="text-dark-300">{feat.label}</span>
                {feat.available ? (
                  <span className="flex items-center gap-1 text-forge-400">
                    <Check className="h-3 w-3" />
                    Available
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-400">
                    <X className="h-3 w-3" />
                    Blocked
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Link
              href="/analytics"
              className="flex-1 rounded-md bg-dark-800 px-3 py-1.5 text-center text-xs font-medium text-dark-200 hover:bg-dark-700 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              Upload Replay
            </Link>
            <Link
              href="/analytics"
              className="flex-1 rounded-md bg-forge-600 px-3 py-1.5 text-center text-xs font-medium text-white hover:bg-forge-500 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              Open Film Room
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
