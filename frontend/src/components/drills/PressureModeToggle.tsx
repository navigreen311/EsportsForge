'use client';

interface PressureModeToggleProps {
  enabled: boolean;
  onToggle: () => void;
}

export default function PressureModeToggle({
  enabled,
  onToggle,
}: PressureModeToggleProps) {
  return (
    <div
      className="flex items-center gap-3"
      title="Simulates tournament pressure — recommended before competitive events"
    >
      <span className="text-sm font-medium text-dark-200">Pressure Mode</span>

      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        onClick={onToggle}
        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
          enabled ? 'bg-amber-500' : 'bg-dark-700'
        }`}
      >
        <span
          className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
            enabled ? 'translate-x-[18px]' : 'translate-x-[3px]'
          }`}
        />
      </button>

      {enabled && (
        <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/20 border border-amber-500/30 rounded px-1.5 py-0.5">
          Pressure Active
        </span>
      )}
    </div>
  );
}

interface PressureContextProps {
  enabled: boolean;
}

export function PressureContext({ enabled }: PressureContextProps) {
  if (!enabled) return null;

  return (
    <div className="rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-400">
      Pressure Mode: Time windows tightened 25%. Decision speed AND accuracy
      scored.
    </div>
  );
}
