'use client';
import { useEffect, useRef } from 'react';

type ShortcutHandler = () => void;

export function useKeyboardShortcuts(shortcuts: Record<string, ShortcutHandler>) {
  const pendingKey = useRef<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      // Skip if typing in input/textarea
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return;

      const key = e.key.toLowerCase();

      // Cmd/Ctrl+K for search
      if ((e.metaKey || e.ctrlKey) && key === 'k') {
        e.preventDefault();
        shortcuts['cmd+k']?.();
        return;
      }

      // ? for help
      if (key === '?' && !e.metaKey && !e.ctrlKey) {
        shortcuts['?']?.();
        return;
      }

      // Escape
      if (key === 'escape') {
        shortcuts['escape']?.();
        return;
      }

      // Two-key sequences: G then X
      if (pendingKey.current === 'g') {
        pendingKey.current = null;
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        const combo = `g+${key}`;
        shortcuts[combo]?.();
        return;
      }

      if (key === 'g') {
        pendingKey.current = 'g';
        timeoutRef.current = setTimeout(() => { pendingKey.current = null; }, 500);
        return;
      }

      // Single key shortcuts
      if (key === 'n') shortcuts['n']?.();
    }

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [shortcuts]);
}
