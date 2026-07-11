/**
 * Voice command bar for the Arsenal page. Recognises a small set of
 * intents and dispatches them — falls back to no-op if VoiceForge is
 * unavailable. Hidden entirely when the underlying SpeechRecognition
 * API isn't present.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Mic, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import {
  useMyArsenal,
  useActiveArsenalTitle,
} from '@/hooks/useArsenal';
import { useArsenalVoice } from '@/lib/arsenal/voiceSettings';
import { TITLE_DISPLAY_NAME } from '@/lib/arsenal/titleMeta';
import api from '@/lib/api';
import { useSessionStore } from '@/lib/sessionStore';
import { useGameStateStore } from '@/lib/arsenal/gameStateStore';

interface Props {
  /** Open the weapon-detail slide-over for the matched weapon. */
  onOpenWeapon: (id: string) => void;
  /** Optional — open the panel directly into Guided Practice. */
  onPracticeWeapon?: (id: string) => void;
}

const PILLS: { label: string; command: string }[] = [
  { label: '"Read my weapons"', command: 'read my weapons' },
  { label: '"Find a trick play"', command: 'find a trick play' },
  { label: '"What should I use right now"', command: 'what should i use right now' },
];

export function VoiceCommandBar({ onOpenWeapon, onPracticeWeapon }: Props) {
  const [available, setAvailable] = useState(false);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const titleId = useActiveArsenalTitle();
  const { data: weapons = [] } = useMyArsenal();
  const voice = useArsenalVoice();
  const router = useRouter();
  const session = useSessionStore((s) => s.session);
  const gameState = useGameStateStore((s) => s.states[titleId] ?? {});

  useEffect(() => {
    setAvailable(VoiceForgeService.isAvailable());
  }, []);

  if (!available || !voice.enabled) return null;

  const speak = (text: string) =>
    VoiceForgeService.speak(text, {
      interruptCurrent: true,
      tone: voice.tone,
    });

  const findWeapon = (phrase: string) => {
    const norm = phrase.toLowerCase();
    return (
      weapons.find((w) => norm.includes(w.name.toLowerCase())) ||
      weapons.find((w) =>
        w.name
          .toLowerCase()
          .split(/[\s—-]+/)
          .some((tok) => tok.length > 3 && norm.includes(tok))
      )
    );
  };

  const dispatch = async (raw: string) => {
    const t = raw.toLowerCase().trim();
    if (!t) return;

    if (t.includes('read my weapons') || t.includes('what weapons do i have')) {
      if (weapons.length === 0) {
        speak('You have no weapons saved yet for this title. Try discover or upload.');
        setFeedback('No weapons saved yet.');
        return;
      }
      const top = weapons[0]!;
      speak(
        `You have ${weapons.length} ${weapons.length === 1 ? 'weapon' : 'weapons'} in your Arsenal for ${TITLE_DISPLAY_NAME[titleId]}. Your top weapon: ${top.name}. Best used when ${top.when_to_use}. Say the name of a weapon to hear its full brief.`
      );
      setFeedback(`Read summary of ${weapons.length} weapons.`);
      return;
    }

    if (t.includes('find a trick play') || t.includes('discover')) {
      router.push('/arsenal/discover');
      setFeedback('Opening Discover…');
      return;
    }

    if (t.startsWith('practice ')) {
      const w = findWeapon(t.replace('practice', ''));
      if (w) {
        setFeedback(`Practice: ${w.name}`);
        if (onPracticeWeapon) onPracticeWeapon(w.id);
        else onOpenWeapon(w.id);
      } else {
        speak('I could not find that weapon in your Arsenal.');
      }
      return;
    }

    if (t.startsWith('read ') || t.startsWith('how do i execute')) {
      const w = findWeapon(t);
      if (w) {
        setFeedback(`Open: ${w.name}`);
        onOpenWeapon(w.id);
      } else {
        speak('I could not find that weapon by name.');
      }
      return;
    }

    if (
      t.includes('what should i use') ||
      t.includes('any weapons right now') ||
      t.includes('weapon moment')
    ) {
      try {
        const { data } = await api.post('/arsenal/trigger', {
          title_id: titleId,
          game_state: gameState,
          session_id: session?.startTime?.toString(),
        });
        if (data?.trigger && data.weapon) {
          speak(
            `${data.weapon.name}. ${data.reason ?? ''} ${data.timing ?? ''}`.trim()
          );
          setFeedback(`Trigger: ${data.weapon.name}`);
        } else {
          speak(
            'No clear weapon deployment window right now. I will alert you when one shows up.'
          );
          setFeedback('No deployment window right now.');
        }
      } catch {
        setFeedback('Could not reach ArsenalAI right now.');
      }
      return;
    }

    setFeedback(`Heard: "${raw}" — no matching command.`);
  };

  const startListening = async () => {
    setListening(true);
    setTranscript(null);
    setFeedback(null);
    try {
      const heard = await VoiceForgeService.listen({ timeout: 5000 });
      setTranscript(heard);
      if (heard) await dispatch(heard);
    } finally {
      setListening(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dark-700/50 bg-dark-900/60 px-3 py-2">
      <button
        type="button"
        onClick={startListening}
        disabled={listening}
        className={clsx(
          'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-bold transition-colors',
          listening
            ? 'border border-forge-500 bg-forge-500/15 text-forge-300'
            : 'border border-dark-700 bg-dark-800 text-dark-200 hover:bg-dark-700'
        )}
      >
        {listening ? (
          <>
            <Loader2 className="h-3 w-3 animate-spin" />
            Listening…
          </>
        ) : (
          <>
            <Mic className="h-3 w-3" />
            Voice
          </>
        )}
      </button>
      {PILLS.map((p) => (
        <button
          key={p.command}
          type="button"
          onClick={() => {
            setTranscript(p.command);
            void dispatch(p.command);
          }}
          className="rounded-full border border-dark-700 bg-dark-800/60 px-2 py-0.5 text-[10px] text-dark-400 transition-colors hover:border-forge-500/40 hover:text-forge-300"
        >
          {p.label}
        </button>
      ))}
      {transcript && (
        <span className="text-[10px] text-dark-500">
          You said: <span className="text-dark-300">{transcript}</span>
        </span>
      )}
      {feedback && <span className="text-[10px] text-forge-300">{feedback}</span>}
    </div>
  );
}
