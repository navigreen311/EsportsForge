'use client';
import { useState } from 'react';
import { Search, ChevronDown, ChevronRight, HelpCircle } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */

const AGENT_DETAILS: Record<string, { short: string; long: string }> = {
  ImpactRank: {
    short: 'Ranks your weaknesses by actual win-rate damage',
    long: 'ImpactRank analyzes every game you play and identifies the mistakes that cost you the most wins. Instead of a generic tier list, it prioritizes what to fix first based on your personal data so your practice time has the highest possible return.',
  },
  PlayerTwin: {
    short: 'Your digital model — learns your real tendencies',
    long: 'PlayerTwin builds a living statistical model of how you play. It captures your habits, reaction patterns, and decision tendencies across thousands of micro-situations so every other agent can reason about *you* specifically.',
  },
  LoopAI: {
    short: 'Learns from every game — self-improving AI',
    long: 'LoopAI is the continuous-learning engine. After every match it re-evaluates what worked and what did not, updating all recommendations. The more you play, the smarter every suggestion becomes.',
  },
  ScoutBot: {
    short: 'Analyzes opponent tendencies from match history',
    long: 'ScoutBot pulls publicly available match data for any opponent and surfaces their habits, comfort picks, and patterns. Use it before a tournament set to know what to expect.',
  },
  GameplanAI: {
    short: 'Generates personalized gameplans vs. specific opponents',
    long: 'GameplanAI combines your PlayerTwin profile with ScoutBot intel to produce a step-by-step plan for beating a specific opponent. It covers bans, picks, early-game approach, and win conditions.',
  },
  DrillBot: {
    short: 'Creates targeted drills for your exact weaknesses',
    long: 'DrillBot takes the top priorities from ImpactRank and generates custom practice routines. Each drill is time-boxed and measurable so you can track improvement session over session.',
  },
  TiltGuard: {
    short: 'Monitors mental performance and intervenes on tilt',
    long: 'TiltGuard watches for signs of tilt — increased error rates, faster input cadence, repeated mistakes — and can pause your queue, suggest a break, or adjust your gameplan to a safer style.',
  },
  ConfidenceAI: {
    short: 'Scores every recommendation with certainty and risk',
    long: 'Every suggestion from the system carries a ConfidenceAI score. High-confidence advice is backed by strong data; low-confidence picks are flagged so you can decide whether the risk is worth it.',
  },
  ForgeCore: {
    short: 'Master orchestrator — one decisive answer from all agents',
    long: 'ForgeCore is the brain that ties all agents together. When multiple agents have competing suggestions, ForgeCore resolves conflicts and presents a single, actionable recommendation.',
  },
  TransferAI: {
    short: 'Measures if practice skills transfer to live play',
    long: 'TransferAI compares your drill performance to your ranked results. If a skill improves in practice but not in competition, it flags the gap and suggests targeted exposure drills.',
  },
  MetaBot: {
    short: 'Tracks what is broken in the current meta',
    long: 'MetaBot monitors patch notes, win-rate shifts, and community data to keep your strategy aligned with the live meta. It alerts you when a change directly affects your champion pool or play style.',
  },
  FilmAI: {
    short: 'Analyzes replays automatically via VisionAudioForge',
    long: 'FilmAI processes your game recordings with computer vision and audio analysis. It timestamps key moments — deaths, objective fights, cooldown misplays — and annotates them for quick review.',
  },
};

interface Article {
  title: string;
  body: string;
}

interface Section {
  id: string;
  title: string;
  articles: Article[];
}

