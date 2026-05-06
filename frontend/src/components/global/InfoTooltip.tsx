'use client';

import { useEffect, useState, type ReactNode } from 'react';
import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import { X } from 'lucide-react';

type Side = 'top' | 'bottom' | 'left' | 'right';

interface InfoTooltipProps {
  content: ReactNode;
  side?: Side;
  delay?: number;
  /** Heading shown in the mobile bottom sheet (defaults to "Details") */
  mobileTitle?: string;
  children: ReactNode;
}

/**
 * Hover-tooltip on pointer devices, bottom-sheet on touch devices.
 *
 * Wraps the trigger with a Radix Tooltip on desktop. On a touch-only device
 * (or when the user explicitly taps the ⓘ-shaped child), a slide-up sheet
 * is rendered instead — much more legible on small screens.
 */
export default function InfoTooltip({
  content,
  side = 'top',
  delay = 200,
  mobileTitle = 'Details',
  children,
}: InfoTooltipProps) {
  const [isTouch, setIsTouch] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(hover: none), (pointer: coarse)');
    setIsTouch(mq.matches);
    const handler = (e: MediaQueryListEvent) => setIsTouch(e.matches);
    mq.addEventListener?.('change', handler);
    return () => mq.removeEventListener?.('change', handler);
  }, []);

  // Mobile bottom-sheet UX polish: Escape closes, body scroll locks while open
  useEffect(() => {
    if (!sheetOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSheetOpen(false);
    };
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [sheetOpen]);

  if (isTouch) {
    return (
      <>
        <span
          onClickCapture={(e) => {
            // Prevent card-selection click from firing when the user taps to read.
            // The card will still receive the click on a *second* tap because
            // sheetOpen is now true and we re-enable propagation below.
            if (!sheetOpen) {
              e.stopPropagation();
              e.preventDefault();
              setSheetOpen(true);
            }
          }}
          className="contents"
        >
          {children}
        </span>
        {sheetOpen && (
          <div
            className="fixed inset-0 z-[9999] flex items-end bg-black/60"
            onClick={() => setSheetOpen(false)}
            role="dialog"
            aria-modal="true"
          >
            <div
              className="w-full rounded-t-2xl border-t border-dark-700 bg-dark-900 p-5 pb-7 shadow-2xl animate-in slide-in-from-bottom"
              onClick={(e) => e.stopPropagation()}
              style={{ animation: 'tooltip-slide-up 200ms ease-out' }}
            >
              <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-dark-600" />
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-sm font-semibold text-dark-100">{mobileTitle}</h3>
                <button
                  onClick={() => setSheetOpen(false)}
                  className="text-dark-500 hover:text-dark-200"
                  aria-label="Close"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="text-sm leading-relaxed text-dark-300">{content}</div>
              <button
                onClick={() => setSheetOpen(false)}
                className="mt-5 w-full rounded-lg bg-forge-500/15 border border-forge-500/30 px-4 py-2 text-sm font-semibold text-forge-300 hover:bg-forge-500/25"
              >
                Got it
              </button>
            </div>
            <style>{`
              @keyframes tooltip-slide-up {
                from { transform: translateY(100%); }
                to   { transform: translateY(0); }
              }
            `}</style>
          </div>
        )}
      </>
    );
  }

  return (
    <TooltipPrimitive.Provider delayDuration={delay} skipDelayDuration={0}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={side}
            sideOffset={8}
            collisionPadding={12}
            className="z-[9999] max-w-[320px] rounded-md border border-dark-700/80 bg-dark-800 px-3 py-2.5 text-xs leading-relaxed text-dark-200 shadow-lg shadow-black/40 data-[state=delayed-open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=delayed-open]:fade-in-0 data-[side=top]:slide-in-from-bottom-1 data-[side=bottom]:slide-in-from-top-1"
            style={{ borderWidth: '0.5px' }}
          >
            {content}
            <TooltipPrimitive.Arrow className="fill-dark-800" width={10} height={5} />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}
