'use client';

import { useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { GlobalSearch } from './GlobalSearch';
import { ShortcutsCheatsheet } from './ShortcutsCheatsheet';

export function SearchShortcutsProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [searchOpen, setSearchOpen] = useState(false);
  const [cheatsheetOpen, setCheatsheetOpen] = useState(false);

  const closeAll = useCallback(() => {
    setSearchOpen(false);
    setCheatsheetOpen(false);
  }, []);

  const shortcuts = useMemo(
    () => ({
      'cmd+k': () => setSearchOpen((prev) => !prev),
      '?': () => setCheatsheetOpen((prev) => !prev),
      escape: () => closeAll(),
      n: () => router.push('/gameplan'),

      // G + key navigation
      'g+d': () => router.push('/dashboard'),
      'g+g': () => router.push('/gameplan'),
      'g+o': () => router.push('/opponents'),
      'g+r': () => router.push('/drills'),
      'g+a': () => router.push('/analytics'),
      'g+s': () => router.push('/settings'),
      'g+t': () => router.push('/tournament'),
      'g+v': () => router.push('/vault'),
    }),
    [router, closeAll]
  );

  useKeyboardShortcuts(shortcuts);

  return (
    <>
      {children}
      <GlobalSearch open={searchOpen} onClose={() => setSearchOpen(false)} />
      <ShortcutsCheatsheet open={cheatsheetOpen} onClose={() => setCheatsheetOpen(false)} />
    </>
  );
}
