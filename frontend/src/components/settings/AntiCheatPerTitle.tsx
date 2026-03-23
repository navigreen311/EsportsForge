'use client';

import { useState } from 'react';
import { Shield, Check, ChevronDown } from 'lucide-react';

interface TitleStatus {
  title: string;
  status: string;
  verified: boolean;
}

const titleStatuses: TitleStatus[] = [
  { title: 'Madden 26', status: 'N/A', verified: false },
  { title: 'CFB 26', status: 'N/A', verified: false },
  { title: 'NBA 2K26', status: 'N/A', verified: false },
  { title: 'EA FC 26', status: 'N/A', verified: false },
  { title: 'Warzone', status: 'Ricochet — Verified Safe', verified: true },
  { title: 'Fortnite', status: 'Easy Anti-Cheat — Verified Safe', verified: true },
  { title: 'Valorant', status: 'Vanguard — Verified Safe', verified: true },
  { title: 'Street Fighter 6', status: 'N/A', verified: false },
  { title: 'Tekken 8', status: 'N/A', verified: false },
];

const faqItems = [
  {
    question: 'Does EsportsForge inject into game memory?',
    answer:
      'No. EsportsForge operates entirely outside game processes. We never inject code, modify game files, or interact with game memory in any way.',
  },
  {
    question: 'Will I get banned for using EsportsForge?',
    answer:
      'No. Our platform has been verified safe by all major anti-cheat providers. EsportsForge uses only publicly available post-game data and approved APIs.',
  },
  {
    question: 'What data does EsportsForge read during gameplay?',
    answer:
      'EsportsForge reads only post-game statistics and replay data. We do not access real-time game state, memory, or network packets during active gameplay.',
  },
];

export default function AntiCheatPerTitle() {
  const [faqOpen, setFaqOpen] = useState(false);

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Title */}
      <div className="flex items-center gap-2 mb-4">
        <Shield className="h-5 w-5 text-forge-400" />
        <h3 className="text-sm font-bold text-dark-200">Anti-Cheat Compliance</h3>
      </div>

      {/* Status Grid */}
      <div className="space-y-2">
        {titleStatuses.map((item) => (
          <div
            key={item.title}
            className="flex items-center justify-between rounded-lg border border-dark-700 bg-dark-800/50 px-4 py-2.5"
          >
            <span className="text-sm text-dark-200">{item.title}</span>
            <div className="flex items-center gap-1.5">
              {item.verified ? (
                <>
                  <span className="text-sm text-forge-400">{item.status} ✓</span>
                  <Check className="h-4 w-4 text-forge-400" />
                </>
              ) : (
                <span className="text-sm text-dark-500">{item.status}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Info Text */}
      <p className="text-xs text-dark-400 mt-3 p-3 rounded-lg bg-dark-800/50 border border-dark-700">
        EsportsForge screen capture and overlay features are disabled for Warzone and Fortnite in
        all non-Offline Lab environments to ensure full compliance with anti-cheat systems.
      </p>

      {/* FAQ Section */}
      <div className="mt-4">
        <button
          onClick={() => setFaqOpen(!faqOpen)}
          className="flex w-full items-center justify-between rounded-lg border border-dark-700 bg-dark-800/50 px-4 py-2.5 text-sm font-medium text-dark-200 transition-colors hover:bg-dark-800"
        >
          Anti-Cheat FAQ
          <ChevronDown
            className={`h-4 w-4 text-dark-400 transition-transform ${
              faqOpen ? 'rotate-180' : ''
            }`}
          />
        </button>

        {faqOpen && (
          <div className="mt-2 space-y-4 rounded-lg border border-dark-700 bg-dark-800/50 p-4">
            {faqItems.map((item, index) => (
              <div key={index}>
                <p className="font-medium text-dark-200">{item.question}</p>
                <p className="text-dark-400 text-sm mt-1">{item.answer}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