const sections: Section[] = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    articles: [
      {
        title: 'What is EsportsForge?',
        body: 'EsportsForge is an AI-powered competitive gaming platform that uses a swarm of specialized agents to analyze your gameplay, build personalized gameplans, and accelerate your improvement. Connect your game account, play a few matches, and the system starts learning about you immediately.',
      },
      {
        title: 'Your first gameplan',
        body: 'Head to the Gameplan page, select an opponent (or let ScoutBot suggest one from your recent matches), and click "Generate Gameplan." GameplanAI will combine your PlayerTwin data with opponent scouting to deliver a tailored strategy in seconds.',
      },
      {
        title: 'Understanding ImpactRank',
        body: 'ImpactRank assigns every weakness a score based on how much win-rate it actually costs you. A bad habit that loses you 3% win-rate ranks higher than one that loses 0.5%. Focus on the top items first for the fastest climb.',
      },
      {
        title: 'How PlayerTwin learns',
        body: 'PlayerTwin updates after every match. It tracks micro-decisions — trade timing, ability usage, positioning — and builds a statistical fingerprint. The more games it processes, the more accurate its predictions become.',
      },
      {
        title: 'Setting up VoiceForge',
        body: 'Go to Settings > Voice and enable VoiceForge. Grant microphone access when prompted. You can choose a wake word or use push-to-talk. VoiceForge lets you ask questions, request gameplans, and control the dashboard hands-free.',
      },
    ],
  },
  {
    id: 'ai-agents',
    title: 'AI Agents',
    articles: Object.entries(AGENT_DETAILS).map(([name, { short, long }]) => ({
      title: `${name} — ${short}`,
      body: long,
    })),
  },
  {
    id: 'features',
    title: 'Features',
    articles: [
      {
        title: 'Drill Lab',
        body: 'Drill Lab is your personal training ground. DrillBot populates it with exercises tailored to your ImpactRank priorities. Each drill tracks completion, accuracy, and improvement over time.',
      },
      {
        title: 'Film Room',
        body: 'Film Room stores your analyzed replays. FilmAI auto-tags key moments so you can jump straight to fights, deaths, or objective contests without scrubbing through the entire VOD.',
      },
      {
        title: 'TournaOps',
        body: 'TournaOps manages your tournament preparation workflow. Set a tournament date, add opponents, and EsportsForge generates a prep schedule with scouting reports and gameplans for each round.',
      },
      {
        title: 'SimLab',
        body: 'SimLab lets you run "what if" scenarios. Change a variable — different champion, different build, different opponent — and see how the model predicts the outcome based on your PlayerTwin data.',
      },
      {
        title: 'ForgeVault',
        body: 'ForgeVault is your secure storage for gameplans, drill results, and scouting reports. Everything is encrypted and organized by date, opponent, and title for easy retrieval.',
      },
    ],
  },
  {
    id: 'troubleshooting',
    title: 'Troubleshooting',
    articles: [
      {
        title: 'VoiceForge not working',
        body: 'Make sure your browser has microphone permissions enabled for EsportsForge. Check Settings > Voice to confirm VoiceForge is toggled on. If you are on Firefox, try switching to Chrome or Edge, which have better Web Speech API support.',
      },
      {
        title: 'Title not switching',
        body: 'If the platform is stuck on the wrong game title, go to Settings > Game and manually select your title. If the dropdown is empty, ensure your game account is linked under Settings > Integrations.',
      },
      {
        title: 'Gameplan not generating',
        body: 'Gameplan generation requires at least 5 analyzed matches for your PlayerTwin. If you recently linked your account, wait for the initial import to finish (check the progress bar on the Dashboard). Also verify the opponent has public match history available.',
      },
    ],
  },
  {
    id: 'billing',
    title: 'Billing',
    articles: [
      {
        title: 'How tiers work',
        body: 'EsportsForge offers Free, Pro, and Elite tiers. Free gives you basic ImpactRank and limited gameplans. Pro unlocks all agents, unlimited gameplans, and Drill Lab. Elite adds priority processing, SimLab, TournaOps, and dedicated support.',
      },
      {
        title: 'How to upgrade or cancel',
        body: 'Go to Settings > Subscription to manage your plan. Upgrades take effect immediately and are pro-rated. Cancellations take effect at the end of your current billing cycle — you keep access until then.',
      },
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  Accordion                                                          */
/* ------------------------------------------------------------------ */

function AccordionItem({ article }: { article: Article }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-dark-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left text-sm font-medium text-dark-100 hover:bg-dark-700/50 transition-colors"
        aria-expanded={open}
      >
        <span>{article.title}</span>
        {open ? <ChevronDown className="w-4 h-4 text-dark-400 shrink-0" /> : <ChevronRight className="w-4 h-4 text-dark-400 shrink-0" />}
      </button>
      {open && (
        <div className="px-4 pb-4 text-sm text-dark-300 leading-relaxed">
          {article.body}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function HelpPage() {
  const [query, setQuery] = useState('');
  const q = query.toLowerCase().trim();

  const filtered = sections
    .map((section) => ({
      ...section,
      articles: section.articles.filter(
        (a) =>
          !q ||
          a.title.toLowerCase().includes(q) ||
          a.body.toLowerCase().includes(q),
      ),
    }))
    .filter((s) => s.articles.length > 0);

  return (
    <div className="max-w-3xl mx-auto px-4 py-10 space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <HelpCircle className="w-8 h-8 text-forge-400" />
        <h1 className="text-2xl font-bold text-dark-50">Help Center</h1>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search help articles..."
          className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-dark-800 border border-dark-600 text-sm text-dark-100 placeholder:text-dark-500 focus:outline-none focus:ring-2 focus:ring-forge-500"
          aria-label="Search help articles"
        />
      </div>

      {/* Sections */}
      {filtered.length === 0 && (
        <p className="text-dark-400 text-sm">No articles match your search.</p>
      )}

      {filtered.map((section) => (
        <section key={section.id} className="space-y-3">
          <h2 className="text-lg font-semibold text-dark-100">{section.title}</h2>
          <div className="space-y-2">
            {section.articles.map((article) => (
              <AccordionItem key={article.title} article={article} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
