/**
 * Wraps `ActiveDrillMode` in a Document Picture-in-Picture window when the
 * browser supports it. Falls back to inline rendering on Firefox / Safari /
 * older Chromium so the experience never disappears for unsupported users.
 *
 * When the floating window is active, the in-page slot shows a small
 * placeholder so the player can tell where the controls went.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ExternalLink, Eye, Maximize2, X } from 'lucide-react';
import type { DrillRecord } from '@/types/analytics';
import ActiveDrillMode, {
  type ActiveDrillResult,
} from '@/components/drills/ActiveDrillMode';
import {
  isPiPSupported,
  openPiPWindow,
  type PiPHandle,
} from '@/lib/drills/pictureInPicture';

type Monitor = NonNullable<
  Parameters<typeof ActiveDrillMode>[0]['monitor']
>;

interface ActiveDrillPiPHostProps {
  drill: DrillRecord;
  titleId: string;
  monitor?: Monitor;
  onComplete: (result: ActiveDrillResult) => void;
  onAbort: () => void;
}

export default function ActiveDrillPiPHost(props: ActiveDrillPiPHostProps) {
  const supported = isPiPSupported();
  const [pipBody, setPipBody] = useState<HTMLElement | null>(null);
  const [pipFailed, setPipFailed] = useState(false);
  const handleRef = useRef<PiPHandle | null>(null);
  const completedRef = useRef(false);
  const abortRef = useRef(props.onAbort);

  // Keep abort callback fresh without re-running the effect.
  useEffect(() => {
    abortRef.current = props.onAbort;
  }, [props.onAbort]);

  useEffect(() => {
    if (!supported) {
      setPipFailed(true);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      const handle = await openPiPWindow({
        width: 420,
        height: 560,
        onClose: () => {
          // If the user closed the PiP window before the drill finished,
          // treat it as an abort. If the drill already completed, do nothing.
          if (!completedRef.current) {
            abortRef.current();
          }
        },
      });
      if (cancelled) {
        handle?.close();
        return;
      }
      if (!handle) {
        setPipFailed(true);
        return;
      }
      handleRef.current = handle;
      // Build a wrapper inside the PiP body that gives ActiveDrillMode some
      // padding without forcing the inline component to know it's portalled.
      const wrapper = handle.window.document.createElement('div');
      wrapper.style.padding = '12px';
      wrapper.style.minHeight = '100vh';
      handle.window.document.body.appendChild(wrapper);
      setPipBody(wrapper);
    })();

    return () => {
      cancelled = true;
      handleRef.current?.close();
      handleRef.current = null;
    };
  }, [supported]);

  const handleComplete = (result: ActiveDrillResult) => {
    completedRef.current = true;
    handleRef.current?.close();
    handleRef.current = null;
    props.onComplete(result);
  };

  const handleAbort = () => {
    completedRef.current = true; // skip the close-handler abort
    handleRef.current?.close();
    handleRef.current = null;
    props.onAbort();
  };

  // PiP unsupported / failed → render inline as before.
  if (!supported || pipFailed) {
    return (
      <ActiveDrillMode
        drill={props.drill}
        titleId={props.titleId}
        monitor={props.monitor}
        onComplete={props.onComplete}
        onAbort={props.onAbort}
      />
    );
  }

  // PiP requested but window not open yet — show a brief placeholder.
  if (!pipBody) {
    return (
      <div className="rounded-xl border border-forge-500/30 bg-dark-900/60 p-6 text-sm text-dark-300">
        Opening floating drill window…
      </div>
    );
  }

  // PiP open — render placeholder in the page, ActiveDrillMode in the PiP.
  return (
    <>
      <div className="flex items-center justify-between rounded-xl border border-forge-500/30 bg-dark-900/60 p-4">
        <div className="flex items-center gap-3">
          <Maximize2 className="h-5 w-5 text-forge-400" />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-forge-400">
              Drill running in floating window
            </p>
            <p className="mt-0.5 text-sm font-bold text-dark-50">{props.drill.name}</p>
            <p className="mt-0.5 inline-flex items-center gap-1 text-[11px] text-dark-400">
              <Eye className="h-3 w-3" /> Always-on-top — visible over your game
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleAbort}
          className="inline-flex items-center gap-1.5 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-semibold text-red-300 hover:bg-red-500/20"
        >
          <X className="h-3.5 w-3.5" /> Close floating window
        </button>
      </div>

      {createPortal(
        <ActiveDrillMode
          drill={props.drill}
          titleId={props.titleId}
          monitor={props.monitor}
          onComplete={handleComplete}
          onAbort={handleAbort}
        />,
        pipBody,
      )}

      <p className="text-[11px] text-dark-500">
        <ExternalLink className="mr-1 inline h-3 w-3" />
        Drag the floating window over your game. Closing it ends the drill early.
      </p>
    </>
  );
}
