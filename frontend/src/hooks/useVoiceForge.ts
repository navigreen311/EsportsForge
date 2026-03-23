/**
 * React hook wrapping VoiceForgeService.
 *
 * Provides reactive state (isListening, isSpeaking, transcript) and safe
 * async wrappers that never throw.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import {
  VoiceForgeService,
  type SpeakOptions,
  type ListenOptions,
} from "@/lib/services/voiceforge";

export interface UseVoiceForgeReturn {
  speak: (text: string, opts?: SpeakOptions) => Promise<void>;
  listen: (opts?: ListenOptions) => Promise<string>;
  stop: () => void;
  isListening: boolean;
  isSpeaking: boolean;
  isAvailable: boolean;
  transcript: string;
}

export function useVoiceForge(): UseVoiceForgeReturn {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isAvailable, setIsAvailable] = useState(false);
  const [transcript, setTranscript] = useState("");

  // ------------------------------------------------------------------
  // Availability check on mount
  // ------------------------------------------------------------------

  useEffect(() => {
    try {
      setIsAvailable(VoiceForgeService.isAvailable());
    } catch {
      setIsAvailable(false);
    }
  }, []);

  // ------------------------------------------------------------------
  // speak
  // ------------------------------------------------------------------

  const speak = useCallback(async (text: string, opts?: SpeakOptions) => {
    try {
      setIsSpeaking(true);
      VoiceForgeService.speak(text, opts);

      // SpeechSynthesis is fire-and-forget via the native API, so we
      // listen for the end event to flip the flag back. If synthesis is
      // unavailable we simply reset immediately.
      if (typeof window !== "undefined" && window.speechSynthesis) {
        await new Promise<void>((resolve) => {
          const check = () => {
            if (!window.speechSynthesis.speaking) {
              resolve();
              return;
            }
            requestAnimationFrame(check);
          };
          // Give the browser a tick to start speaking before polling.
          setTimeout(check, 50);
        });
      }
    } catch {
      // Never throw — voice is non-critical.
    } finally {
      setIsSpeaking(false);
    }
  }, []);

  // ------------------------------------------------------------------
  // listen
  // ------------------------------------------------------------------

  const listen = useCallback(async (opts?: ListenOptions) => {
    try {
      setIsListening(true);
      const result = await VoiceForgeService.listen(opts);
      setTranscript(result);
      return result;
    } catch {
      return "";
    } finally {
      setIsListening(false);
    }
  }, []);

  // ------------------------------------------------------------------
  // stop
  // ------------------------------------------------------------------

  const stop = useCallback(() => {
    try {
      VoiceForgeService.stop();
    } catch {
      // Ignore.
    }
    setIsListening(false);
    setIsSpeaking(false);
  }, []);

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  return {
    speak,
    listen,
    stop,
    isListening,
    isSpeaking,
    isAvailable,
    transcript,
  };
}
