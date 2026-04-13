'use client';

import { useState } from 'react';
import {
  Check,
  X,
  CreditCard,
  Download,
  ExternalLink,
  AlertTriangle,
} from 'lucide-react';
import type { UserTier } from '@/types/auth';

interface SubscriptionManagementProps {
  currentTier: UserTier;
}

/* ------------------------------------------------------------------ */
/*  SECTION 1 — Current Plan data                                     */
/* ------------------------------------------------------------------ */

interface PlanFeature {
  label: string;
  included: boolean;
}

const competitivePlanFeatures: PlanFeature[] = [
  { label: 'Madden 26 + CFB 26', included: true },
  { label: 'NBA 2K26, EA FC 26, MLB 26, Warzone, Fortnite', included: true },
  { label: 'Full AI agent suite', included: true },
  { label: 'PlayerTwin + FilmAI + TiltGuard', included: true },
  { label: 'Tournament Ops (Elite only)', included: false },
  { label: 'UFC 5, PGA 2K25, Undisputed (Elite only)', included: false },
];

const tierData: Record<
  UserTier,
  { name: string; price: number; features: PlanFeature[] }
> = {
  free: {
    name: 'Free Tier',
    price: 0,
    features: [
      { label: 'Single game title tracking', included: true },
      { label: 'Basic analytics dashboard', included: true },
      { label: 'Community meta reports', included: true },
      { label: 'AI agent suite (Competitive+)', included: false },
      { label: 'Advanced analytics (Competitive+)', included: false },
    ],
  },
  competitive: {
    name: 'Competitive Tier',
    price: 19.99,
    features: competitivePlanFeatures,
  },
  elite: {
    name: 'Elite Tier',
    price: 49.99,
    features: [
      { label: 'All 11 game titles', included: true },
      { label: 'Full AI agent suite', included: true },
      { label: 'TournaOps tournament hub', included: true },
      { label: 'ForgeVault + VoiceForge', included: true },
      { label: 'Full ImpactRank analytics', included: true },
      { label: 'Coach Portal & War Room (Team only)', included: false },
    ],
  },
  team: {
    name: 'Team Tier',
    price: 149.99,
    features: [
      { label: 'All 11 game titles', included: true },
      { label: 'Full AI agent suite + TournaOps', included: true },
      { label: 'Coach Portal & War Room', included: true },
      { label: 'SquadOps + 6 team seats', included: true },
      { label: 'Dedicated account manager', included: true },
    ],
  },
};

/* ------------------------------------------------------------------ */
/*  SECTION 2 — Upgrade cards                                         */
/* ------------------------------------------------------------------ */

const upgradeCards: {
  tier: UserTier;
  price: string;
  tagline: string;
  cta: string;
  ctaStyle: 'filled' | 'outlined';
}[] = [
  {
    tier: 'elite',
    price: '$49.99/mo',
    tagline:
      'All 11 titles + TournaOps + ForgeVault + VoiceForge + full ImpactRank.',
    cta: 'Upgrade to Elite',
    ctaStyle: 'filled',
  },
  {
    tier: 'team',
    price: '$149.99/mo',
    tagline:
      'Everything Elite + Coach Portal + War Room + SquadOps + 6 seats.',
    cta: 'Upgrade to Team',
    ctaStyle: 'outlined',
  },
];

const tierOrder: UserTier[] = ['free', 'competitive', 'elite', 'team'];

/* ------------------------------------------------------------------ */
/*  SECTION 3 — Invoices                                              */
/* ------------------------------------------------------------------ */

