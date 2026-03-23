'use client';

import { IdentityTrait } from '@/hooks/useProfile';
import { Fingerprint } from 'lucide-react';

interface IdentityCardProps {
  traits: IdentityTrait[];
}

export default function IdentityCard({ traits }: IdentityCardProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <h2 className="text-lg font-bold text-dark-100 mb-4 flex items-center gap-2">
        <Fingerprint className="w-5 h-5 text-purple-400" />
        Identity Card
      </h2>

      <div className="space-y-5">
        {traits.map((trait) => {
          const position = ((trait.value - trait.min) / (trait.max - trait.min)) * 100;
          return (
            <div key={trait.name}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-dark-200">
                  {trait.name}
                </span>
                <span className="text-sm font-mono font-bold text-dark-300">
                  {trait.value}
                </span>
              </div>

              {/* Slider track */}
              <div className="relative w-full h-2 bg-dark-800 rounded-full">
                {/* Fill */}
                <div
                  className="absolute top-0 left-0 h-2 rounded-full bg-gradient-to-r from-purple-600 to-purple-400"
                  style={{ width: `${position}%` }}
                />
                {/* Thumb */}
                <div
                  className="absolute top-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full bg-purple-400 border-2 border-dark-900 shadow-md"
                  style={{ left: `${position}%`, marginLeft: '-7px' }}
                />
              </div>

              {/* Labels */}
              <div className="flex justify-between mt-1">
                <span className="text-[10px] text-dark-500">
                  {trait.lowLabel}
                </span>
                <span className="text-[10px] text-dark-500">
                  {trait.highLabel}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
