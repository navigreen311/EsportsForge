/**
 * Upload a Secret Weapon — text / URL / document / video paths.
 */

'use client';

import { useState } from 'react';
import {
  Upload,
  FileText,
  LinkIcon,
  Type,
  Video,
  Loader2,
  Check,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import api from '@/lib/api';
import { useActiveArsenalTitle, useUpdateWeapon } from '@/hooks/useArsenal';
import { TITLE_DISPLAY_NAME } from '@/lib/arsenal/titleMeta';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import { useArsenalVoice, toneSpeed } from '@/lib/arsenal/voiceSettings';
import type { Weapon } from '@/hooks/useArsenal';

type Mode = 'text' | 'url' | 'document' | 'video';

const MODE_OPTIONS: { value: Mode; label: string; icon: typeof Type }[] = [
  { value: 'video', label: 'Video File', icon: Video },
  { value: 'url', label: 'YouTube / URL', icon: LinkIcon },
  { value: 'document', label: 'Document', icon: FileText },
  { value: 'text', label: 'Paste Text', icon: Type },
];

export default function UploadPage() {
  const titleId = useActiveArsenalTitle();
  const voice = useArsenalVoice();
  const [mode, setMode] = useState<Mode>('text');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generated, setGenerated] = useState<Weapon | null>(null);

  const reset = () => {
    setText('');
    setUrl('');
    setFile(null);
    setGenerated(null);
    setError(null);
  };

  const submit = async () => {
    setError(null);
    setLoading(true);
    try {
      let weapon: Weapon;
      if (mode === 'text') {
        const { data } = await api.post<Weapon>('/arsenal/upload/text', {
          content: text,
          title_id: titleId,
        });
        weapon = data;
      } else if (mode === 'url') {
        const { data } = await api.post<Weapon>('/arsenal/upload/url', {
          url,
          title_id: titleId,
        });
        weapon = data;
      } else {
        if (!file) throw new Error('Pick a file first');
        const fd = new FormData();
        fd.append('file', file);
        fd.append('title_id', titleId);
        const path = mode === 'document' ? 'document' : 'video';
        const { data } = await api.post<Weapon>(
          `/arsenal/upload/${path}`,
          fd,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        weapon = data;
      }
      setGenerated(weapon);

      // Spoken confirmation so the player can step away from the keyboard.
      if (voice.enabled && VoiceForgeService.isAvailable()) {
        const setupCount = (weapon.setup_steps ?? []).length;
        const execCount = (weapon.instructions ?? []).length;
        VoiceForgeService.speak(
          `New weapon added to your Arsenal: ${weapon.name}. I have extracted ${setupCount} setup ${setupCount === 1 ? 'step' : 'steps'} and ${execCount} execution ${execCount === 1 ? 'step' : 'steps'}. Tap "read it" or "practice it" to continue.`,
          { interruptCurrent: true, speed: toneSpeed(voice.tone) }
        );
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Upload failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-3 text-3xl font-bold text-dark-50">
          <Upload className="h-8 w-8 text-forge-400" />
          Upload a Secret Weapon
        </h1>
        <p className="mt-1 text-dark-400">
          Found a trick play on YouTube? Got a document? Upload it and ArsenalAI
          converts it into step-by-step instructions you can execute in your next game.
        </p>
        <p className="mt-2 text-xs text-dark-400">
          Analyzing for:{' '}
          <span className="font-semibold text-forge-300">
            {TITLE_DISPLAY_NAME[titleId]}
          </span>
        </p>
      </div>

      {!generated && (
        <>
          {/* Mode selector */}
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
            {MODE_OPTIONS.map((m) => {
              const Icon = m.icon;
              const active = mode === m.value;
              return (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => {
                    setMode(m.value);
                    reset();
                  }}
                  className={clsx(
                    'flex items-center justify-center gap-2 rounded-lg border px-3 py-3 text-sm font-semibold transition-all',
                    active
                      ? 'border-forge-500 bg-forge-500/15 text-forge-300'
                      : 'border-dark-700 bg-dark-800/60 text-dark-300 hover:border-dark-600'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {m.label}
                </button>
              );
            })}
          </div>

          {/* Input by mode */}
          <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-5">
            {mode === 'text' && (
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
                placeholder="Paste a Reddit post, Discord message, forum thread, or any description of a trick play..."
                className="w-full resize-y rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
              />
            )}
            {mode === 'url' && (
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
                className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
              />
            )}
            {(mode === 'document' || mode === 'video') && (
              <div className="rounded-lg border-2 border-dashed border-dark-700 px-4 py-8 text-center">
                <input
                  type="file"
                  accept={
                    mode === 'document'
                      ? '.pdf,.doc,.docx,.txt'
                      : 'video/mp4,video/quicktime,video/x-msvideo,video/x-matroska'
                  }
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="block w-full text-xs text-dark-300"
                />
                <p className="mt-2 text-[11px] text-dark-500">
                  {mode === 'document'
                    ? 'Accepted: PDF, DOC, DOCX, TXT — max 10 MB'
                    : 'Accepted: MP4, MOV, AVI, MKV — max 500 MB'}
                </p>
              </div>
            )}

            <button
              type="button"
              onClick={submit}
              disabled={
                loading ||
                (mode === 'text' && !text.trim()) ||
                (mode === 'url' && !url.trim()) ||
                ((mode === 'document' || mode === 'video') && !file)
              }
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950 transition-colors hover:bg-forge-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing…
                </>
              ) : (
                'Analyze'
              )}
            </button>
          </div>

          {loading && <ProcessingStages />}
        </>
      )}

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {generated && (
        <GeneratedWeaponEditor weapon={generated} onDiscard={reset} onSaved={reset} />
      )}
    </div>
  );
}

function ProcessingStages() {
  // Cosmetic — stages tick on a timer while the request is in flight.
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-4">
      <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-dark-400">
        ArsenalAI is analyzing your content…
      </p>
      <ul className="space-y-1 text-xs text-dark-300">
        <li className="flex items-center gap-2">
          <Check className="h-3.5 w-3.5 text-forge-400" /> Content received
        </li>
        <li className="flex items-center gap-2">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-amber-400" />
          Identifying play type…
        </li>
        <li className="flex items-center gap-2 text-dark-500">
          <span className="h-3.5 w-3.5 rounded-full border border-dark-600" />
          Extracting execution steps
        </li>
        <li className="flex items-center gap-2 text-dark-500">
          <span className="h-3.5 w-3.5 rounded-full border border-dark-600" />
          Building trigger conditions
        </li>
      </ul>
    </div>
  );
}

function GeneratedWeaponEditor({
  weapon,
  onDiscard,
  onSaved,
}: {
  weapon: Weapon;
  onDiscard: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(weapon.name);
  const [description, setDescription] = useState(weapon.description);
  const [whenToUse, setWhenToUse] = useState(weapon.when_to_use);
  const [instructions, setInstructions] = useState(
    (weapon.instructions ?? []).join('\n')
  );
  const [setupSteps, setSetupSteps] = useState(
    (weapon.setup_steps ?? []).join('\n')
  );
  const update = useUpdateWeapon();

  const save = async () => {
    await update.mutateAsync({
      id: weapon.id,
      patch: {
        name,
        description,
        when_to_use: whenToUse,
        instructions: instructions.split('\n').filter(Boolean),
        setup_steps: setupSteps.split('\n').filter(Boolean),
      },
    });
    // Auto-save into user's arsenal so it shows up under My Arsenal.
    try {
      await api.post(`/arsenal/my-arsenal/${weapon.id}`);
    } catch {
      // already saved or other — non-fatal
    }
    onSaved();
  };

  return (
    <div className="space-y-3 rounded-xl border border-forge-500/30 bg-emerald-950/20 p-5">
      <p className="text-[11px] font-bold uppercase tracking-wider text-forge-300">
        Generated Weapon — review & edit before saving
      </p>
      <Field label="Name" value={name} onChange={setName} />
      <Field
        label="Description"
        value={description}
        onChange={setDescription}
        textarea
      />
      <Field
        label="When to use"
        value={whenToUse}
        onChange={setWhenToUse}
        textarea
      />
      <Field
        label="Setup steps (one per line)"
        value={setupSteps}
        onChange={setSetupSteps}
        textarea
      />
      <Field
        label="Execution steps (one per line)"
        value={instructions}
        onChange={setInstructions}
        textarea
      />
      <div className="flex items-center justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onDiscard}
          className="rounded-md px-3 py-1.5 text-xs font-medium text-dark-400 hover:bg-dark-800"
        >
          <X className="mr-1 inline h-3 w-3" /> Discard
        </button>
        <button
          type="button"
          onClick={save}
          className="rounded-md bg-forge-500 px-3 py-1.5 text-xs font-bold text-dark-950 hover:bg-forge-400"
        >
          Save to My Arsenal
        </button>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  textarea,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  textarea?: boolean;
}) {
  const Element: React.ElementType = textarea ? 'textarea' : 'input';
  return (
    <div>
      <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-dark-500">
        {label}
      </p>
      <Element
        value={value}
        onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
          onChange(e.target.value)
        }
        rows={textarea ? 3 : undefined}
        className="w-full rounded-md border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 focus:border-forge-500 focus:outline-none"
      />
    </div>
  );
}
