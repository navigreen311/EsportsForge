'use client';

import { FileText, BookOpen, FileJson, Copy, Check } from 'lucide-react';
import { useState, useCallback } from 'react';

interface ExportControlsProps {
  gameplanName: string;
}

export default function ExportControls({ gameplanName }: ExportControlsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, []);

  const buttons = [
    { label: 'Call Sheet', icon: FileText, onClick: () => {} },
    { label: 'eBook', icon: BookOpen, onClick: () => {} },
    { label: 'JSON', icon: FileJson, onClick: () => {} },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2">
      {buttons.map((btn) => {
        const Icon = btn.icon;
        return (
          <button
            key={btn.label}
            onClick={btn.onClick}
            className="inline-flex items-center gap-2 rounded-lg border border-dark-700 bg-dark-800/80 px-3 py-2 text-sm font-medium text-dark-200 transition-colors hover:border-dark-500 hover:bg-dark-700 hover:text-dark-50"
          >
            <Icon className="h-4 w-4" />
            {btn.label}
          </button>
        );
      })}

      <button
        onClick={handleCopy}
        className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
          copied
            ? 'border-forge-500/30 bg-forge-500/10 text-forge-400'
            : 'border-dark-700 bg-dark-800/80 text-dark-200 hover:border-dark-500 hover:bg-dark-700 hover:text-dark-50'
        }`}
      >
        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        {copied ? 'Copied!' : 'Copy to Clipboard'}
      </button>
    </div>
  );
}