const invoices = [
  { date: 'Apr 15, 2026', amount: '$19.99', status: 'Paid' },
  { date: 'Mar 15, 2026', amount: '$19.99', status: 'Paid' },
  { date: 'Feb 15, 2026', amount: '$19.99', status: 'Paid' },
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function generateInvoiceBlob(invoice: { date: string; amount: string }): string {
  return [
    '========================================',
    '         ESPORTSFORGE INVOICE',
    '========================================',
    '',
    `Date:       ${invoice.date}`,
    `Amount:     ${invoice.amount}`,
    `Status:     Paid`,
    `Plan:       Competitive Tier`,
    '',
    'Payment Method: Visa ending in 4242',
    '',
    '----------------------------------------',
    'EsportsForge Inc.',
    'support@esportsforge.com',
    '========================================',
  ].join('\n');
}

function downloadInvoice(invoice: { date: string; amount: string }) {
  const text = generateInvoiceBlob(invoice);
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `esportsforge-invoice-${invoice.date.replace(/[\s,]+/g, '-').toLowerCase()}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/* ------------------------------------------------------------------ */
/*  Retention / cancel features the user will lose                    */
/* ------------------------------------------------------------------ */

const competitiveLossFeatures = [
  'Full AI agent suite (LoopAI, PlayerTwin, FilmAI, TiltGuard)',
  'Madden 26, CFB 26, NBA 2K26, EA FC 26, MLB 26, Warzone, Fortnite',
  'ImpactRank tracking & advanced analytics',
  'Kill sheet generator & unlimited drills',
];

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */

export default function SubscriptionManagement({
  currentTier,
}: SubscriptionManagementProps) {
  const plan = tierData[currentTier];
  const currentIndex = tierOrder.indexOf(currentTier);

  // Upgrade button state: key = tier, value = loading text or null
  const [upgradingTier, setUpgradingTier] = useState<UserTier | null>(null);

  // Cancel flow state
  const [showRetentionDialog, setShowRetentionDialog] = useState(false);
  const [cancelledUntil, setCancelledUntil] = useState<string | null>(null);
  const [cancellingInProgress, setCancellingInProgress] = useState(false);

  const availableUpgrades = upgradeCards.filter(
    (card) => tierOrder.indexOf(card.tier) > currentIndex
  );

  /* ---- handlers ---- */

  async function handleUpgrade(tier: UserTier) {
    setUpgradingTier(tier);
    try {
      // Mock fetch
      await fetch('/api/v1/subscriptions/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier }),
      }).catch(() => {
        // swallow network error for mock
      });
      // Simulate redirect delay
      await new Promise((r) => setTimeout(r, 2000));
    } finally {
      setUpgradingTier(null);
    }
  }

  async function handleCancelConfirm() {
    setCancellingInProgress(true);
    try {
      await fetch('/api/v1/subscriptions/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }).catch(() => {
        // swallow network error for mock
      });
      await new Promise((r) => setTimeout(r, 1000));
      setCancelledUntil('May 15, 2026');
      setShowRetentionDialog(false);
    } finally {
      setCancellingInProgress(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* ========== SECTION 1: Current Plan ========== */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">Current Plan</h2>

        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-xl font-bold text-dark-50">{plan.name}</span>
          <span className="text-dark-400">&mdash;</span>
          <span className="text-xl font-bold text-forge-400">
            {plan.price === 0 ? 'Free' : `$${plan.price.toFixed(2)}/month`}
          </span>
        </div>

        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-dark-400 mb-5">
          <span>Active since: Jan 15, 2026</span>
          <span>Next billing: May 15, 2026</span>
        </div>

        {/* Feature checklist with check / cross */}
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {plan.features.map((feat) => (
            <li
              key={feat.label}
              className={`flex items-start gap-2 text-sm ${
                feat.included ? 'text-dark-300' : 'text-dark-500'
              }`}
            >
              {feat.included ? (
                <Check className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              ) : (
                <X className="w-4 h-4 text-dark-600 mt-0.5 shrink-0" />
              )}
              {feat.label}
            </li>
          ))}
        </ul>
      </div>

      {/* ========== SECTION 2: Available Upgrades ========== */}
      {currentTier !== 'team' && availableUpgrades.length > 0 && (
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
          <h2 className="text-lg font-bold text-dark-100 mb-4">
            Available Upgrades
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableUpgrades.map((card) => {
              const isUpgrading = upgradingTier === card.tier;
              return (
                <div
                  key={card.tier}
                  className="rounded-xl border border-dark-600 bg-dark-800/60 p-5"
                >
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-lg font-bold text-dark-50 capitalize">
                      {card.tier}
                    </span>
                    <span className="text-sm font-semibold text-forge-400">
                      {card.price}
                    </span>
                  </div>

                  <p className="text-sm text-dark-400 mb-5">{card.tagline}</p>

                  {card.ctaStyle === 'filled' ? (
                    <button
                      disabled={isUpgrading}
                      onClick={() => handleUpgrade(card.tier)}
                      className="w-full rounded-lg bg-forge-600 py-2.5 text-sm font-medium text-white hover:bg-forge-500 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isUpgrading ? (
                        'Redirecting to checkout...'
                      ) : (
                        <>
                          {card.cta} <span aria-hidden="true">&rarr;</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <button
                      disabled={isUpgrading}
                      onClick={() => handleUpgrade(card.tier)}
                      className="w-full rounded-lg border border-forge-600 bg-transparent py-2.5 text-sm font-medium text-forge-400 hover:bg-forge-600/10 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isUpgrading ? (
                        'Redirecting to checkout...'
                      ) : (
                        <>
                          {card.cta} <span aria-hidden="true">&rarr;</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ========== SECTION 3: Billing ========== */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">Billing</h2>

        {/* Payment Method */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <CreditCard className="w-5 h-5 text-dark-400" />
            <span className="text-sm text-dark-300">
              &bull;&bull;&bull;&bull; 4242 (Visa)
            </span>
          </div>
          <button className="rounded-lg border border-dark-600 bg-dark-800 px-4 py-2 text-sm font-medium text-dark-200 hover:bg-dark-700 transition-colors">
            Update
          </button>
        </div>

        {/* Invoice History */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-dark-300 mb-3">
            Invoice History
          </h3>
          <div className="space-y-2">
            {invoices.map((invoice) => (
              <div
                key={invoice.date}
                className="flex items-center justify-between rounded-lg border border-dark-700 bg-dark-800/40 px-4 py-3"
              >
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-dark-300">{invoice.date}</span>
                  <span className="font-medium text-dark-200">
                    {invoice.amount}
                  </span>
                  <span className="inline-flex items-center gap-1 text-green-500">
                    {invoice.status} <Check className="w-3.5 h-3.5" />
                  </span>
                </div>
                <button
                  onClick={() => downloadInvoice(invoice)}
                  className="flex items-center gap-1.5 text-sm text-forge-400 hover:text-forge-300 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Manage Billing link */}
        <div className="mb-6">
          <button className="flex items-center gap-1.5 text-sm font-medium text-forge-400 hover:text-forge-300 transition-colors">
            Manage Billing <ExternalLink className="w-4 h-4" />
          </button>
        </div>

        {/* Cancel Subscription */}
        {currentTier !== 'free' && (
          <div>
            {cancelledUntil ? (
              <p className="text-sm text-dark-400">
                Subscription cancelled. Active until{' '}
                <span className="text-dark-200 font-medium">{cancelledUntil}</span>.
              </p>
            ) : (
              <button
                onClick={() => setShowRetentionDialog(true)}
                className="text-sm font-medium text-red-400 hover:text-red-300 transition-colors"
              >
                Cancel Subscription
              </button>
            )}
          </div>
        )}
      </div>

      {/* ========== Retention / Cancel Dialog ========== */}
      {showRetentionDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-md rounded-xl border border-dark-600 bg-dark-800 p-6 shadow-2xl mx-4">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-yellow-500 shrink-0" />
              <h3 className="text-lg font-bold text-dark-100">
                Before you go&hellip;
              </h3>
            </div>

            <p className="text-sm text-dark-400 mb-4">
              You&rsquo;ll lose access to these features:
            </p>

            <ul className="space-y-2 mb-6">
              {competitiveLossFeatures.map((feat) => (
                <li
                  key={feat}
                  className="flex items-start gap-2 text-sm text-dark-300"
                >
                  <X className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                  {feat}
                </li>
              ))}
            </ul>

            <div className="flex gap-3">
              <button
                onClick={() => setShowRetentionDialog(false)}
                className="flex-1 rounded-lg bg-forge-600 py-2.5 text-sm font-medium text-white hover:bg-forge-500 transition-colors"
              >
                Keep Plan
              </button>
              <button
                disabled={cancellingInProgress}
                onClick={handleCancelConfirm}
                className="flex-1 rounded-lg border border-red-500/50 bg-transparent py-2.5 text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {cancellingInProgress ? 'Cancelling...' : 'Cancel Anyway'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
