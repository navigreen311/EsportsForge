'use client';

import { Mic, MicOff, Volume2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useVoiceForge } from '@/hooks/useVoiceForge';
import { matchVoiceCommand } from '@/lib/voiceCommandRouter';

export default function VoiceCommandButton() {
  const { isAvailable, isListening, isSpeaking, listen, speak } =
    useVoiceForge();
  const router = useRouter();

  if (!isAvailable) return null;

  const handleClick = async () => {
    if (isListening || isSpeaking) return;

    const result = await listen();

    if (!result) {
      speak("Sorry, I didn't catch that. Try again.");
      return;
    }

    const match = matchVoiceCommand(result);

    if (match) {
      if (match.navigate) {
        router.push(match.navigate);
      }
      speak(`Got it — ${match.description}`);
    } else {
      speak("Sorry, I didn't catch that. Try again.");
    }
  };

  if (isSpeaking) {
    return (
      <button
        type="button"
        className="bg-forge-500/10 rounded-lg p-2"
        aria-label="Speaking"
      >
        <Volume2 className="h-5 w-5 text-forge-400" />
      </button>
    );
  }

  if (isListening) {
    return (
      <div className="relative">
        <button
          type="button"
          className="ring-2 ring-forge-500/50 animate-pulse bg-forge-500/10 rounded-lg p-2"
          aria-label="Listening for voice command"
        >
          <Mic className="h-5 w-5 text-forge-400" />
        </button>
        <span className="absolute left-1/2 -translate-x-1/2 top-full mt-1 text-[10px] text-forge-400 whitespace-nowrap">
          Listening...
        </span>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className="rounded-lg p-2 hover:bg-dark-800 transition-colors"
      aria-label="Voice command"
    >
      <Mic className="h-5 w-5 text-dark-400" />
    </button>
  );
}
