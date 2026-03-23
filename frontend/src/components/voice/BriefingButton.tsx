'use client';

import { Volume2, VolumeX } from 'lucide-react';
import { useVoiceForge } from '@/hooks/useVoiceForge';

interface BriefingButtonProps {
  priorityName: string;
  recommendation: string;
  confidence: number;
}

export default function BriefingButton({
  priorityName,
  recommendation,
  confidence,
}: BriefingButtonProps) {
  const { isAvailable, isSpeaking, speak, stop } = useVoiceForge();

  if (!isAvailable) return null;

  const handleClick = () => {
    if (isSpeaking) {
      stop();
      return;
    }

    const text = `Your top priority is ${priorityName}. The recommendation is: ${recommendation}. Confidence: ${confidence} percent.`;
    speak(text);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className="inline-flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800/50 px-3 py-1.5 text-xs font-medium text-dark-200 hover:border-forge-500/50 hover:text-forge-400 transition-colors"
    >
      {isSpeaking ? (
        <>
          <VolumeX className="h-4 w-4" />
          Speaking...
        </>
      ) : (
        <>
          <Volume2 className="h-4 w-4" />
          Read Briefing
        </>
      )}
    </button>
  );
}
