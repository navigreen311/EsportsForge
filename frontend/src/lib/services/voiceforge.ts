/**
 * VoiceForge service wrapper.
 *
 * Uses the Web Speech API as a fallback until the dedicated VoiceForge
 * microservice is available. When the service is ready, swap the internal
 * implementation to hit the REST API while keeping the same public interface.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SpeakOptions {
  /** Priority level — reserved for future queue-based implementation. */
  priority?: "low" | "normal" | "high";
  /** If true, cancel any in-progress utterance before speaking. */
  interruptCurrent?: boolean;
  /** Playback speed (0.5 – 2.0). Defaults to 1. */
  speed?: number;
}

export interface ListenOptions {
  /** Max milliseconds to wait for speech before resolving. */
  timeout?: number;
  /** Optional prompt text shown to the user (UI layer responsibility). */
  prompt?: string;
  /** Keep the recogniser open for multiple phrases. */
  continuous?: boolean;
}

export interface ToneResult {
  mood: string;
  confidence: number;
}

// ---------------------------------------------------------------------------
// Internals
// ---------------------------------------------------------------------------

const VOICEFORGE_ENABLED =
  typeof process !== "undefined" &&
  process.env.NEXT_PUBLIC_VOICEFORGE_ENABLED === "true";

const API_BASE =
  typeof process !== "undefined"
    ? process.env.NEXT_PUBLIC_VOICEFORGE_API_URL ?? "http://localhost:9000"
    : "http://localhost:9000";

/**
 * Safely access SpeechSynthesis — returns undefined when running on the
 * server or in browsers that lack the API.
 */
function getSynthesis(): SpeechSynthesis | undefined {
  try {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      return window.speechSynthesis;
    }
  } catch {
    // SSR or restricted environment — ignore.
  }
  return undefined;
}

/**
 * Safely access the SpeechRecognition constructor.
 */
function getRecognitionCtor(): (new () => SpeechRecognition) | undefined {
  try {
    if (typeof window !== "undefined") {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const W = window as any;
      return W.SpeechRecognition ?? W.webkitSpeechRecognition ?? undefined;
    }
  } catch {
    // SSR or restricted environment — ignore.
  }
  return undefined;
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

export const VoiceForgeService = {
  // -----------------------------------------------------------------------
  // speak
  // -----------------------------------------------------------------------

  /**
   * Speak the given text using the Web Speech API.
   *
   * When the VoiceForge REST service is live the implementation will POST to
   * `${API_BASE}/v1/tts` and stream the resulting audio instead.
   */
  speak(text: string, opts: SpeakOptions = {}): void {
    if (!VOICEFORGE_ENABLED) return;

    try {
      const synth = getSynthesis();
      if (!synth) return;

      if (opts.interruptCurrent) {
        synth.cancel();
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = Math.min(2, Math.max(0.5, opts.speed ?? 1));

      synth.speak(utterance);
    } catch {
      // Graceful degradation — voice is non-critical.
    }
  },

  // -----------------------------------------------------------------------
  // listen
  // -----------------------------------------------------------------------

  /**
   * Start speech recognition and resolve with the captured transcript.
   *
   * When the VoiceForge REST service is live, this will stream audio to
   * `${API_BASE}/v1/stt` via a WebSocket instead.
   */
  listen(opts: ListenOptions = {}): Promise<string> {
    if (!VOICEFORGE_ENABLED) return Promise.resolve("");

    const Ctor = getRecognitionCtor();
    if (!Ctor) return Promise.resolve("");

    return new Promise<string>((resolve) => {
      try {
        const recognition = new Ctor();
        recognition.continuous = opts.continuous ?? false;
        recognition.interimResults = false;
        recognition.lang = "en-US";

        let settled = false;
        let transcript = "";

        const finish = () => {
          if (settled) return;
          settled = true;
          resolve(transcript);
        };

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
              transcript += event.results[i][0].transcript;
            }
          }
        };

        recognition.onerror = () => finish();
        recognition.onend = () => finish();

        recognition.start();

        if (opts.timeout && opts.timeout > 0) {
          setTimeout(() => {
            try {
              recognition.stop();
            } catch {
              // Already stopped — ignore.
            }
          }, opts.timeout);
        }
      } catch {
        resolve("");
      }
    });
  },

  // -----------------------------------------------------------------------
  // stop
  // -----------------------------------------------------------------------

  /** Cancel any in-progress speech output. */
  stop(): void {
    try {
      const synth = getSynthesis();
      synth?.cancel();
    } catch {
      // Ignore.
    }
  },

  // -----------------------------------------------------------------------
  // isAvailable
  // -----------------------------------------------------------------------

  /** Returns true when both SpeechSynthesis and SpeechRecognition are present. */
  isAvailable(): boolean {
    if (!VOICEFORGE_ENABLED) return false;

    try {
      return !!getSynthesis() && !!getRecognitionCtor();
    } catch {
      return false;
    }
  },

  // -----------------------------------------------------------------------
  // detectTone
  // -----------------------------------------------------------------------

  /**
   * Analyse tone / mood from audio data.
   *
   * Currently returns a mock result. When the VoiceForge REST service is
   * available this will POST audio to `${API_BASE}/v1/tone`.
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  detectTone(_audioData?: ArrayBuffer): ToneResult {
    return { mood: "neutral", confidence: 72 };
  },

  // -----------------------------------------------------------------------
  // REST helpers (prepared for the real service)
  // -----------------------------------------------------------------------

  /** @internal Base URL for the VoiceForge REST API. */
  _apiBase: API_BASE,
} as const;
