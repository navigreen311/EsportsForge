'use client';
import { useEffect, useState, useCallback } from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';

type Theme = 'dark' | 'light' | 'system';

const STORAGE_KEY = 'esportsforge_theme';

const options: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'system', label: 'System', icon: Monitor },
];

function applyThemeToDOM(theme: Theme) {
  const root = document.documentElement;
  if (theme === 'dark') {
    root.classList.add('dark');
    root.classList.remove('light');
  } else if (theme === 'light') {
    root.classList.add('light');
    root.classList.remove('dark');
  } else {
    // system
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
  }
}

export default function ThemeSelector() {
  const [theme, setTheme] = useState<Theme>('dark');

  // On mount: read persisted theme and apply it
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    const initial: Theme = stored && ['dark', 'light', 'system'].includes(stored) ? stored : 'dark';
    setTheme(initial);
    applyThemeToDOM(initial);
  }, []);

  // Listen for system preference changes when theme is 'system'
  useEffect(() => {
    if (theme !== 'system') return;

    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => applyThemeToDOM('system');
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  const handleChange = useCallback((t: Theme) => {
    setTheme(t);
    applyThemeToDOM(t);
    localStorage.setItem(STORAGE_KEY, t);

    // Fire-and-forget preference sync
    fetch('/api/user/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme: t }),
    }).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium text-dark-200">Appearance</h3>
        <p className="text-xs text-dark-400 mt-1">Theme</p>
      </div>
      <div className="flex gap-3">
        {options.map(({ value, label, icon: Icon }) => {
          const selected = theme === value;
          return (
            <button
              key={value}
              onClick={() => handleChange(value)}
              aria-pressed={selected}
              className={`flex items-center gap-2 rounded-lg p-4 border text-sm font-medium cursor-pointer transition-all ${
                selected
                  ? 'border-forge-400 shadow-[0_0_10px_rgba(74,222,128,0.15)] text-forge-400'
                  : 'bg-dark-800 border-dark-600 text-dark-300 hover:border-dark-400'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
