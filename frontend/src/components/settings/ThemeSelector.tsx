'use client';
import { useEffect, useState } from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';
import { type Theme, getStoredTheme, applyTheme } from '@/lib/theme';

const options: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'system', label: 'System', icon: Monitor },
];

export default function ThemeSelector() {
  const [theme, setTheme] = useState<Theme>('dark');

  useEffect(() => {
    setTheme(getStoredTheme());
  }, []);

  const handleChange = (t: Theme) => {
    setTheme(t);
    applyTheme(t);
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-dark-200">Appearance</h3>
      <div className="flex gap-2">
        {options.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            onClick={() => handleChange(value)}
            aria-pressed={theme === value}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
              theme === value
                ? 'bg-forge-500/20 border-forge-500 text-forge-400'
                : 'bg-dark-800 border-dark-600 text-dark-300 hover:border-dark-400'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
