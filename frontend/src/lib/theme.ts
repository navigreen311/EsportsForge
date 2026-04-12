'use client';

export type Theme = 'dark' | 'light' | 'system';

export function getStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'dark';
  return (localStorage.getItem('esportsforge-theme') as Theme) || 'dark';
}

export function applyTheme(theme: Theme) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('esportsforge-theme', theme);
  const root = document.documentElement;
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.classList.toggle('dark', prefersDark);
  } else {
    root.classList.toggle('dark', theme === 'dark');
  }
}
