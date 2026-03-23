'use client';

import { useState, useEffect } from 'react';
import { Plug } from 'lucide-react';

export default function ForgeIntegrations() {
  const [voiceAvailable, setVoiceAvailable] = useState(false);

  useEffect(() => {
    setVoiceAvailable(
      typeof window !== 'undefined' && 'speechSynthesis' in window
    );
  }, []);

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Header */}
      <div className="mb-4 flex items-center gap-2">
        <Plug className="h-5 w-5 text-forge-400" />
        <h2 className="text-lg font-semibold text-white">Forge Integrations</h2>
      </div>

      {/* Integration Cards */}
      <div className="flex flex-col gap-4">
        {/* VoiceForge Card */}
        <div className="rounded-lg border border-dark-700/50 bg-dark-800/50 p-4">
          <div className="flex items-center justify-between">
            <span className="font-medium text-white">VoiceForge</span>
            <span className="flex items-center gap-1.5">
              {voiceAvailable ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  <span className="text-sm text-forge-400">Connected</span>
                </>
              ) : (
                <>
                  <span className="h-2 w-2 rounded-full bg-gray-500" />
                  <span className="text-sm text-dark-500">Offline</span>
                </>
              )}
            </span>
          </div>
          <p className="mt-1 text-sm text-dark-400">
            Voice coaching, briefings, commands
          </p>
          <p className="mt-1 text-[10px] text-dark-500">
            navigreen311/voiceforge
          </p>
          <button className="mt-3 text-sm text-forge-400 hover:text-forge-300 transition-colors">
            Configure Voice Settings
          </button>
        </div>

        {/* VisionAudioForge Card */}
        <div className="rounded-lg border border-dark-700/50 bg-dark-800/50 p-4">
          <div className="flex items-center justify-between">
            <span className="font-medium text-white">VisionAudioForge</span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm text-forge-400">Connected</span>
            </span>
          </div>
          <p className="mt-1 text-sm text-dark-400">
            Film analysis, input telemetry, clip export
          </p>
          <p className="mt-1 text-[10px] text-forge-400">
            Anti-cheat: Offline Lab only ✓
          </p>
          <p className="mt-1 text-[10px] text-dark-500">
            navigreen311/visionaudioforge
          </p>
          <button className="mt-3 text-sm text-forge-400 hover:text-forge-300 transition-colors">
            Configure Vision Settings
          </button>
        </div>
      </div>
    </div>
  );
}
