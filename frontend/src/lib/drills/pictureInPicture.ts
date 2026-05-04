/**
 * Thin wrapper around the Document Picture-in-Picture API.
 *
 * Opens a true OS-floating browser-managed window (always on top, sits over
 * other apps including the game) into which we can portal arbitrary React
 * content. Available in Chromium 116+ — `isPiPSupported()` returns false on
 * Firefox / Safari / older Chromium so callers can fall back to inline.
 *
 * The PiP window is a separate document but shares the opener's origin, so
 * any React context portalled in continues to share state, the same axios
 * client, NextAuth session, etc.
 */

type DocumentPiP = {
  requestWindow(opts?: { width?: number; height?: number }): Promise<Window>;
  window: Window | null;
};

declare global {
  interface Window {
    documentPictureInPicture?: DocumentPiP;
  }
}

export function isPiPSupported(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(window.documentPictureInPicture);
}

/**
 * Mirror the host document's `<link rel="stylesheet">` and `<style>` tags
 * into the PiP window so portalled content keeps its Tailwind classes.
 *
 * Copying nodes (rather than re-inserting the same DOM elements) avoids
 * hot-module-reload reattaching them to the wrong document.
 */
function copyStylesheets(targetDoc: Document): void {
  const head = targetDoc.head;
  if (!head) return;

  document.head.querySelectorAll('link[rel="stylesheet"], style').forEach((node) => {
    const clone = node.cloneNode(true) as HTMLElement;
    head.appendChild(clone);
  });

  // Match the host body's classes so dark backgrounds carry over.
  if (document.body.className) {
    targetDoc.body.className = document.body.className;
  }
  targetDoc.body.style.margin = '0';
  targetDoc.body.style.background = 'rgb(10, 10, 10)';
}

export interface PiPHandle {
  window: Window;
  /** Resolves once the PiP window has been closed (for any reason). */
  closed: Promise<void>;
  /** Programmatically close the PiP window. */
  close: () => void;
}

export async function openPiPWindow(opts: {
  width?: number;
  height?: number;
  /** Called once when the user (or code) closes the PiP window. */
  onClose?: () => void;
}): Promise<PiPHandle | null> {
  if (!isPiPSupported()) return null;

  let pipWin: Window;
  try {
    pipWin = await window.documentPictureInPicture!.requestWindow({
      width: opts.width ?? 380,
      height: opts.height ?? 520,
    });
  } catch (err) {
    console.warn('[PiP] requestWindow rejected:', err);
    return null;
  }

  copyStylesheets(pipWin.document);

  let resolveClosed: () => void;
  const closed = new Promise<void>((resolve) => {
    resolveClosed = resolve;
  });
  const handleClose = () => {
    opts.onClose?.();
    resolveClosed();
  };
  pipWin.addEventListener('pagehide', handleClose, { once: true });

  return {
    window: pipWin,
    closed,
    close: () => {
      try {
        pipWin.close();
      } catch {
        // Already closed — pagehide handler will fire anyway.
      }
    },
  };
}
