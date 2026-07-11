/**
 * Pre-Execution Brief — opens from ArsenalAlert's "View Setup Steps".
 * Shows a stripped-down 30-second setup + execute brief, with a
 * VoiceForge "Read Brief to Me" button. "I'm Ready — Go" logs the
 * deployment and closes.
 */

'use client';

import { useState } from 'react';
import { Volume2, StopCircle, X, Zap } from 'lucide-react';
import { useWeapon } from '@/hooks/useArsenal';
import { Modal } from '@/components/shared/Modal';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import { useArsenalVoice } from '@/lib/arsenal/voiceSettings';
import { buildPreExecBrief, titleFamily } from '@/lib/arsenal/voiceScripts';
import { useSessionStore } from '@/lib/sessionStore';
import api from '@/lib/api';

interface Props {
  open: boolean;
  weaponId: string | null;
  urgency?: 'now' | 'soon' | 'watch';
  onClose: () => void;
  /** Called when the player taps "I'm Ready — Go". */
  onDeploy?: () => void;
}

export function PreExecutionBrief({
  open,
  weaponId,
  urgency,
  onClose,
  onDeploy,
}: Props) {
  const { data: weapon } = useWeapon(weaponId);
  const voice = useArsenalVoice();
  const session = useSessionStore((s) => s.session);
  const [reading, setReading] = useState(false);

  if (!open || !weapon) {
    return (
      <Modal open={open} onClose={onClose} title="Pre-Execution Brief" size="md">
        <p className="py-4 text-sm text-dark-400">Loading…</p>
      </Modal>
    );
  }

  const family = titleFamily(weapon.title_id);
  const setupTrim = weapon.setup_steps?.slice(0, family === 'basketball' ? 0 : 2) ?? [];
  const execTrim =
    weapon.instructions?.slice(
      0,
      family === 'fighting' ? 2 : family === 'fps' ? 3 : family === 'poker' ? 1 : 3
    ) ?? [];

  const stop = () => {
    VoiceForgeService.stop();
    setReading(false);
  };

  const read = async () => {
    if (!voice.enabled || !voice.preExecBrief) return;
    if (!VoiceForgeService.isAvailable()) return;
    setReading(true);
    const text = buildPreExecBrief(weapon, urgency);
    await VoiceForgeService.speakAsync(text, {
      tone: voice.tone,
      interruptCurrent: true,
    });
    setReading(false);
  };

  const deploy = async () => {
    VoiceForgeService.stop();
    if (weapon) {
      try {
        await api.post('/arsenal/usage-log', {
          weapon_id: weapon.id,
          title_id: weapon.title_id,
          deployed: true,
          session_id: session?.startTime?.toString(),
        });
      } catch {
        /* non-fatal */
      }
    }
    onDeploy?.();
    onClose();
  };

  return (
    <Modal open={open} onClose={onClose} size="md">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-forge-400" />
            <p className="text-[10px] font-bold uppercase tracking-wider text-forge-300">
              Pre-Execution Brief
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-dark-400 hover:bg-dark-800 hover:text-dark-100"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <h3 className="text-lg font-bold text-dark-50">{weapon.name}</h3>

        {setupTrim.length > 0 && (
          <div>
            <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-dark-400">
              Setup
            </p>
            <ol className="space-y-1 text-sm text-dark-200">
              {setupTrim.map((s, i) => (
                <li key={i} className="flex gap-2">
                  <span className="font-bold text-forge-400">{i + 1}.</span>
                  <span>{s}</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {execTrim.length > 0 && (
          <div>
            <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-dark-400">
              Execute
            </p>
            <ol className="space-y-1 text-sm text-dark-100">
              {execTrim.map((s, i) => (
                <li key={i} className="flex gap-2">
                  <span className="font-bold text-forge-400">{i + 1}.</span>
                  <span>{s}</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-dark-700/50 pt-3">
          {voice.enabled && voice.preExecBrief && VoiceForgeService.isAvailable() ? (
            reading ? (
              <button
                type="button"
                onClick={stop}
                className="inline-flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs font-bold text-red-300 hover:bg-red-500/20"
              >
                <StopCircle className="h-4 w-4" />
                Stop
              </button>
            ) : (
              <button
                type="button"
                onClick={read}
                className="inline-flex items-center gap-1 rounded-md border border-forge-500/40 bg-forge-500/10 px-3 py-2 text-xs font-bold text-forge-300 hover:bg-forge-500/20"
              >
                <Volume2 className="h-4 w-4" />
                Read Brief to Me
              </button>
            )
          ) : (
            <span />
          )}
          <button
            type="button"
            onClick={deploy}
            className="inline-flex items-center gap-1 rounded-md bg-forge-500 px-4 py-2 text-xs font-bold text-dark-950 hover:bg-forge-400"
          >
            I&apos;m Ready — Go
          </button>
        </div>
      </div>
    </Modal>
  );
}
